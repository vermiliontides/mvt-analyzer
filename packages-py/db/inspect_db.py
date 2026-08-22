#!/usr/bin/env python3
"""
Verichron Epoch - Database Inspection & Verification Utility
Inspects the local forensic SQLite database to verify ingested record counts,
artifact sources, and sample schema structures.
"""

import sqlite3
import json
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "epoch_forensics.db"

def inspect_database(db_path: str = str(DEFAULT_DB_PATH)) -> None:
    path = Path(db_path)
    if not path.exists():
        print(f"[-] Database file not found at: {path}")
        print("[*] Run the ingestion pipeline first to generate records.")
        return

    print(f"==================================================")
    print(f"🔍 Inspecting Database: {path.name}")
    print(f"==================================================")

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Check total record count
    cursor.execute("SELECT COUNT(*) as total FROM normalized_records;")
    total_records = cursor.fetchone()["total"]
    print(f"\n[+] Total Normalized Records: {total_records}")

    if total_records == 0:
        print("[!] The database is currently empty.")
        conn.close()
        return

    # 2. Breakdown by Engine & Source Artifact
    print("\n--- Breakdown by Source Artifact ---")
    cursor.execute("""
        SELECT engine, source_artifact, COUNT(*) as count 
        FROM normalized_records 
        GROUP BY engine, source_artifact 
        ORDER BY count DESC;
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"  • Engine: {row['engine']} | Artifact: {row['source_artifact']} | Records: {row['count']}")

    # 3. Sample the Latest 2 Records
    print("\n--- Sample Records (Latest 2) ---")
    cursor.execute("""
        SELECT id, engine, source_artifact, timestamp, data, created_at 
        FROM normalized_records 
        ORDER BY id DESC 
        LIMIT 2;
    """)
    samples = cursor.fetchall()
    for s in samples:
        print(f"\n  [Record ID: {s['id']}]")
        print(f"    Engine:     {s['engine']}")
        print(f"    Artifact:   {s['source_artifact']}")
        print(f"    Timestamp:  {s['timestamp']}")
        print(f"    Ingested:   {s['created_at']}")
        
        # Safely load and pretty-print the JSON payload data
        try:
            parsed_data = json.loads(s['data'])
            # Truncate large data dictionaries for clean terminal viewing
            preview = {k: v for i, (k, v) in enumerate(parsed_data.items()) if i < 5}
            print(f"    Data Fields (Preview): {json.dumps(preview, indent=6)}")
        except Exception:
            print(f"    Data Raw: {s['data'][:100]}...")

    conn.close()
    print("\n==================================================")
    print("[+] Inspection complete.")

if __name__ == "__main__":
    inspect_database()