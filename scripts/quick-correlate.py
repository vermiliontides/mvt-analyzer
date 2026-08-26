#!/usr/bin/env python3
"""
scripts/quick-correlate.py — standalone, no-Postgres sanity check for a
single mvt-ios check-backup output directory.

WHAT THIS IS FOR: everything this file does is now also done, more
durably, by the real pipeline — extractors/mvt_iocs/main.py persists the
same detections/anomalies into forensic_records, and
reporting/generate_report.py renders the same correlation view from
there. This script exists for the step BEFORE that: a quick eyeball of
what mvt-ios found immediately after `mvt-ios check-backup` finishes,
without decrypting via mvt-runner's exact workspace convention, without
Postgres running, without creating a pipeline_runs row. Point it straight
at a results/<name>/ directory and read the Markdown on stdout.

Use this when:
  - You just ran mvt-ios by hand (or via mvt-runner) and want a fast look
    at correlated findings before deciding whether the backup is worth
    formally ingesting into the pipeline.
  - You're debugging why the real pipeline's correlation section is
    showing (or not showing) something — this script's --window-minutes
    and --backup-date flags let you override values the orchestrator
    normally derives automatically, which is useful for isolating whether
    an issue is in the window/date logic or somewhere else.
  - Postgres isn't running and you don't want to stand it up just to
    check one backup.

Do NOT use this as a substitute for actually running the pipeline: its
output isn't persisted anywhere, isn't visible to generate_report.py, and
doesn't get the benefit of cross-domain correlation against crash/safari/
sms/network data once those extractors exist — it only ever sees what's
in this one results/ directory. Treat it as a magnifying glass, not a
record of findings.

The two things this script checks, same as extractors/mvt_iocs/main.py's
persisted checks (kept in sync manually — if you change the anomaly/
correlation logic here, mvt_iocs/main.py needs the equivalent change,
and vice versa):

  1. CORRELATION: for every alert/detection with a real event_time, pulls
     every other event across every mvt module within a time window, using
     mvt's own already-generated results/<name>/timeline.csv as the
     cross-domain index instead of re-deriving one. (mvt already builds this
     file on every run; nothing in the pipeline currently reads it.)

  2. TIMESTAMP-PLAUSIBILITY CHECK: flags any event across ANY module whose
     timestamp is later than the backup itself — something no built-in mvt
     module checks for, because each module only validates its own record
     shape, never the record's temporal plausibility against the backup
     as a whole.

Input: a directory of raw `mvt-ios check-backup` output (alerts.json +
timeline.csv at minimum). Output: a Markdown report to stdout.

Usage:
    python scripts/quick-correlate.py --results-dir <path> \\
        --backup-date "2026-05-28 11:23:38" [--window-minutes 15]
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# This file lives at <repo-root>/scripts/quick-correlate.py, so packages-py
# (where runtime_env.py lives) is one level up, then into packages-py —
# different from correlate.py's old location under packages-py/core/,
# which only needed to go up one level to reach packages-py itself.
_PACKAGES_PY = Path(__file__).resolve().parents[1] / "packages-py"
if str(_PACKAGES_PY) not in sys.path:
    sys.path.insert(0, str(_PACKAGES_PY))
from runtime_env import fatal_if_missing_venv

CORRELATION_WINDOW = timedelta(minutes=15)
# Modules whose per-second churn is real but not semantically interesting
# for a human reading a correlation window (backup-internal bookkeeping,
# not device/user activity). Counted, not dumped line-by-line.
LOW_SIGNAL_PLUGINS = {"Manifest"}


def parse_ts(s: str):
    s = s.strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def load_alerts(results_dir: Path):
    """Alerts/detections that carry a real event_time — these are the
    correlation pivot points. Ones with an empty event_time (e.g. a global
    preference flag with no natural timestamp) are reported separately,
    since there's nothing to correlate them against."""
    alerts_path = results_dir / "alerts.json"
    if not alerts_path.exists():
        return [], []
    data = json.loads(alerts_path.read_text())
    timed, untimed = [], []
    for a in data:
        ts = parse_ts(a.get("event_time", ""))
        if ts:
            timed.append((ts, a))
        else:
            untimed.append(a)
    return timed, untimed


def load_timeline(results_dir: Path):
    """mvt's own already-built cross-module timeline. Loaded once, sorted,
    then windowed per-alert — cheaper and more honest than each extractor
    re-deriving its own event_time independently and never cross-checking
    against the others."""
    tpath = results_dir / "timeline.csv"
    rows = []
    if not tpath.exists():
        return rows
    with tpath.open(newline="", encoding="utf-8", errors="replace") as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) < 4:
                continue
            ts = parse_ts(row[0])
            if ts is None:
                continue
            rows.append((ts, row[1], row[2], row[3]))
    rows.sort(key=lambda x: x[0])
    return rows


def window(rows, center, delta=CORRELATION_WINDOW):
    lo, hi = center - delta, center + delta
    # rows is sorted; linear scan is fine at this size but a bisect would
    # be the move if this ever runs against a much longer timeline.
    return [r for r in rows if lo <= r[0] <= hi]


def summarize_window(rows, pivot_ts):
    """Splits a correlation window into 'signal' (shown per-line) and
    'low-signal churn' (counted, not dumped) — this is what keeps a
    correlation section readable instead of drowning a real finding in
    hundreds of Manifest file-touch rows."""
    signal, churn = [], {}
    for ts, plugin, event, desc in rows:
        if plugin in LOW_SIGNAL_PLUGINS:
            churn[plugin] = churn.get(plugin, 0) + 1
            continue
        signal.append((ts, plugin, event, desc))
    return signal, churn


