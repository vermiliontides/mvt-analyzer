#!/usr/bin/env python3
"""
automated_forensics.py

LLM-assisted triage over MVT check-backup output, plus differential
tamper-detection across two backup snapshots.

Checkpointing is per-CHUNK (not per-file) in SQLite, so:
  - Resuming after an interruption only re-does chunks that never completed
    successfully (status 'pending' or 'failed') — chunks already marked
    'safe' or 'flagged' are never re-analyzed.
  - A file is only considered complete when every one of its chunks reached
    a terminal, non-failed state. A run where every chunk failed (e.g.
    Ollama was down) leaves the file incomplete and eligible for resume,
    instead of being silently marked done.
  - Failures are bounded-retried per chunk, not infinitely re-attempted and
    not silently swallowed into the results.
"""

import json
import logging
import os
import sqlite3
import sys
import time
from contextlib import closing
from datetime import datetime, UTC

import requests

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"  # cheap connectivity check
MODEL_NAME = "llama3:8b-instruct-q4_K_M"

DIR_MAY28 = "./results/iPhone_16_Pro_Max_20260528_44GB"
DIR_JUNE01 = "./results/iPhone_16_Pro_Max_20260601_26GB"
FINAL_REPORT_PATH = "comprehensive_forensic_report.md"
CHECKPOINT_DB_PATH = "forensic_checkpoint.sqlite3"
LOG_PATH = "automated_forensics.log"

MAX_ATTEMPTS_PER_CHUNK = 3
RETRY_BACKOFF_SECONDS = 5

SYSTEM_PROMPT = (
    "You are an expert iOS digital forensics analyst. Analyze this small chunk of MVT JSON logs.\n"
    "You will be provided with the JSON context/schema keys to help you interpret the values accurately.\n"
    "Look ONLY for indicators of compromise, unrecognized background daemons, or suspicious network traffic.\n\n"
    "CRITICAL FORMATTING RULES:\n"
    "1. If you find anomalies, output them ONLY as markdown table rows using this exact format:\n"
    "   | Timestamp | Process / Domain / Artifact | Risk Level | Brief Technical Justification |\n"
    "2. Do NOT include markdown table headers (no '| --- |') or introduction text. Just provide the raw rows.\n"
    "3. If everything in this chunk looks completely normal and safe, reply ONLY with the word: SAFE."
)

# ----------------------------------------------------------------------------
# LOGGING
# ----------------------------------------------------------------------------


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("forensics")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    file_handler = logging.FileHandler(LOG_PATH)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


log = setup_logging()

# ----------------------------------------------------------------------------
# CHECKPOINT STORE (SQLite, per-chunk)
# ----------------------------------------------------------------------------


