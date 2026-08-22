"""
extractors/db_writer.py

Shared Postgres write helpers every Python extractor imports. This is the
concrete thing that makes the extractor contract's idempotency and
validation requirements load-bearing instead of aspirational — an
extractor author doesn't hand-write ingest/write SQL and hope it matches
the contract, they call these two functions.

Owns exactly what the two shared tables need:
  - ingest_file()  -> idempotent insert into ingested_files, keyed on file_hash
  - write_record() / write_records() -> validated insert into forensic_records

Deliberately does NOT own:
  - source-format parsing (each extractor's own code)
  - the `fields` sub-shape (each extractor owns and documents its own, per
    EXTRACTOR_CONTRACT.md #4)

A future TypeScript extractor needs the equivalent of this file written
against normalizedRecord.ts + node-postgres — not covered here since no TS
extractor exists yet, but same shape when one does.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras

# Resolve packages-py directory
_EXTRACTORS_DIR = Path(__file__).resolve().parent
_PACKAGES_PY = _EXTRACTORS_DIR.parent
sys.path.insert(0, str(_PACKAGES_PY / "contracts"))

from normalized_record import NormalizedRecord, SourceType  # noqa: E402

def compute_file_hash(path: str | Path) -> str:
    """sha256 of file contents — the idempotency key for ingested_files.
    Streamed in chunks so this doesn't load a large SMS attachment or
    gcloud log export fully into memory just to hash it."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ingest_file(
    conn,
    run_id: str,
    file_path: str | Path,
    source_type: str,
    raw_payload: dict[str, Any],
) -> tuple[str, bool]:
    """
    Idempotent insert into ingested_files.

    Returns (file_hash, already_ingested). When already_ingested is True,
    the caller should skip re-parsing and re-writing forensic_records for
    this file entirely — that's what makes "re-run the pipeline against the
    same backup" cheap (EXTRACTOR_CONTRACT.md #3), and it's checked BEFORE
    any insert is attempted, not via a race-prone insert-then-catch.
    """
    file_path = Path(file_path)
    file_hash = compute_file_hash(file_path)

    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM ingested_files WHERE file_hash = %s", (file_hash,))
        if cur.fetchone():
            return file_hash, True

        cur.execute(
            """
            INSERT INTO ingested_files
                (file_hash, run_id, file_path, file_name, source_type, raw_payload)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (file_hash) DO NOTHING
            """,
            (
                file_hash,
                run_id,
                str(file_path),
                file_path.name,
                source_type,
                psycopg2.extras.Json(raw_payload),
            ),
        )
    conn.commit()
    return file_hash, False


def write_record(conn, run_id: str, file_hash: str, record: NormalizedRecord) -> None:
    """
    Insert one validated NormalizedRecord into forensic_records.

    Takes a NormalizedRecord *instance*, not a dict — that's the enforcement
    point. There's no code path here that accepts an un-validated row; the
    Pydantic model has to construct successfully before this function can
    even be called. This is the class of bug the original crash-report
    extractor had (a field silently drifting from what the report expected)
    pushed as early as it can go — construction time, not report-render time.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO forensic_records
                (file_hash, run_id, incident_id, source_type, event_time,
                 bug_type, process_name, pid, bundle_id, fields)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                file_hash,
                run_id,
                record.incident_id,
                record.source_type.value,
                record.event_time,
                record.bug_type,
                record.process_name,
                record.pid,
                record.bundle_id,
                psycopg2.extras.Json(record.fields),
            ),
        )
    conn.commit()


def write_records(
    conn, run_id: str, file_hash: str, records: list[NormalizedRecord]
) -> int:
    """
    Bulk convenience wrapper — same validation guarantee as write_record,
    one round trip and one commit for the whole batch instead of one per
    row. Extractors processing a high-volume source (gcloud logs, SMS
    attachments) should call this instead of looping write_record(), or
    every row pays its own network round trip.

    Returns the number of records written.
    """
    if not records:
        return 0

    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO forensic_records
                (file_hash, run_id, incident_id, source_type, event_time,
                 bug_type, process_name, pid, bundle_id, fields)
            VALUES %s
            """,
            [
                (
                    file_hash,
                    run_id,
                    r.incident_id,
                    r.source_type.value,
                    r.event_time,
                    r.bug_type,
                    r.process_name,
                    r.pid,
                    r.bundle_id,
                    psycopg2.extras.Json(r.fields),
                )
                for r in records
            ],
        )
    conn.commit()
    return len(records)
