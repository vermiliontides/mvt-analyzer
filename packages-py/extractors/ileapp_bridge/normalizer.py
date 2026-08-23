#!/usr/bin/env python3
"""
Verichron Epoch - iLEAPP Data Normalizer
Reads raw iLEAPP extraction outputs (SQLite/CSV) and transforms them 
into the unified Verichron normalized record schema format.
"""

import csv
import json
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from pathlib import Path


def normalize_timestamp(raw_ts) -> str | None:
    """Ensures timestamps conform to ISO 8601 UTC string format.

    Returns None when no real timestamp can be recovered from raw_ts,
    rather than fabricating one from the current wall-clock time. A
    fabricated "now" timestamp is worse than no timestamp: it silently
    lands inside someone's correlation window and reads as real evidence
    (see extractors/crash/main.py's parse_crash_time, which follows the
    same null-over-misleading-value convention for the same reason).
    """
    if not raw_ts:
        return None

    if isinstance(raw_ts, (int, float)):
        if raw_ts > 1e12:
            raw_ts /= 1000.0
        try:
            return datetime.fromtimestamp(raw_ts, tz=timezone.utc).isoformat()
        except (ValueError, OSError):
            return None

    if isinstance(raw_ts, str):
        try:
            dt = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            dt = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            return None

    return None


def build_normalized_record(source_artifact: str, timestamp: str | None, data: dict) -> dict:
    """Construct a single standardized record conforming to the extractor schema."""
    return {
        "schema_version": "1.0.0",
        "engine": "iLEAPP",
        "source_artifact": source_artifact,
        "timestamp": normalize_timestamp(timestamp),
        "data": data,
        "data": data,
    }



def list_supported_artifacts(output_dir: str | Path) -> list[Path]:
def list_supported_artifacts(output_dir: str | Path) -> list[Path]:
    out_path = Path(output_dir)
    if not out_path.exists():
        raise FileNotFoundError(f"iLEAPP output directory does not exist: {out_path}")

    supported = {".csv", ".tsv", ".db", ".sqlite"}
    return sorted(
        path for path in out_path.rglob("*") if path.is_file() and path.suffix.lower() in supported
    )


def parse_artifact_file(file_path: Path) -> list[dict]:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return _parse_tabular_artifact(file_path, delimiter=",")
    if suffix == ".tsv":
        return _parse_tabular_artifact(file_path, delimiter="\t")
    if suffix in {".db", ".sqlite"}:
        return _parse_sqlite_artifact(file_path)
    return []


def parse_ileapp_outputs(output_dir: str) -> list:
    """Walks the iLEAPP output directory and normalizes every supported artifact."""
    supported = {".csv", ".tsv", ".db", ".sqlite"}
    return sorted(
        path for path in out_path.rglob("*") if path.is_file() and path.suffix.lower() in supported
    )


def parse_artifact_file(file_path: Path) -> list[dict]:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return _parse_tabular_artifact(file_path, delimiter=",")
    if suffix == ".tsv":
        return _parse_tabular_artifact(file_path, delimiter="\t")
    if suffix in {".db", ".sqlite"}:
        return _parse_sqlite_artifact(file_path)
    return []


def parse_ileapp_outputs(output_dir: str) -> list:
    """Walks the iLEAPP output directory and normalizes every supported artifact."""
    normalized_records = []
    for file_path in list_supported_artifacts(output_dir):
        normalized_records.extend(parse_artifact_file(file_path))
    for file_path in list_supported_artifacts(output_dir):
        normalized_records.extend(parse_artifact_file(file_path))
    print(f"[+] Successfully normalized {len(normalized_records)} total records from iLEAPP output.")
    return normalized_records


def _parse_tabular_artifact(file_path: Path, delimiter: str = ",") -> list:

def _parse_tabular_artifact(file_path: Path, delimiter: str = ",") -> list:
    records = []
    artifact_name = file_path.stem
    try:
        with open(file_path, mode="r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
        with open(file_path, mode="r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            for row in reader:
                ts_candidate = None
                for key in row:
                    if any(token in key.lower() for token in ["time", "date", "timestamp", "created"]):
                for key in row:
                    if any(token in key.lower() for token in ["time", "date", "timestamp", "created"]):
                        ts_candidate = row.get(key)
                        if ts_candidate:
                            break
                records.append(
                    build_normalized_record(
                        source_artifact=artifact_name,
                        timestamp=ts_candidate,
                        data=dict(row),
                    )
                )
    except Exception as exc:  # pragma: no cover - defensive logging for malformed exports
        print(f"[-] Error parsing tabular file {file_path.name}: {exc}")
                records.append(
                    build_normalized_record(
                        source_artifact=artifact_name,
                        timestamp=ts_candidate,
                        data=dict(row),
                    )
                )
    except Exception as exc:  # pragma: no cover - defensive logging for malformed exports
        print(f"[-] Error parsing tabular file {file_path.name}: {exc}")
    return records



def _parse_sqlite_artifact(file_path: Path) -> list:
    records = []
    artifact_name = file_path.stem
    try:
        conn = sqlite3.connect(file_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table["name"]
            cursor.execute(f"SELECT * FROM [{table_name}]")
            while True:
                rows = cursor.fetchmany(1000)
                if not rows:
                    break
                for row in rows:
                    row_dict = dict(row)
                    ts_candidate = None
                    for key, value in row_dict.items():
                        key_lower = key.lower()
                        if any(token in key_lower for token in ["time", "date", "timestamp", "created"]):
                            ts_candidate = value
                            if ts_candidate:
                                break
                    records.append(
                        build_normalized_record(
                            source_artifact=f"{artifact_name}:{table_name}",
                            timestamp=ts_candidate,
                            data={str(k): (v.hex() if isinstance(v, bytes) else v) for k, v in row_dict.items()},
                        )
                    )
            cursor.execute(f"SELECT * FROM [{table_name}]")
            while True:
                rows = cursor.fetchmany(1000)
                if not rows:
                    break
                for row in rows:
                    row_dict = dict(row)
                    ts_candidate = None
                    for key, value in row_dict.items():
                        key_lower = key.lower()
                        if any(token in key_lower for token in ["time", "date", "timestamp", "created"]):
                            ts_candidate = value
                            if ts_candidate:
                                break
                    records.append(
                        build_normalized_record(
                            source_artifact=f"{artifact_name}:{table_name}",
                            timestamp=ts_candidate,
                            data={str(k): (v.hex() if isinstance(v, bytes) else v) for k, v in row_dict.items()},
                        )
                    )
        conn.close()
    except Exception as exc:  # pragma: no cover - defensive logging for malformed exports
        print(f"[-] Error parsing SQLite DB {file_path.name}: {exc}")
    except Exception as exc:  # pragma: no cover - defensive logging for malformed exports
        print(f"[-] Error parsing SQLite DB {file_path.name}: {exc}")
    return records


if __name__ == "__main__":
    import sys


    if len(sys.argv) < 2:
        print("Usage: python normalizer.py <path_to_ileapp_output_directory>")
        sys.exit(1)

    target_dir = sys.argv[1]
    results = parse_ileapp_outputs(target_dir)


    if results:
        print("\n--- Sample Normalized Record ---")
        print(json.dumps(results[0], indent=2))