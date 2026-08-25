#!/usr/bin/env python3
"""Extractor entrypoint for the iLEAPP bridge using the shared Postgres contract."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

_PY_ROOT = Path(__file__).resolve().parents[2]
if str(_PY_ROOT) not in sys.path:
    sys.path.insert(0, str(_PY_ROOT))
from runtime_env import fatal_if_missing_venv
from typing import Any

_EXTRACTORS_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _EXTRACTORS_DIR.parent.parent
sys.path.insert(0, str(_EXTRACTORS_DIR))
sys.path.insert(0, str(_REPO_ROOT / "packages-py" / "contracts"))

from db_writer import ingest_file, write_records  # noqa: E402
from etl_run import ETLRunResult  # noqa: E402
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


def process_artifact_file(conn, run_id: str, file_path: Path) -> ETLRunResult:
    result = ETLRunResult()
    records = parse_artifact_file(file_path)
    if not records:
        return result  # nothing in this artifact — empty, not a failure

    summary = _summarize_raw_payload(file_path, records)
    file_hash, already_ingested = ingest_file(
        conn,
        run_id,
        file_path,
        source_type=SourceType.ILEAPP_RECORD.value,
        raw_payload=summary,
    )
    if already_ingested:
        return result

    normalized_records = []
    for i, record in enumerate(records):
        try:
            normalized_records.append(normalize_record(record))
        except Exception as exc:
            result.fail(f"{file_path.name}[{i}]", f"malformed record ({exc})")

    if not normalized_records:
        # Every record in this artifact failed to normalize. Previously
        # this returned 0 with only a stderr print and no tracked failure
        # — a file where every row was malformed still exited 0, and the
        # orchestrator recorded the stage as "succeeded" while quietly
        # losing that file's data. Now it's counted in result.failed.
        return result

    written = write_records(conn, run_id, file_hash, normalized_records)
    result.ok(written)
    return result


def process_output_directory(db_url: str, run_id: str, output_dir: str) -> ETLRunResult:
    out_path = Path(output_dir)
    artifacts = list_supported_artifacts(out_path)
    if not artifacts:
        raise FileNotFoundError(f"No supported iLEAPP artifact files were found under {out_path}")

    result = ETLRunResult()
    conn = psycopg2.connect(db_url)
    try:
        for artifact in artifacts:
            try:
                file_result = process_artifact_file(conn, run_id, artifact)
            except Exception as exc:
                # Per-file isolation (EXTRACTOR_CONTRACT.md #5): one
                # unreadable/unparseable artifact must not abort the rest
                # of the output directory. Previously unguarded — an
                # exception from parse_artifact_file or ingest_file
                # propagated straight out of this loop and stopped every
                # artifact file after it, not just the bad one.
                result.fail(artifact.name, exc)
                continue
            result = result.merge(file_result)
        conn.commit()
        return result
    finally:
        conn.close()


def run_pipeline(artifact_path: str, output_dir: str, db_url: str, run_id: str | None = None) -> ETLRunResult:
    out_path = Path(output_dir)
    run_id = run_id or __import__("uuid").uuid4().hex

    extraction = run_ileapp_extraction(artifact_path, str(out_path))
    if extraction.get("status") != "success":
        raise RuntimeError(extraction.get("error") or "iLEAPP extraction failed without a detailed error")

    result = process_output_directory(db_url, run_id, str(out_path))
    print(f"[+] Persisted {result.succeeded} iLEAPP record(s) to Postgres for run {run_id}.")
    return result


def main() -> int:
    fatal_if_missing_venv()
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
        result = run_pipeline(args.backup_path, args.output_dir, args.db_url, run_id=args.run_id)
    except Exception as exc:
        print(f"[ileapp] extraction pipeline failed: {exc}", file=sys.stderr)
        return 1

    result.print_summary("ileapp")
    return result.exit_code


if __name__ == "__main__":
    fatal_if_missing_venv()
    sys.exit(main())