def init_checkpoint_db(db_path: str = CHECKPOINT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunk_status (
            file_name     TEXT NOT NULL,
            chunk_index   INTEGER NOT NULL,
            total_chunks  INTEGER NOT NULL,
            status        TEXT NOT NULL CHECK(status IN ('pending','safe','flagged','failed')),
            result_rows   TEXT,
            error_message TEXT,
            attempts      INTEGER NOT NULL DEFAULT 0,
            updated_at    TEXT NOT NULL,
            PRIMARY KEY (file_name, chunk_index)
        )
        """
    )
    conn.commit()
    return conn


def ensure_chunks_registered(conn: sqlite3.Connection, file_name: str, total_chunks: int) -> None:
    """Idempotently registers every chunk index for a file as 'pending' if not already tracked.
    Never overwrites an existing row — this is what preserves already-successful chunks across runs."""
    now = datetime.now(UTC).isoformat()
    for idx in range(total_chunks):
        conn.execute(
            """
            INSERT INTO chunk_status (file_name, chunk_index, total_chunks, status, attempts, updated_at)
            VALUES (?, ?, ?, 'pending', 0, ?)
            ON CONFLICT(file_name, chunk_index) DO NOTHING
            """,
            (file_name, idx, total_chunks, now),
        )
    conn.commit()


def get_outstanding_chunks(conn: sqlite3.Connection, file_name: str) -> list[int]:
    """Chunks that still need work: never attempted, or failed and under the retry cap."""
    cur = conn.execute(
        """
        SELECT chunk_index FROM chunk_status
        WHERE file_name = ?
          AND status IN ('pending', 'failed')
          AND attempts < ?
        ORDER BY chunk_index
        """,
        (file_name, MAX_ATTEMPTS_PER_CHUNK),
    )
    return [row[0] for row in cur.fetchall()]


def record_chunk_result(
    conn: sqlite3.Connection,
    file_name: str,
    chunk_index: int,
    status: str,
    result_rows: list[str] | None = None,
    error_message: str | None = None,
) -> None:
    now = datetime.now(UTC).isoformat()
    conn.execute(
        """
        UPDATE chunk_status
        SET status = ?, result_rows = ?, error_message = ?, attempts = attempts + 1, updated_at = ?
        WHERE file_name = ? AND chunk_index = ?
        """,
        (status, json.dumps(result_rows) if result_rows else None, error_message, now, file_name, chunk_index),
    )
    conn.commit()


def file_completion_summary(conn: sqlite3.Connection, file_name: str) -> dict:
    cur = conn.execute(
        """
        SELECT status, COUNT(*) FROM chunk_status WHERE file_name = ? GROUP BY status
        """,
        (file_name,),
    )
    counts = {status: count for status, count in cur.fetchall()}
    total = sum(counts.values())
    terminal = counts.get("safe", 0) + counts.get("flagged", 0)
    exhausted_failures = 0
    cur = conn.execute(
        "SELECT COUNT(*) FROM chunk_status WHERE file_name = ? AND status = 'failed' AND attempts >= ?",
        (file_name, MAX_ATTEMPTS_PER_CHUNK),
    )
    exhausted_failures = cur.fetchone()[0]
    return {
        "total": total,
        "safe": counts.get("safe", 0),
        "flagged": counts.get("flagged", 0),
        "failed": counts.get("failed", 0),
        "pending": counts.get("pending", 0),
        "complete": terminal == total,
        "exhausted_failures": exhausted_failures,
    }


def collect_flagged_rows(conn: sqlite3.Connection, file_name: str) -> list[str]:
    cur = conn.execute(
        """
        SELECT result_rows FROM chunk_status
        WHERE file_name = ? AND status = 'flagged' AND result_rows IS NOT NULL
        ORDER BY chunk_index
        """,
        (file_name,),
    )
    rows: list[str] = []
    for (result_json,) in cur.fetchall():
        rows.extend(json.loads(result_json))
    return rows


# ----------------------------------------------------------------------------
# CHUNKING / SCHEMA HELPERS
# ----------------------------------------------------------------------------


def get_chunk_size(filename: str) -> int:
    if "datausage" in filename or "interaction_c" in filename:
        return 60  # Dropped slightly to guarantee stability over long runs
    if "safari" in filename or "sms" in filename:
        return 90
    return 130


def extract_schema_keys(file_path: str) -> list[str]:
    """Safely extracts the top-level keys of the JSON file to provide context to the LLM."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return list(data[0].keys())
            elif isinstance(data, dict):
                return list(data.keys())
    except Exception:
        pass
    return ["Unknown Schema"]


def chunk_log_file(file_path: str, chunk_size: int) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            lines = json.dumps(data, indent=2).split("\n")
        except json.JSONDecodeError:
            f.seek(0)
            lines = f.readlines()

    return ["\n".join(lines[i : i + chunk_size]) for i in range(0, len(lines), chunk_size)]


# ----------------------------------------------------------------------------
# JUNK ROW FILTERING (fixes header/separator leakage into results)
# ----------------------------------------------------------------------------


def is_junk_row(row: str) -> bool:
    """Detects markdown table headers and separator rows the model produced
    despite being told not to, so they never make it into stored results."""
    lowered = row.lower()
    if "timestamp" in lowered and "risk level" in lowered:
        return True  # header row
    stripped = row.replace("|", "").replace("-", "").replace(" ", "").replace(":", "")
    if stripped == "":
        return True  # separator row, e.g. "| :--- | :--- |"
    return False


# ----------------------------------------------------------------------------
# OLLAMA
# ----------------------------------------------------------------------------


def check_ollama_reachable() -> tuple[bool, str]:
    try:
        resp = requests.get(OLLAMA_TAGS_URL, timeout=5)
        if resp.ok:
            return True, ""
        return False, f"Ollama responded with status {resp.status_code}"
    except Exception as e:
        return False, str(e)


def query_local_llm(log_chunk: str, schema_keys: list[str]) -> tuple[bool, list[str], str | None]:
    """Returns (ok, clean_rows, error_message). ok=True and empty rows means
    the model reported SAFE for this chunk — that's a real, storable result,
    distinct from a failed request."""
    context_prompt = f"DATABASE SCHEMA FIELDS FOR REFERENCE: {schema_keys}\n\n{SYSTEM_PROMPT}\n\nLOG DATA CHUNK:\n{log_chunk}"
    payload = {"model": MODEL_NAME, "prompt": context_prompt, "stream": False}
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json().get("response", "").strip()
    except Exception as e:
        return False, [], str(e)

    if not result:
        return False, [], "empty response from model"

    if result.strip().upper() == "SAFE":
        return True, [], None

    clean_rows = [row.strip() for row in result.split("\n") if row.strip().startswith("|")]
    clean_rows = [row for row in clean_rows if not is_junk_row(row)]
    return True, clean_rows, None


# ----------------------------------------------------------------------------
# DIFFERENTIAL ANALYSIS (unchanged in spirit, not chunked, cheap to redo)
# ----------------------------------------------------------------------------


def run_differential_analysis() -> list[str]:
    if not os.path.exists(DIR_MAY28) or not os.path.exists(DIR_JUNE01):
        return ["| N/A | Baseline Error | HIGH | Results directory mapping missing. |"]

    tampering_alerts = []
    may_files = {f for f in os.listdir(DIR_MAY28) if f.endswith(".json")}
    june_files = {f for f in os.listdir(DIR_JUNE01) if f.endswith(".json")}

    for f in may_files - june_files:
        tampering_alerts.append(
            f"| N/A | `{f}` | CRITICAL | File present on May 28, but completely MISSING on June 01. "
            f"Potential targeted database wiping event. |"
        )

    for f in may_files & june_files:
        path_may = os.path.join(DIR_MAY28, f)
        path_june = os.path.join(DIR_JUNE01, f)
        size_may = os.path.getsize(path_may)
        size_june = os.path.getsize(path_june)
        if size_june < (size_may * 0.5) and size_may > 1024:
            tampering_alerts.append(
                f"| N/A | `{f}` | HIGH | File size dropped violently from {size_may} bytes to "
                f"{size_june} bytes. Possible log clearing. |"
            )

    return tampering_alerts


# ----------------------------------------------------------------------------
# REPORT
# ----------------------------------------------------------------------------


def write_final_report(
    conn: sqlite3.Connection,
    differential_alerts: list[str],
    all_files: list[str],
) -> None:
    with open(FINAL_REPORT_PATH, "w", encoding="utf-8") as repo:
        repo.write("# Comprehensive iOS Forensic Anomaly Report\n")
        repo.write("**Target Device:** iPhone 16 Pro Max  \n")
        repo.write(f"**Primary Baseline:** `{DIR_MAY28}`  \n")
        repo.write(f"**Comparative Target:** `{DIR_JUNE01}`  \n\n")

        # --- Honesty section: what's actually complete vs. outstanding ---
        repo.write("## Analysis Completeness\n\n")
        repo.write("| Source File | Total Chunks | Safe | Flagged | Failed | Pending | Status |\n")
        repo.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        any_incomplete = False
        for fname in all_files:
            s = file_completion_summary(conn, fname)
            status = "complete" if s["complete"] else "INCOMPLETE — re-run to finish"
            if not s["complete"]:
                any_incomplete = True
            repo.write(
                f"| `{fname}` | {s['total']} | {s['safe']} | {s['flagged']} | {s['failed']} | "
                f"{s['pending']} | {status} |\n"
            )
        repo.write("\n")
        if any_incomplete:
            repo.write(
                "> ⚠️ One or more files have chunks that failed or never ran. Findings below reflect only "
                "the chunks that completed successfully — **this report is not yet a complete picture**. "
                "Re-run the script to retry outstanding chunks; already-completed chunks will not be "
                "re-analyzed.\n\n"
            )

        repo.write("## ⚠️ Anti-Forensic Differential Alerts\n")
        if differential_alerts:
            repo.write("| Timestamp | Target File | Risk Level | Anomaly Description |\n")
            repo.write("| :--- | :--- | :--- | :--- |\n")
            for alert in differential_alerts:
                repo.write(f"{alert}\n")
        else:
            repo.write("> No database wiping detected between the two dates.\n")

        repo.write("\n## 🤖 AI-Flagged Behavioral Telemetry\n")
        any_rows = False
        repo.write("| Source File | Timestamp | Process / Domain / Artifact | Risk Level | Brief Technical Justification |\n")
        repo.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for fname in all_files:
            rows = collect_flagged_rows(conn, fname)
            for row in rows:
                repo.write(f"| `{fname}` {row}\n")
                any_rows = True
        if not any_rows:
            repo.write("| _none_ | | | | No indicators of compromise isolated across completed chunks. |\n")


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------


def main() -> None:
    conn = init_checkpoint_db()

    log.info("Phase 1: gathering anti-forensic differential statistics")
    differential_alerts = run_differential_analysis()
    if differential_alerts:
        log.warning(f"{len(differential_alerts)} differential alert(s) found")

    reachable, reason = check_ollama_reachable()
    if not reachable:
        log.error(
            f"Ollama is not reachable at {OLLAMA_TAGS_URL} ({reason}). "
            f"Aborting before processing any chunks — nothing will be checkpointed as failed "
            f"just because Ollama is down. Start Ollama and re-run; already-completed chunks "
            f"from prior runs are unaffected."
        )
        sys.exit(1)
    log.info("Ollama connectivity check passed")

    if not os.path.exists(DIR_MAY28):
        log.error(f"Baseline directory not found: {DIR_MAY28}")
        sys.exit(1)

    all_json_files = sorted([f for f in os.listdir(DIR_MAY28) if f.endswith(".json")])
    log.info(f"Phase 2: {len(all_json_files)} file(s) to analyze")

    for filename in all_json_files:
        file_path = os.path.join(DIR_MAY28, filename)
        chunk_size = get_chunk_size(filename)
        schema_keys = extract_schema_keys(file_path)
        chunks = chunk_log_file(file_path, chunk_size)

        ensure_chunks_registered(conn, filename, len(chunks))
        outstanding = get_outstanding_chunks(conn, filename)

        summary = file_completion_summary(conn, filename)
        if not outstanding:
            if summary["complete"]:
                log.info(f"{filename}: already complete ({summary['total']} chunks) — skipping")
            else:
                log.warning(
                    f"{filename}: {summary['exhausted_failures']} chunk(s) exhausted retries "
                    f"({MAX_ATTEMPTS_PER_CHUNK} attempts) and remain failed — not retrying further "
                    f"automatically. See {LOG_PATH} for error details."
                )
            continue

        log.info(
            f"{filename}: {len(outstanding)} chunk(s) outstanding of {len(chunks)} total "
            f"(safe={summary['safe']} flagged={summary['flagged']} failed={summary['failed']})"
        )

        for chunk_index in outstanding:
            chunk = chunks[chunk_index]
            ok, rows, error = query_local_llm(chunk, schema_keys)

            if not ok:
                record_chunk_result(conn, filename, chunk_index, "failed", error_message=error)
                log.warning(f"{filename} chunk {chunk_index + 1}/{len(chunks)}: FAILED — {error}")
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue

            if rows:
                record_chunk_result(conn, filename, chunk_index, "flagged", result_rows=rows)
                log.info(f"{filename} chunk {chunk_index + 1}/{len(chunks)}: FLAGGED ({len(rows)} row(s))")
            else:
                record_chunk_result(conn, filename, chunk_index, "safe")
                log.debug(f"{filename} chunk {chunk_index + 1}/{len(chunks)}: safe")

        # Report is rewritten after every file so progress is never lost,
        # and it always reflects true per-chunk completeness, not a guess.
        write_final_report(conn, differential_alerts, all_json_files)

    log.info("Phase 3: finalizing report")
    write_final_report(conn, differential_alerts, all_json_files)

    # --- Run summary ---
    log.info("=" * 60)
    log.info("Run summary:")
    incomplete_files = []
    for fname in all_json_files:
        s = file_completion_summary(conn, fname)
        if not s["complete"]:
            incomplete_files.append((fname, s))
    if incomplete_files:
        log.warning(f"{len(incomplete_files)} file(s) incomplete — re-run this script to continue:")
        for fname, s in incomplete_files:
            log.warning(
                f"  {fname}: {s['pending']} pending, {s['failed']} failed "
                f"({s['exhausted_failures']} exhausted retries)"
            )
    else:
        log.info("All files fully analyzed.")
    log.info(f"Report: {FINAL_REPORT_PATH}")
    log.info(f"Checkpoint DB: {CHECKPOINT_DB_PATH} (safe to inspect with sqlite3 directly)")
    log.info("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