# Modules that legitimately contain forward-looking, scheduled data rather
# than a record of something that already happened — a calendar is SUPPOSED
# to have future entries (recurring holidays, upcoming appointments); that's
# not evidence of anything. Excluding them is what keeps this check a signal
# instead of drowning in expected future dates.
FORWARD_LOOKING_PLUGINS = {"Calendar"}


def find_timestamp_anomalies(rows, backup_date: datetime, grace=timedelta(days=1)):
    """The check no individual mvt module performs: is this event's own
    timestamp later than the backup that supposedly contains it? For
    modules that record something that already happened (history, usage,
    messages, tab state, interactions, ...) there's no legitimate way for
    a backup to contain a record dated after the backup itself — that's a
    different failure mode than an implausibly OLD timestamp (which can be
    entirely legitimate, e.g. Calendar's undated-birthday convention
    anchored to 1604)."""
    cutoff = backup_date + grace
    return [
        (ts, plugin, event, desc)
        for ts, plugin, event, desc in rows
        if ts > cutoff and plugin not in FORWARD_LOOKING_PLUGINS
    ]


def fmt_desc(desc, maxlen=140):
    d = desc.strip()
    return d if len(d) <= maxlen else d[: maxlen - 1] + "…"


def main():
    fatal_if_missing_venv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", required=True, type=Path)
    ap.add_argument("--backup-date", required=True, help="e.g. '2026-05-28 11:23:38' (from backup_info.json 'Last Backup Date')")
    ap.add_argument("--window-minutes", type=int, default=15)
    args = ap.parse_args()

    global CORRELATION_WINDOW
    CORRELATION_WINDOW = timedelta(minutes=args.window_minutes)

    backup_date = parse_ts(args.backup_date)
    if backup_date is None:
        print(f"error: could not parse --backup-date {args.backup_date!r}", file=sys.stderr)
        sys.exit(2)

    timed_alerts, untimed_alerts = load_alerts(args.results_dir)
    timeline = load_timeline(args.results_dir)

    out = []
    out.append("# Cross-Domain Correlation Report\n")
    out.append(f"Backup date: `{backup_date.isoformat()}`  ")
    out.append(f"Correlation window: ±{args.window_minutes} min  ")
    out.append(f"Timeline events indexed: {len(timeline)}  ")
    out.append(f"Alerts with a timestamp: {len(timed_alerts)}  ")
    out.append(f"Alerts without a timestamp (reported separately): {len(untimed_alerts)}\n")

    out.append("## Section 1 — Alert correlation (what mvt flagged, in context)\n")
    for ts, alert in sorted(timed_alerts, key=lambda x: x[0]):
        rows = window(timeline, ts)
        signal, churn = summarize_window(rows, ts)
        out.append(f"### `{ts.isoformat()}` — {alert.get('level')} — {alert.get('module')}")
        out.append(f"> {alert.get('message')}")
        ev = alert.get("event", {})
        if "url" in ev:
            out.append(f"- **URL:** `{ev['url']}`")
        out.append("")
        if signal:
            out.append(f"**Correlated activity (±{args.window_minutes} min, {len(signal)} event(s), excluding backup-internal churn):**\n")
            out.append("| Time | Module | Event |")
            out.append("| :--- | :--- | :--- |")
            for rts, plugin, event, desc in signal:
                marker = " ← ALERT" if rts == ts else ""
                out.append(f"| {rts.strftime('%H:%M:%S.%f')[:-3]}{marker} | {plugin} | {fmt_desc(desc)} |")
        else:
            out.append("_No correlated activity found in other modules within the window._")
        if churn:
            churn_desc = ", ".join(f"{v} {k}" for k, v in churn.items())
            out.append(f"\n_(+{sum(churn.values())} low-signal backup-bookkeeping event(s) omitted: {churn_desc})_")
        out.append("")

    if untimed_alerts:
        out.append("## Section 2 — Alerts with no timestamp (not correlatable)\n")
        for a in untimed_alerts:
            out.append(f"- **{a.get('level')} / {a.get('module')}:** {a.get('message')} — `{a.get('event')}`")
        out.append("")

    out.append("## Section 3 — Timestamp-plausibility anomalies (new check; not an mvt alert type)\n")
    anomalies = find_timestamp_anomalies(timeline, backup_date)
    if anomalies:
        out.append(f"**{len(anomalies)} event(s) timestamped AFTER the backup was taken** "
                    f"(`{backup_date.isoformat()}`) — impossible under normal device operation, "
                    f"worth investigating for clock tampering, anti-forensic timestomping, or an "
                    f"upstream parsing bug:\n")
        out.append("| Time | Module | Event | Description | Δ from backup |")
        out.append("| :--- | :--- | :--- | :--- | :--- |")
        for ts, plugin, event, desc in anomalies:
            delta = ts - backup_date
            years = delta.days / 365.25
            out.append(f"| {ts.isoformat()} | {plugin} | {event} | {fmt_desc(desc)} | +{years:.1f} yr |")
    else:
        out.append("No events found with a timestamp later than the backup date.")
    out.append("")

    print("\n".join(out))


if __name__ == "__main__":
    fatal_if_missing_venv()
    main()
