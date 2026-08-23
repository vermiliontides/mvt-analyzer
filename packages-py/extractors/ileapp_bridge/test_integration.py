#!/usr/bin/env python3
"""
Integration test suite for the iLEAPP extractor.

Tests the full pipeline:
  - Bridge validation and artifact detection
  - Normalizer parsing (CSV/TSV/SQLite)
  - NormalizedRecord schema validation
  - Idempotent file hashing
  - Partial failure handling (skip malformed records)
"""

import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "contracts"))

from ileapp_bridge.normalizer import parse_ileapp_outputs, list_supported_artifacts, parse_artifact_file
from ileapp_bridge.main import normalize_record
from ileapp_bridge.bridge import run_ileapp_extraction
from db_writer import compute_file_hash
from normalized_record import NormalizedRecord, SourceType


def test_normalizer_csv() -> None:
    """Test CSV parsing and normalization."""
    print("TEST: CSV parsing...")
    tmpdir = tempfile.mkdtemp()
    try:
        csv_file = Path(tmpdir) / "history.csv"
        csv_file.write_text(
            "url,visit_count,timestamp\n"
            "https://example.com,5,2024-01-15T10:30:00Z\n"
            "https://test.com,3,2024-01-15T10:35:00Z\n"
        )

        records = parse_artifact_file(csv_file)
        assert len(records) == 2, f"Expected 2 records, got {len(records)}"
        assert records[0]["engine"] == "iLEAPP"
        assert records[0]["source_artifact"] == "history"
        assert "url" in records[0]["data"]
        print("  ✓ CSV parsing works correctly")
    finally:
        import shutil
        shutil.rmtree(tmpdir)


