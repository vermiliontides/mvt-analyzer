#!/usr/bin/env python3
"""
extractors/mvt_iocs/main.py

Consumes mvt-ios's OWN analysis output as primary evidence:

  - results/<name>/alerts.json   -> source_type: mvt_ioc_detection
  - results/<name>/timeline.csv  -> source_type: timestamp_anomaly

This is the one extractor in the pipeline that deliberately does NOT
re-parse a raw artifact out of the decrypted backup (contrast with
safari/sms/network, which parse History.db/sms.db/DataUsage.sqlite
directly — see EXTRACTOR_CONTRACT.md and ./README.md "Why this extractor
doesn't follow Option A"). alerts.json IS the primary evidence for a
detection — mvt's own judgment that something matched an indicator or
heuristic is not a second-hand parse of something more authoritative;
there is no more-primary source to prefer instead. timeline.csv is mvt's
own already-built cross-module index, reused here rather than re-derived,
per the same reasoning.

Two source_types, two different questions:
  mvt_ioc_detection  — "what did mvt itself flag?" (one row per alerts.json
                        entry, timed or not — untimed alerts, e.g. a global
                        preference flag, are still stored; they just can't
                        participate in the report's correlation window)
  timestamp_anomaly  — "is there anything ACROSS EVERY MODULE whose own
                        timestamp is impossible given when this backup was
                        taken?" — a check no individual mvt module performs,
                        because each module only validates its own record
                        shape, never plausibility against the backup itself.

See ./README.md for the fields sub-shape, the FORWARD_LOOKING_PLUGINS
exclusion rationale, and partial-failure behavior.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_PY_ROOT = Path(__file__).resolve().parents[2]
if str(_PY_ROOT) not in sys.path:
    sys.path.insert(0, str(_PY_ROOT))
from runtime_env import fatal_if_missing_venv
from typing import Any

_EXTRACTORS_DIR = Path(__file__).resolve().parent.parent  # packages-py/extractors
_PACKAGES_PY = _EXTRACTORS_DIR.parent                      # packages-py

sys.path.insert(0, str(_EXTRACTORS_DIR))
sys.path.insert(0, str(_PACKAGES_PY / "contracts"))
from db_writer import ingest  # noqa: E402
from normalized_record import NormalizedRecord, SourceType  # noqa: E402

import psycopg2


# Modules that legitimately contain forward-looking, scheduled data rather
# than a record of something that already happened — a calendar is SUPPOSED
# to have future entries (recurring holidays, upcoming appointments); that
# is not evidence of anything. Excluding them is what keeps the anomaly
# check a signal instead of drowning in expected future dates. New forward-
# looking modules (reminders, alarms, ...) should be added here, not have
# their false positives tolerated downstream.
FORWARD_LOOKING_PLUGINS = {"Calendar"}

# Grace period past the backup timestamp before something counts as an
# anomaly — small enough to not mask real findings, large enough to absorb
# ordinary clock/timezone slop between the device and the machine that ran
# mvt-ios.
ANOMALY_GRACE = timedelta(days=1)


def parse_ts(s: Any) -> datetime | None:
    if not isinstance(s, str) or not s.strip():
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def resolve_results_path(results_path: str | None, backup_path: str) -> Path:
    """--results-path is the preferred, explicit input (see
    EXTRACTOR_CONTRACT.md #1 amendment — the orchestrator derives and
    passes it). Falls back to swapping 'decrypted' for 'results' in
    --backup-path for older orchestrator builds or manual invocation,
    since that's mvt-runner's fixed workspace layout
    (<workspace>/decrypted/<name> and <workspace>/results/<name> are
    siblings)."""
    if results_path:
        return Path(results_path)
    p = Path(backup_path)
    parts = list(p.parts)
    if "decrypted" in parts:
        idx = parts.index("decrypted")
        parts[idx] = "results"
        return Path(*parts)
    raise ValueError(
        f"could not derive a results/ path from --backup-path {backup_path!r} "
        f"(no 'decrypted' segment to swap) — pass --results-path explicitly"
    )


# --- alerts.json -> mvt_ioc_detection ---------------------------------


def alert_to_record(alert: dict) -> NormalizedRecord:
    """One row per alerts.json entry, timed or not. 'detection' here
    covers both literal STIX2 indicator matches (matched_indicator set)
    and mvt's own built-in heuristics (matched_indicator null, e.g. the
    fast-redirect / lockdown-mode checks) — that's what alerts.json
    actually contains in practice, and both are equally "mvt's own
    judgment", so both get stored rather than only the narrower
    IOC-matched subset."""
    event = alert.get("event")
    if not isinstance(event, dict):
        event = {}

    return NormalizedRecord(
        incident_id=None,
        source_type=SourceType.MVT_IOC_DETECTION,
        event_time=parse_ts(alert.get("event_time")),
        bug_type=None,
        process_name=event.get("process_name"),
        pid=event.get("pid"),
        bundle_id=event.get("bundle_id"),
        fields={
            "level": alert.get("level"),
            "source_module": alert.get("module"),
            "message": alert.get("message"),
            "matched_indicator": alert.get("matched_indicator"),
            "original_event": event,
        },
    )


def process_alerts(conn, run_id: str, results_dir: Path) -> tuple[int, int, list[str]]:
    path = results_dir / "alerts.json"
    if not path.exists():
        return 0, 0, [f"{path.name}: not found — skipping detection ingest for this backup"]

    errors: list[str] = []

    # The parse happens inside the transaction. Previously ingest_file()
    # committed the ledger row first, so the `could not parse` return below left
    # a committed row with zero records -- and dedup keyed on that row existing,
    # so alerts.json was never re-read on any later run. A single malformed
    # alerts.json permanently removed every mvt-ios detection from the evidence
    # set while the stage kept reporting success.
    try:
        with ingest(
            conn,
            run_id,
            path,
            source_type=SourceType.MVT_IOC_DETECTION.value,
        ) as unit:
            if unit.already_ingested:
                return 0, 0, []  # dedup: a prior run finished this file

            alerts = json.loads(path.read_text())

            # The payload is only knowable after parsing. Same transaction now,
            # rather than the old insert-{} / commit / parse / update / commit
            # sequence that left a second window where the ledger disagreed
            # with reality.
            unit.set_raw_payload(alerts)

            records = []
            for i, alert in enumerate(alerts):
                try:
                    records.append(alert_to_record(alert))
                except Exception as e:
                    errors.append(f"{path.name}[{i}]: failed to normalize ({e})")

            written = unit.write(records)
    except Exception as e:
        # Rolled back: no ledger row, so the next run retries this file.
        return 0, 1, [f"{path.name}: could not ingest ({e})"]

    return written, len(errors), errors


# --- timeline.csv -> timestamp_anomaly ---------------------------------


def get_backup_date(results_dir: Path) -> datetime | None:
    """The one piece of context this check needs that isn't in
    timeline.csv itself: when was the backup actually taken? mvt-ios
    already writes this to backup_info.json (results/<name>/) alongside
    everything else, so no new CLI surface is needed for it."""
    path = results_dir / "backup_info.json"
    if not path.exists():
        return None
    try:
        info = json.loads(path.read_text())
    except Exception:
        return None
    return parse_ts(info.get("Last Backup Date"))


def anomaly_to_record(ts: datetime, plugin: str, event: str, desc: str, backup_date: datetime) -> NormalizedRecord:
    delta = ts - backup_date
    return NormalizedRecord(
        incident_id=None,
        source_type=SourceType.TIMESTAMP_ANOMALY,
        event_time=ts,
        bug_type=None,
        process_name=None,
        pid=None,
        bundle_id=None,
        fields={
            "plugin": plugin,
            "event": event,
            "description": desc,
            "backup_date": backup_date.isoformat(),
            "delta_from_backup_seconds": delta.total_seconds(),
        },
    )


def process_timeline(conn, run_id: str, results_dir: Path) -> tuple[int, int, list[str]]:
    path = results_dir / "timeline.csv"
    if not path.exists():
        return 0, 0, [f"{path.name}: not found — skipping timestamp-anomaly check for this backup"]

    backup_date = get_backup_date(results_dir)
    if backup_date is None:
        return 0, 1, [
            f"could not determine backup date from backup_info.json — "
            f"skipping timestamp-anomaly check (this is the one thing this "
            f"check needs that isn't self-contained in timeline.csv)"
        ]

    # timeline.csv is mvt's own already-parsed, already-JSON-safe artifact
    # (one row per already-normalized event) — unlike a raw SQLite DB, a
    # full-row raw_payload dump here doesn't lose anything a summary would,
    # but at ~250k+ rows for a busy device it's not worth writing wholesale
    # into a JSONB column. raw_payload stores summary metadata instead; the
    # complete original row for every anomaly this stage finds is still
    # fully preserved in that record's own `fields` — nothing is lost, it's
    # just not duplicated in full alongside it. See README "raw_payload"
    # for this documented deviation from the usual whole-file dump.
    row_count = 0
    plugin_counts: dict[str, int] = {}
    anomalies: list[NormalizedRecord] = []
    cutoff = backup_date + ANOMALY_GRACE

    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 4:
                continue
            row_count += 1
            ts_raw, plugin, event, desc = row[0], row[1], row[2], row[3]
            plugin_counts[plugin] = plugin_counts.get(plugin, 0) + 1

            if plugin in FORWARD_LOOKING_PLUGINS:
                continue
            ts = parse_ts(ts_raw)
            if ts is None or ts <= cutoff:
                continue
            anomalies.append(anomaly_to_record(ts, plugin, event, desc, backup_date))

    try:
        with ingest(
            conn,
            run_id,
            path,
            source_type=SourceType.TIMESTAMP_ANOMALY.value,
            raw_payload={
                "row_count": row_count,
                "plugin_counts": plugin_counts,
                "backup_date": backup_date.isoformat(),
            },
        ) as unit:
            if unit.already_ingested:
                return 0, 0, []  # dedup: a prior run finished this file
            written = unit.write(anomalies)
    except Exception as e:
        # Rolled back: no ledger row, so the next run retries this file.
        return 0, 1, [f"{path.name}: could not ingest ({e})"]

    return written, 0, []


# --- main ----------------------------------------------------------------


def main():
    fatal_if_missing_venv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--backup-path", required=True)
    parser.add_argument("--results-path", default=None, help="results/<name>/ dir; derived from --backup-path if omitted")
    parser.add_argument("--db-url", required=True)
    args = parser.parse_args()

    try:
        results_dir = resolve_results_path(args.results_path, args.backup_path)
    except ValueError as e:
        print(f"[mvt_iocs] {e}", file=sys.stderr)
        sys.exit(1)

    if not results_dir.exists():
        print(f"[mvt_iocs] results directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        conn = psycopg2.connect(args.db_url)
    except Exception as e:
        print(f"[mvt_iocs] could not connect to database: {e}", file=sys.stderr)
        sys.exit(1)

    total_written = 0
    total_failed = 0
    all_errors: list[str] = []

    try:
        w, f, errs = process_alerts(conn, args.run_id, results_dir)
        total_written += w
        total_failed += f
        all_errors += errs

        w, f, errs = process_timeline(conn, args.run_id, results_dir)
        total_written += w
        total_failed += f
        all_errors += errs
    except Exception as e:
        print(f"[mvt_iocs] unhandled error: {e}", file=sys.stderr)
        conn.close()
        sys.exit(1)
    finally:
        conn.close()

    print(f"[mvt_iocs] {total_written} record(s) written, {total_failed} issue(s)")
    for e in all_errors:
        print(f"[mvt_iocs]   {e}", file=sys.stderr)

    sys.exit(1 if total_failed else 0)


if __name__ == "__main__":
    fatal_if_missing_venv()
    main()
