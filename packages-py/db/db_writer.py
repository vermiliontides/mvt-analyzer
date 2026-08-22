#!/usr/bin/env python3
"""
Verichron Epoch - Database Writer & Storage Engine (Idempotent & Resilient)
"""

import sqlite3
import json
import hashlib
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "epoch_forensics.db"

def get_connection(db_path: str = str(DEFAULT_DB_PATH)) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = str(DEFAULT_DB_PATH)) -> None:
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS normalized_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_hash TEXT UNIQUE NOT NULL,
            engine TEXT NOT NULL,
            source_artifact TEXT NOT NULL,
            timestamp TEXT,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_record_hash ON normalized_records(record_hash);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON normalized_records(timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_engine ON normalized_records(engine);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifact ON normalized_records(source_artifact);")

    conn.commit()
    conn.close()

def generate_record_hash(engine: str, artifact: str, timestamp: str, data: dict) -> str:
    """Creates a deterministic SHA-256 hash for idempotency and deduplication."""
    payload = f"{engine}:{artifact}:{timestamp}:{json.dumps(data, sort_keys=True)}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def insert_records(records: list, db_path: str = str(DEFAULT_DB_PATH)) -> int:
    """
    Idempotent batch insert. Existing duplicates (matching record_hash) are ignored,
    making safe restarts and multi-runs completely seamless.
    """
    if not records:
        print("[*] No records provided for insertion.")
        return 0

    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    rows_to_insert = []
    for r in records:
        engine = r.get("engine", "unknown")
        artifact = r.get("source_artifact", "unknown")
        timestamp = r.get("timestamp")
        data = r.get("data", {})
        
        r_hash = generate_record_hash(engine, artifact, timestamp, data)
        rows_to_insert.append((
            r_hash,
            engine,
            artifact,
            timestamp,
            json.dumps(data)
        ))

    inserted_count = 0
    try:
        cursor.execute("BEGIN TRANSACTION;")
        
        # INSERT OR IGNORE guarantees idempotency if the script is restarted or rerun
        cursor.executemany("""
            INSERT OR IGNORE INTO normalized_records (record_hash, engine, source_artifact, timestamp, data)
            VALUES (?, ?, ?, ?, ?)
        """, rows_to_insert)
        
        inserted_count = cursor.rowcount
        conn.commit()
        print(f"[+] Persistence complete. Inserted {inserted_count} new unique records (duplicates safely ignored).")
    except Exception as e:
        conn.rollback()
        print(f"[-] Database transaction failed, rolled back: {e}", file=sys.stderr)
        raise e
    finally:
        conn.close()

    return inserted_count