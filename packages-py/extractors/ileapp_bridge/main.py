#!/usr/bin/env python3
"""Extractor entrypoint for the iLEAPP bridge using the shared Postgres contract."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_EXTRACTORS_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _EXTRACTORS_DIR.parent.parent
sys.path.insert(0, str(_EXTRACTORS_DIR))
sys.path.insert(0, str(_REPO_ROOT / "packages-py" / "contracts"))

from db_writer import ingest_file, write_records  # noqa: E402
from normalized_record import NormalizedRecord, SourceType  # noqa: E402

# Add the bridge module to the path for import
_BRIDGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_BRIDGE_DIR))
from bridge import run_ileapp_extraction  # noqa: E402
from normalizer import list_supported_artifacts, parse_artifact_file  # noqa: E402

import psycopg2


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _clean_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _clean_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return str(value)


def normalize_record(raw_record: dict) -> NormalizedRecord:
    data = raw_record.get("data") or {}
    if not isinstance(data, dict):
        data = {"value": data}

    fields = {"engine": raw_record.get("engine", "iLEAPP"), "source_artifact": raw_record.get("source_artifact", "unknown")}
    for key, value in data.items():
        fields[str(key)] = _clean_value(value)

    record = NormalizedRecord(
        incident_id=(data.get("incident_id") or data.get("id") or None),
        source_type=SourceType.ILEAPP_RECORD,
        event_time=_coerce_datetime(raw_record.get("timestamp") or data.get("timestamp")),
        bug_type=data.get("bug_type"),
        process_name=(data.get("process_name") or data.get("name") or None),
        pid=_coerce_int(data.get("pid")),
        bundle_id=(data.get("bundle_id") or data.get("bundleID") or None),
        fields=fields,
    )
    return record


def _summarize_raw_payload(file_path: Path, records: list[dict]) -> dict[str, Any]:
    sample = []
    for item in records[:10]:
        sample.append(_clean_value(item.get("data", {})))
    return {
        "artifact_name": file_path.name,
        "artifact_path": str(file_path),
        "format": file_path.suffix.lower().lstrip("."),
        "record_count": len(records),
        "sample_records": sample,
    }


def process_artifact_file(conn, run_id: str, file_path: Path) -> int:
    records = parse_artifact_file(file_path)
    if not records:
        return 0

    summary = _summarize_raw_payload(file_path, records)
    file_hash, already_ingested = ingest_file(
        conn,
        run_id,
        file_path,
        source_type=SourceType.ILEAPP_RECORD.value,
        raw_payload=summary,
    )
    if already_ingested:
        return 0

    normalized_records = []
    for record in records:
        try:
            normalized_records.append(normalize_record(record))
        except Exception as exc:  # pragma: no cover - logged per-file, not fatal to the rest
            print(f"[-] Dropping malformed record from {file_path.name}: {exc}", file=sys.stderr)

    if not normalized_records:
        return 0

    written = write_records(conn, run_id, file_hash, normalized_records)
    return written


def process_output_directory(db_url: str, run_id: str, output_dir: str) -> int:
    out_path = Path(output_dir)
    artifacts = list_supported_artifacts(out_path)
    if not artifacts:
        raise FileNotFoundError(f"No supported iLEAPP artifact files were found under {out_path}")

    conn = psycopg2.connect(db_url)
    try:
        total = 0
        for artifact in artifacts:
            total += process_artifact_file(conn, run_id, artifact)
        conn.commit()
        return total
    finally:
        conn.close()


def run_pipeline(artifact_path: str, output_dir: str, db_url: str, run_id: str | None = None) -> int:
    out_path = Path(output_dir)
    run_id = run_id or __import__("uuid").uuid4().hex

    extraction = run_ileapp_extraction(artifact_path, str(out_path))
    if extraction.get("status") != "success":
        raise RuntimeError(extraction.get("error") or "iLEAPP extraction failed without a detailed error")

    total = process_output_directory(db_url, run_id, str(out_path))
    print(f"[+] Persisted {total} iLEAPP record(s) to Postgres for run {run_id}.")
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the iLEAPP bridge using the repo's shared Postgres extractor contract")
    parser.add_argument("--run-id", required=True, help="Pipeline run id assigned by the orchestrator")
    parser.add_argument("--backup-path", required=True, help="Decrypted iPhone backup or extraction directory")
    parser.add_argument("--db-url", required=True, help="Postgres connection string")
    parser.add_argument("--output", "--output-dir", dest="output_dir", default="./ileapp_raw_output", help="Directory for raw iLEAPP output")
    parser.add_argument("--clean", action="store_true", help="Remove any existing staging directory before extraction")
    parser.add_argument("--results-path", dest="results_path", default=None, help="Unused compatibility flag for the shared extractor contract")

    args = parser.parse_args()

    try:
        if args.clean and Path(args.output_dir).exists():
            import shutil
            shutil.rmtree(args.output_dir)
        run_pipeline(args.backup_path, args.output_dir, args.db_url, run_id=args.run_id)
        return 0
    except Exception as exc:
        print(f"[ileapp] extraction pipeline failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
