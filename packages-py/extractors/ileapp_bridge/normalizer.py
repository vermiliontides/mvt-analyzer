#!/usr/bin/env python3
"""
Verichron Epoch - iLEAPP Data Normalizer
Reads raw iLEAPP extraction outputs (SQLite/CSV) and transforms them 
into the unified Verichron normalized record schema format.
"""

import os
import csv
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

def normalize_timestamp(raw_ts) -> str:
    """Ensures timestamps conform to ISO 8601 UTC string format."""
    if not raw_ts:
        return datetime.now(timezone.utc).isoformat()
    
    if isinstance(raw_ts, (int, float)):
        # Handle Unix epoch timestamps (seconds or milliseconds)
        if raw_ts > 1e12:
            raw_ts /= 1000.0
        try:
            return datetime.fromtimestamp(raw_ts, tz=timezone.utc).isoformat()
        except (ValueError, OSError):
            pass

    if isinstance(raw_ts, str):
        # Return as-is if it looks like an ISO string, otherwise parse
        try:
            dt = datetime.fromisoformat(raw_ts.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            pass

    return datetime.now(timezone.utc).isoformat()

def build_normalized_record(source_artifact: str, timestamp: str, data: dict) -> dict:
    """
    Constructs a single standardized record conforming to the Verichron schema.
    """
    return {
        "schema_version": "1.0.0",
        "engine": "iLEAPP",
        "source_artifact": source_artifact,
        "timestamp": normalize_timestamp(timestamp),
        "data": data
    }

def parse_ileapp_outputs(output_dir: str) -> list:
    """
    Walks the iLEAPP output directory to locate generated SQLite and CSV reports,
    parsing them into unified normalized records.
    """
    out_path = Path(output_dir)
    if not out_path.exists():
        raise FileNotFoundError(f"iLEAPP output directory does not exist: {out_path}")

    normalized_records = []

 # Walk directory for .tsv, .csv, and .db reports
    for file_path in out_path.rglob("*"):
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            records = _parse_tabular_artifact(file_path, delimiter=",")
            normalized_records.extend(records)
        elif suffix == ".tsv":
            records = _parse_tabular_artifact(file_path, delimiter="\t")
            normalized_records.extend(records)
        elif suffix == ".db":
            records = _parse_sqlite_artifact(file_path)
            normalized_records.extend(records)

    print(f"[+] Successfully normalized {len(normalized_records)} total records from iLEAPP output.")
    return normalized_records

def _parse_csv_artifact(file_path: Path) -> list:
    records = []
    artifact_name = file_path.stem
    try:
        with open(file_path, mode="r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Attempt to find a likely timestamp column
                ts_candidate = None
                for key in row.keys():
                    if any(t_keyword in key.lower() for t_keyword in ["time", "date", "timestamp", "created"]):
                        ts_candidate = row.get(key)
                        if ts_candidate:
                            break

                records.append(build_normalized_record(
                    source_artifact=artifact_name,
                    timestamp=ts_candidate,
                    data=dict(row)
                ))
    except Exception as e:
        print(f"[-] Error parsing CSV {file_path.name}: {e}")
    return records

def _parse_sqlite_artifact(file_path: Path) -> list:
    records = []
    artifact_name = file_path.stem
    try:
        conn = sqlite3.connect(file_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table["name"]
            if table_name.startswith("sqlite_"):
                continue
            
            cursor.execute(f"SELECT * FROM [{table_name}] LIMIT 500;")
            rows = cursor.fetchall()
            
            for row in rows:
                row_dict = dict(row)
                ts_candidate = None
                for key in row_dict.keys():
                    if any(t_keyword in key.lower() for t_keyword in ["time", "date", "timestamp", "created"]):
                        ts_candidate = row_dict.get(key)
                        if ts_candidate:
                            break

                records.append(build_normalized_record(
                    source_artifact=f"{artifact_name}:{table_name}",
                    timestamp=ts_candidate,
                    data={str(k): (v.hex() if isinstance(v, bytes) else v) for k, v in row_dict.items()}
                ))
        conn.close()
    except Exception as e:
        print(f"[-] Error parsing SQLite DB {file_path.name}: {e}")
        
    return records

def _parse_tabular_artifact(file_path: Path, delimiter: str = ",") -> list:
    records = []
    artifact_name = file_path.stem
    try:
        with open(file_path, mode="r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                ts_candidate = None
                for key in row.keys():
                    if any(t_keyword in key.lower() for t_keyword in ["time", "date", "timestamp", "created"]):
                        ts_candidate = row.get(key)
                        if ts_candidate:
                            break

                records.append(build_normalized_record(
                    source_artifact=artifact_name,
                    timestamp=ts_candidate,
                    data=dict(row)
                ))
    except Exception as e:
        print(f"[-] Error parsing tabular file {file_path.name}: {e}")
    return records

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python normalizer.py <path_to_ileapp_output_directory>")
        sys.exit(1)

    target_dir = sys.argv[1]
    results = parse_ileapp_outputs(target_dir)
    
    # Optional: Print sample output of the first normalized record
    if results:
        print("\n--- Sample Normalized Record ---")
        print(json.dumps(results[0], indent=2))