##!/usr/bin/env python3
"""
automated_forensics.py

LLM-assisted triage over MVT check-backup output, plus differential
tamper-detection across two backup snapshots.

Features:
  - Per-chunk checkpointing in SQLite with schema auto-migration.
  - Full model provenance tracking per chunk.
  - Thread-safe HTTP request pool with single-threaded SQLite writes.
  - Command-line control over model selection, concurrency, and re-modeling.
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, UTC

import requests

# ----------------------------------------------------------------------------
# DEFAULT CONFIGURATION
# ----------------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

# Default tuned for 6GB VRAM GPUs (GTX 1060 / 1660 Ti / RTX 3060 Laptop)
DEFAULT_MODEL_NAME = "llama3:8b-instruct-q4_K_M"
DEFAULT_MAX_CONCURRENT_CHUNKS = 1

DIR_MAY28 = "./results/iPhone_16_Pro_Max_20260528_44GB"
DIR_JUNE01 = "./results/iPhone_16_Pro_Max_20260601_26GB"
FINAL_REPORT_PATH = "comprehensive_forensic_report.md"
CHECKPOINT_DB_PATH = "forensic_checkpoint.sqlite3"
LOG_PATH = "automated_forensics.log"

MAX_ATTEMPTS_PER_CHUNK = 3

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
# CHECKPOINT STORE (SQLite)
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
    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(chunk_status)").fetchall()}
    if "model_name" not in existing_cols:
        conn.execute("ALTER TABLE chunk_status ADD COLUMN model_name TEXT")
        log.info("Migrated checkpoint DB: added 'model_name' column.")
    conn.commit()
    return conn

def ensure_chunks_registered(conn: sqlite3.Connection, file_name: str, total_chunks: int) -> None:
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
    model_name: str,
    result_rows: list[str] | None = None,
    error_message: str | None = None,
) -> None:
    now = datetime.now(UTC).isoformat()
    conn.execute(
        """
        UPDATE chunk_status
        SET status = ?, result_rows = ?, error_message = ?, model_name = ?,
            attempts = attempts + 1, updated_at = ?
        WHERE file_name = ? AND chunk_index = ?
        """,
        (status, json.dumps(result_rows) if result_rows else None, error_message,
         model_name, now, file_name, chunk_index),
    )
    conn.commit()

def stale_model_chunk_counts(conn: sqlite3.Connection, current_model: str) -> list[tuple[str | None, int]]:
    cur = conn.execute(
        """
        SELECT model_name, COUNT(*) FROM chunk_status
        WHERE status IN ('safe', 'flagged') AND (model_name IS NULL OR model_name != ?)
        GROUP BY model_name
        """,
        (current_model,),
    )
    return cur.fetchall()

def reset_stale_model_chunks(conn: sqlite3.Connection, current_model: str) -> int:
    now = datetime.now(UTC).isoformat()
    cur = conn.execute(
        """
        UPDATE chunk_status
        SET status = 'pending', attempts = 0, result_rows = NULL, error_message = NULL, updated_at = ?
        WHERE status IN ('safe', 'flagged') AND (model_name IS NULL OR model_name != ?)
        """,
        (now, current_model),
    )
    conn.commit()
    return cur.rowcount

def models_used_for_file(conn: sqlite3.Connection, file_name: str) -> list[str]:
    cur = conn.execute(
        """
        SELECT DISTINCT model_name FROM chunk_status
        WHERE file_name = ? AND status IN ('safe', 'flagged') AND model_name IS NOT NULL
        ORDER BY model_name
        """,
        (file_name,),
    )
    return [row[0] for row in cur.fetchall()]

def file_completion_summary(conn: sqlite3.Connection, file_name: str) -> dict:
    cur = conn.execute("SELECT status, COUNT(*) FROM chunk_status WHERE file_name = ? GROUP BY status", (file_name,))
    counts = {status: count for status, count in cur.fetchall()}
    total = sum(counts.values())
    terminal = counts.get("safe", 0) + counts.get("flagged", 0)
    
    cur = conn.execute("SELECT COUNT(*) FROM chunk_status WHERE file_name = ? AND status = 'failed' AND attempts >= ?", (file_name, MAX_ATTEMPTS_PER_CHUNK))
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
# CHUNKING & PARSING HELPERS
# ----------------------------------------------------------------------------

def get_chunk_size(filename: str) -> int:
    if "datausage" in filename or "interaction_c" in filename:
        return 60
    if "safari" in filename or "sms" in filename:
        return 90
    return 130

def extract_schema_keys(file_path: str) -> list[str]:
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

def is_junk_row(row: str) -> bool:
    lowered = row.lower()
    if "timestamp" in lowered and "risk level" in lowered:
        return True
    stripped = row.replace("|", "").replace("-", "").replace(" ", "").replace(":", "")
    return stripped == ""

# ----------------------------------------------------------------------------
# OLLAMA API INTERACTION
# ----------------------------------------------------------------------------

def check_ollama_reachable() -> tuple[bool, str]:
    try:
        resp = requests.get(OLLAMA_TAGS_URL, timeout=5)
        if resp.ok:
            return True, ""
        return False, f"Ollama responded with status {resp.status_code}"
    except Exception as e:
        return False, str(e)

def query_local_llm(log_chunk: str, schema_keys: list[str], model_name: str) -> tuple[bool, list[str], str | None]:
    context_prompt = f"DATABASE SCHEMA FIELDS FOR REFERENCE: {schema_keys}\n\n{SYSTEM_PROMPT}\n\nLOG DATA CHUNK:\n{log_chunk}"
    payload = {"model": model_name, "prompt": context_prompt, "stream": False}
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
# DIFFERENTIAL ANALYSIS & REPORTING
# ----------------------------------------------------------------------------

def run_differential_analysis() -> list[str]:
    if not os.path.exists(DIR_MAY28) or not os.path.exists(DIR_JUNE01):
        return ["| N/A | Baseline Error | HIGH | Results directory mapping missing. |"]

    tampering_alerts = []
    may_files = {f for f in os.listdir(DIR_MAY28) if f.endswith(".json")}
    june_files = {f for f in os.listdir(DIR_JUNE01) if f.endswith(".json")}

    for f in may_files - june_files:
        tampering_alerts.append(f"| N/A | `{f}` | CRITICAL | File present on May 28, but MISSING on June 01. |")

    for f in may_files & june_files:
        path_may = os.path.join(DIR_MAY28, f)
        path_june = os.path.join(DIR_JUNE01, f)
        size_may = os.path.getsize(path_may)
        size_june = os.path.getsize(path_june)
        if size_june < (size_may * 0.5) and size_may > 1024:
            tampering_alerts.append(f"| N/A | `{f}` | HIGH | File size dropped significantly from {size_may} to {size_june} bytes. |")

    return tampering_alerts

def write_final_report(conn: sqlite3.Connection, differential_alerts: list[str], all_files: list[str]) -> None:
    with open(FINAL_REPORT_PATH, "w", encoding="utf-8") as repo:
        repo.write("# Comprehensive iOS Forensic Anomaly Report\n")
        repo.write("**Target Device:** iPhone 16 Pro Max  \n")
        repo.write(f"**Primary Baseline:** `{DIR_MAY28}`  \n")
        repo.write(f"**Comparative Target:** `{DIR_JUNE01}`  \n\n")

        repo.write("## Analysis Completeness\n\n")
        repo.write("| Source File | Total Chunks | Safe | Flagged | Failed | Pending | Model(s) | Status |\n")
        repo.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        
        any_incomplete = False
        any_mixed_model = False
        
        for fname in all_files:
            s = file_completion_summary(conn, fname)
            status = "complete" if s["complete"] else "INCOMPLETE — re-run to finish"
            if not s["complete"]:
                any_incomplete = True
            models = models_used_for_file(conn, fname)
            models_display = ", ".join(models) if models else "—"
            if len(models) > 1:
                models_display = f"⚠️ MIXED: {models_display}"
                any_mixed_model = True
            repo.write(f"| `{fname}` | {s['total']} | {s['safe']} | {s['flagged']} | {s['failed']} | {s['pending']} | {models_display} | {status} |\n")
        
        repo.write("\n")
        if any_incomplete:
            repo.write("> ⚠️ One or more files have incomplete chunks. Findings below reflect only completed chunks.\n\n")
        if any_mixed_model:
            repo.write("> ⚠️ Results contain findings from multiple model versions. Run with `--remodel` to unify.\n\n")

        repo.write("## ⚠️ Anti-Forensic Differential Alerts\n")
        if differential_alerts:
            repo.write("| Timestamp | Target File | Risk Level | Anomaly Description |\n")
            repo.write("| :--- | :--- | :--- | :--- |\n")
            for alert in differential_alerts:
                repo.write(f"{alert}\n")
        else:
            repo.write("> No database wiping detected between snapshots.\n")

        repo.write("\n## 🤖 AI-Flagged Behavioral Telemetry\n")
        repo.write("| Source File | Timestamp | Process / Domain / Artifact | Risk Level | Brief Technical Justification |\n")
        repo.write("| :--- | :--- | :--- | :--- | :--- |\n")
        any_rows = False
        for fname in all_files:
            for row in collect_flagged_rows(conn, fname):
                repo.write(f"| `{fname}` {row}\n")
                any_rows = True
        if not any_rows:
            repo.write("| _none_ | | | | No indicators of compromise isolated across completed chunks. |\n")

# ----------------------------------------------------------------------------
# MAIN EXECUTION
# ----------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LLM-assisted triage over MVT log output.")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_NAME, help="Ollama model name to run.")
    parser.add_argument("--max-concurrent", type=int, default=DEFAULT_MAX_CONCURRENT_CHUNKS, help="Max concurrent request threads.")
    parser.add_argument("--remodel", action="store_true", help="Re-queue chunks processed under a different model.")
    return parser.parse_args()

def process_file(conn: sqlite3.Connection, filename: str, chunks: list[str], schema_keys: list[str], outstanding: list[int], model_name: str, max_concurrent: int) -> None:
    def _run(chunk_index: int) -> tuple[int, bool, list[str], str | None]:
        ok, rows, error = query_local_llm(chunks[chunk_index], schema_keys, model_name)
        return chunk_index, ok, rows, error

    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        futures = [executor.submit(_run, idx) for idx in outstanding]
        for future in as_completed(futures):
            chunk_index, ok, rows, error = future.result()

            if not ok:
                record_chunk_result(conn, filename, chunk_index, "failed", model_name, error_message=error)
                log.warning(f"{filename} chunk {chunk_index + 1}/{len(chunks)}: FAILED — {error}")
            elif rows:
                record_chunk_result(conn, filename, chunk_index, "flagged", model_name, result_rows=rows)
                log.info(f"{filename} chunk {chunk_index + 1}/{len(chunks)}: FLAGGED ({len(rows)} row(s))")
            else:
                record_chunk_result(conn, filename, chunk_index, "safe", model_name)
                log.debug(f"{filename} chunk {chunk_index + 1}/{len(chunks)}: safe")

def main() -> None:
    args = parse_args()
    conn = init_checkpoint_db()

    stale = stale_model_chunk_counts(conn, args.model)
    if stale:
        stale_desc = ", ".join(f"{count} from {name or 'untracked'}" for name, count in stale)
        if args.remodel:
            reset_count = reset_stale_model_chunks(conn, args.model)
            log.info(f"--remodel active: Re-queued {reset_count} chunk(s) ({stale_desc}) for re-analysis under {args.model}.")
        else:
            log.warning(f"{sum(c for _, c in stale)} chunk(s) were analyzed under a different model ({stale_desc}). Pass --remodel to reprocess.")

    log.info("Phase 1: Gathering differential statistics")
    differential_alerts = run_differential_analysis()

    reachable, reason = check_ollama_reachable()
    if not reachable:
        log.error(f"Ollama connection check failed: {reason}")
        sys.exit(1)

    if not os.path.exists(DIR_MAY28):
        log.error(f"Baseline directory missing: {DIR_MAY28}")
        sys.exit(1)

    all_json_files = sorted([f for f in os.listdir(DIR_MAY28) if f.endswith(".json")])
    log.info(f"Phase 2: Analyzing {len(all_json_files)} file(s) with model '{args.model}' (Concurrency: {args.max_concurrent})")

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
                log.info(f"{filename}: Complete ({summary['total']} chunks) — skipping")
            continue

        log.info(f"{filename}: Processing {len(outstanding)}/{len(chunks)} outstanding chunks...")
        process_file(conn, filename, chunks, schema_keys, outstanding, args.model, args.max_concurrent)
        write_final_report(conn, differential_alerts, all_json_files)

    log.info("Phase 3: Finalizing forensic report")
    write_final_report(conn, differential_alerts, all_json_files)
    conn.close()

if __name__ == "__main__":
    main()
