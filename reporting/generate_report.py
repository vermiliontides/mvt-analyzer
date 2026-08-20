#!/usr/bin/env python3
"""
reporting/generate_report.py

Reads forensic_records + pipeline_stage_status for a run and renders the
Markdown artifact. This replaces the report-generation half of the original
deep_ips_report.py — that file's PARSING logic moves to /extractors/crash,
its RENDERING logic (and rendering for every other domain) lives here.

Two things this file must always do, per the "fix, don't punish" principle:
  1. Query pipeline_stage_status FIRST and render an honest preface —
     which domains are present, which failed, which were never run.
  2. Never let a missing/failed domain silently disappear from the report.
     A failed stage gets a visible "not available" note, not omission.
"""

import argparse
import sys
from datetime import datetime, UTC

import psycopg2
import psycopg2.extras


def fetch_stage_status(conn, run_id: str) -> list[dict]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT stage_name, status, error_message, started_at, finished_at
            FROM pipeline_stage_status
            WHERE run_id = %s
            ORDER BY stage_name
            """,
            (run_id,),
        )
        return cur.fetchall()


def fetch_records_by_source_type(conn, run_id: str, source_type: str) -> list[dict]:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT incident_id, source_type, event_time, bug_type,
                   process_name, pid, bundle_id, fields
            FROM forensic_records
            WHERE run_id = %s AND source_type = %s
            ORDER BY event_time NULLS LAST
            """,
            (run_id, source_type),
        )
        return cur.fetchall()


def render_stage_preface(stages: list[dict]) -> list[str]:
    """The honesty section — what's actually in this report, up front."""
    lines = ["## Run Completeness", ""]
    lines.append("| Stage | Status | Note |")
    lines.append("| :--- | :--- | :--- |")
    for s in stages:
        status = s["status"]
        note = s["error_message"] or ""
        if status == "failed":
            note = f"FAILED — {note}. Fix and re-run the pipeline against the same backup; already-succeeded stages will not be redone."
        elif status == "pending":
            note = "never ran"
        lines.append(f"| {s['stage_name']} | {status} | {note} |")
    lines.append("")
    return lines


# TODO: one render_<source_type>_section() per domain as extractors land.
# Keep each renderer scoped to its own domain's `fields` shape — this file
# should never need to know the internal shape of, say, safari_history's
# fields to render crash_report's section, matching the extractor contract's
# ownership boundaries.
def render_crash_section(records: list[dict]) -> list[str]:
    lines = ["## Crash Reports", "", "| Incident | Process | PID | Bug Type | Event Time |", "| :--- | :--- | :--- | :--- | :--- |"]
    for r in records:
        lines.append(
            f"| `{r['incident_id'] or 'N/A'}` | {r['process_name'] or 'Unknown'} "
            f"| `{r['pid']}` | `{r['bug_type']}` | `{r['event_time'] or 'unknown'}` |"
        )
    lines.append("")

    for r in records:
        fields = r["fields"] or {}
        lines.append(f"### `{r['incident_id'] or fields.get('filename', 'unknown')}`")
        lines.append(f"- **Source file:** `{fields.get('filename')}`")
        lines.append(
            f"- **OS:** `{fields.get('os_version')}` | **Hardware:** `{fields.get('hardware_model')}` "
            f"| **Arch:** `{fields.get('cpu_type')}`"
        )
        lines.append(
            f"- **Bundle:** `{r['bundle_id']}` (`{fields.get('bundle_version')}`)"
        )
        lines.append(
            f"- **Process:** `{r['process_name']}` (PID `{r['pid']}`), spawned by "
            f"`{fields.get('parent_proc')}` (PID `{fields.get('parent_pid')}`)"
        )
        exc = fields.get("exception") or {}
        if exc:
            lines.append(
                f"- **Exception:** `{exc.get('type')}` / signal `{exc.get('signal')}` "
                f"(code `{exc.get('code')}`, subcode `{exc.get('subcode')}`)"
            )
        term = fields.get("termination") or {}
        if term:
            lines.append(
                f"- **Termination:** namespace `{term.get('namespace')}`, code `{term.get('code')}`, "
                f"by `{term.get('by')}`"
            )
        asi = fields.get("asi") or []
        if asi:
            lines.append("- **Application Specific Info:**")
            for msg in asi:
                lines.append(f"  > `{msg}`")
        lines.append("")

    return lines


RENDERERS = {
    "crash_report": render_crash_section,
    # "safari_history": render_safari_section,
    # ...
}


def generate_report(conn, run_id: str, output_path: str) -> None:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    stages = fetch_stage_status(conn, run_id)

    lines = [
        "# Forensic Investigation Report",
        f"**Run ID:** `{run_id}`  ",
        f"**Generated:** {timestamp}  ",
        "",
        "---",
        "",
    ]
    lines += render_stage_preface(stages)
    lines.append("---")
    lines.append("")

    for source_type, renderer in RENDERERS.items():
        records = fetch_records_by_source_type(conn, run_id, source_type)
        if not records:
            continue
        lines += renderer(records)
        lines.append("---")
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    print(f"[reporting] wrote {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--backup-path", required=False)  # unused here, present for contract consistency
    parser.add_argument("--db-url", required=True)
    parser.add_argument("--output", default="investigation_report.md")
    args = parser.parse_args()

    try:
        conn = psycopg2.connect(args.db_url)
    except Exception as e:
        print(f"[reporting] could not connect to database: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        generate_report(conn, args.run_id, args.output)
    except Exception as e:
        print(f"[reporting] failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()