def test_normalizer_sqlite() -> None:
    """Test SQLite parsing and normalization."""
    print("TEST: SQLite parsing...")
    tmpdir = tempfile.mkdtemp()
    try:
        db_file = Path(tmpdir) / "sms.db"
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
                phone TEXT,
                message TEXT,
                timestamp TEXT
            )
            """
        )
        cursor.execute("INSERT INTO messages VALUES (1, '+1234567890', 'hello', '2024-01-15T10:30:00Z')")
        cursor.execute("INSERT INTO messages VALUES (2, '+1987654321', 'world', '2024-01-15T10:35:00Z')")
        conn.commit()
        conn.close()

        records = parse_artifact_file(db_file)
        assert len(records) == 2, f"Expected 2 records, got {len(records)}"
        assert records[0]["engine"] == "iLEAPP"
        assert records[0]["source_artifact"] == "sms:messages"
        assert "phone" in records[0]["data"]
        print("  ✓ SQLite parsing works correctly")
    finally:
        import shutil
        shutil.rmtree(tmpdir)


def test_normalizer_mixed_artifacts() -> None:
    """Test parsing of multiple artifact types in a directory."""
    print("TEST: Mixed artifacts parsing...")
    tmpdir = tempfile.mkdtemp()
    try:
        csv_file = Path(tmpdir) / "safari.csv"
        csv_file.write_text("url,timestamp\nhttps://example.com,2024-01-15T10:30:00Z\n")

        tsv_file = Path(tmpdir) / "network.tsv"
        tsv_file.write_text("iface\tbytes\ttimestamp\neth0\t1000\t2024-01-15T10:30:00Z\n")

        artifacts = list_supported_artifacts(tmpdir)
        assert len(artifacts) == 2, f"Expected 2 artifacts, got {len(artifacts)}"

        all_records = parse_ileapp_outputs(tmpdir)
        assert len(all_records) == 2, f"Expected 2 total records, got {len(all_records)}"
        print("  ✓ Mixed artifact parsing works correctly")
    finally:
        import shutil
        shutil.rmtree(tmpdir)


def test_schema_validation() -> None:
    """Test that normalized records conform to the NormalizedRecord schema."""
    print("TEST: Schema validation...")
    tmpdir = tempfile.mkdtemp()
    try:
        csv_file = Path(tmpdir) / "test.csv"
        csv_file.write_text("id,data,timestamp\n1,sample,2024-01-15T10:30:00Z\n")

        records = parse_artifact_file(csv_file)
        normalized = normalize_record(records[0])

        # Validate type
        assert isinstance(normalized, NormalizedRecord)
        assert normalized.source_type == SourceType.ILEAPP_RECORD
        assert normalized.event_time is not None

        # Validate fields structure
        assert "engine" in normalized.fields
        assert normalized.fields["engine"] == "iLEAPP"
        assert "source_artifact" in normalized.fields

        print("  ✓ Schema validation passed")
    finally:
        import shutil
        shutil.rmtree(tmpdir)


def test_partial_failure_malformed_records() -> None:
    """Test that malformed records are skipped without failing the entire file."""
    print("TEST: Partial failure (malformed records)...")
    tmpdir = tempfile.mkdtemp()
    try:
        csv_file = Path(tmpdir) / "mixed.csv"
        # Mix of valid and invalid timestamp formats
        csv_file.write_text(
            "id,timestamp,data\n"
            "1,2024-01-15T10:30:00Z,good\n"
            "2,,missing_timestamp\n"
            "3,2024-01-15T10:35:00Z,also_good\n"
        )

        records = parse_artifact_file(csv_file)
        # All records should parse (timestamp is optional in raw_record)
        assert len(records) == 3, f"Expected 3 records, got {len(records)}"

        normalized_records = []
        for record in records:
            try:
                normalized_records.append(normalize_record(record))
            except Exception:
                pass

        # All should normalize successfully since we allow missing timestamps
        assert len(normalized_records) == 3
        print("  ✓ Partial failure handling works correctly")
    finally:
        import shutil
        shutil.rmtree(tmpdir)


def test_file_hashing_idempotency() -> None:
    """Test that file hashing is deterministic for idempotent deduplication."""
    print("TEST: File hashing idempotency...")
    tmpdir = tempfile.mkdtemp()
    try:
        test_file = Path(tmpdir) / "data.csv"
        test_file.write_text("id,value\n1,test\n")

        hash1 = compute_file_hash(test_file)
        hash2 = compute_file_hash(test_file)

        assert hash1 == hash2, "File hash not deterministic"
        assert len(hash1) == 64, "SHA256 hash should be 64 hex characters"

        # Modify file and verify hash changes
        test_file.write_text("id,value\n1,modified\n")
        hash3 = compute_file_hash(test_file)
        assert hash1 != hash3, "File hash should change after modification"

        print("  ✓ File hashing idempotency works correctly")
    finally:
        import shutil
        shutil.rmtree(tmpdir)


def test_large_sqlite_table_streaming() -> None:
    """Test that large SQLite tables are streamed in batches to avoid memory blowup."""
    print("TEST: Large table streaming...")
    tmpdir = tempfile.mkdtemp()
    try:
        db_file = Path(tmpdir) / "large.db"
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, data TEXT, timestamp TEXT)")

        # Insert 2500 rows (will be fetched in 1000-row batches)
        for i in range(2500):
            cursor.execute(
                "INSERT INTO events VALUES (?, ?, ?)",
                (i, f"event_{i}", f"2024-01-15T{10 + i // 3600:02d}:30:00Z"),
            )
        conn.commit()
        conn.close()

        records = parse_artifact_file(db_file)
        assert len(records) == 2500, f"Expected 2500 records, got {len(records)}"
        print("  ✓ Large table streaming works correctly")
    finally:
        import shutil
        shutil.rmtree(tmpdir)


def test_timestamp_normalization() -> None:
    """Test that timestamps in various formats are normalized to ISO8601 UTC,
    and that an unparseable timestamp comes back null rather than a
    fabricated wall-clock value.

    normalize_timestamp() deliberately does NOT fall back to
    datetime.now(UTC) for missing/invalid input (see normalizer.py's
    docstring) — a fabricated "now" would silently land inside someone's
    correlation window and read as real evidence. A record with a
    genuinely unparseable source timestamp must produce a null
    event_time, matching extractors/crash/main.py's parse_crash_time
    convention.
    """
    print("TEST: Timestamp normalization...")
    tmpdir = tempfile.mkdtemp()
    try:
        csv_file = Path(tmpdir) / "timestamps.csv"
        csv_file.write_text(
            "id,timestamp,data\n"
            "1,2024-01-15T10:30:00Z,iso8601\n"
            "2,2024-01-15 10:30:00,space_separated\n"
            "3,invalid_timestamp,bad_format\n"
        )

        records = parse_artifact_file(csv_file)
        normalized_list = [normalize_record(r) for r in records]

        # Parseable timestamps normalize to a real value.
        assert normalized_list[0].event_time is not None
        assert normalized_list[1].event_time is not None
        # Unparseable timestamp must come back null, not a fabricated "now".
        assert normalized_list[2].event_time is None

        # Verify ISO8601 format with timezone on a parsed value.
        event_time_str = str(normalized_list[0].event_time)
        assert "+" in event_time_str or "Z" in event_time_str, f"Expected timezone in {event_time_str}"

        print("  ✓ Timestamp normalization works correctly")
    finally:
        import shutil
        shutil.rmtree(tmpdir)


def main() -> None:
    """Run all tests."""
    print("=" * 60)
    print("iLEAPP Extractor Integration Test Suite")
    print("=" * 60)

    tests = [
        test_normalizer_csv,
        test_normalizer_sqlite,
        test_normalizer_mixed_artifacts,
        test_schema_validation,
        test_partial_failure_malformed_records,
        test_file_hashing_idempotency,
        test_large_sqlite_table_streaming,
        test_timestamp_normalization,
    ]

    failed = []
    for test in tests:
        try:
            test()
        except Exception as exc:
            print(f"  ✗ FAILED: {exc}")
            failed.append((test.__name__, exc))

    print("=" * 60)
    if failed:
        print(f"\n{len(failed)} test(s) failed:")
        for name, exc in failed:
            print(f"  - {name}: {exc}")
        sys.exit(1)
    else:
        print(f"\n✓ All {len(tests)} tests passed")
        sys.exit(0)


if __name__ == "__main__":
    main()