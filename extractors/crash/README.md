# extractors/crash

Parses iOS `.ips` crash and analytics-telemetry files (SpringBoard crashes,
watchdog kills, Siri/analytics reports — anything the OS writes as `.ips`)
out of a decrypted backup and writes one `forensic_records` row per file.

Ported from the original `deep_ips_report.py` prototype; the parsing logic
(`parse_ips_file`, `extract_rich_telemetry`) is carried over close to
unchanged — it was already solid. What changed is where state and output
go: the prototype's own `crash_state.db` SQLite table is gone, replaced by
the shared `ingested_files` table (Postgres, keyed on `file_hash`, via
`extractors/db_writer.py`); its own Markdown rendering is gone too — that's
`reporting/generate_report.py`'s job now, reading `forensic_records`.

## Expected input shape

`--backup-path` is searched recursively for `*.ips` files
(`Path(backup_path).rglob("*.ips")`). No assumption is made about where
under the decrypted backup they live — mvt-ios's `decrypt-backup`
reconstructs the original relative paths, so this just walks the whole tree.

## `fields` sub-shape

Everything without a dedicated top-level column on `forensic_records`:

```json
{
  "filename": "...",
  "os_version": "...",
  "hardware_model": "...",
  "cpu_type": "...",
  "bundle_version": "...",
  "parent_proc": "...",
  "parent_pid": 1,
  "proc_launch": "...",
  "proc_path": "...",
  "proc_role": "...",
  "time_awake_since_boot": 5000,
  "exception": { "type": "...", "signal": "...", "code": "...", "subcode": "..." },
  "termination": { "namespace": "...", "code": 6, "by": "..." },
  "faulting_thread": 0,
  "is_simulated": false,
  "is_non_fatal": false,
  "asi": ["..."],
  "vm_region_info": "..."
}