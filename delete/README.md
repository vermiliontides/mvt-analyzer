# extractors/mvt_iocs

Consumes `mvt-ios check-backup`'s own analysis output — `alerts.json` and
`timeline.csv` — and writes normalized `forensic_records` rows with
`source_type: mvt_ioc_detection` and `source_type: timestamp_anomaly`.

## Why this extractor doesn't follow Option A

Every other MVT-based extractor (safari, sms, network) parses the raw
SQLite DB directly out of the decrypted backup, not mvt-ios's JSON
summary of it — that's the chain-of-custody argument in
`docs/architecture.md`: a report finding should be defensible against the
literal source file, not a second party's interpretation of it.

That argument doesn't apply here. `alerts.json` isn't mvt-ios's parse of
something more primary — it's mvt-ios's own analytical judgment ("this
matched a known indicator" / "this redirect looked suspicious"). There is
no more-primary source to prefer instead; the verdict only exists inside
mvt-ios's output. Re-implementing STIX2 indicator matching against
Amnesty/maintained threat feeds ourselves, just to have "our own" copy of
the same judgment, would be redundant effort for zero fidelity gain.
`timeline.csv` gets the same treatment for a different reason: mvt-ios
already builds a merged, timestamp-sorted index across every module on
every `check-backup` run — nothing in this pipeline consumed it before
this extractor existed, so this reuses it rather than re-deriving a worse
version of the same thing from `forensic_records`.

## Input

`--results-path` — the `results/<name>/` directory `mvt-ios check-backup`
wrote (NOT `decrypted/<name>/`, which every other extractor takes via
`--backup-path`). See `EXTRACTOR_CONTRACT.md` §1 amendment — the
orchestrator derives and passes this alongside `--backup-path` for every
stage now; extractors that don't need it just ignore it.

If `--results-path` is omitted (older orchestrator, manual invocation),
the extractor derives it by swapping `decrypted` for `results` in
`--backup-path`, matching mvt-runner's fixed workspace layout. Fails
loudly if that swap isn't possible rather than silently guessing.

Reads two files inside that directory:
- `alerts.json` — every detection/heuristic-flag mvt-ios produced for
  this backup.
- `timeline.csv` — mvt-ios's own cross-module merged timeline.
- `backup_info.json` — read only for `"Last Backup Date"`, which the
  timestamp-anomaly check needs as its reference point.

## `source_type: mvt_ioc_detection`

One row per `alerts.json` entry — timed or not. "Detection" is used
broadly here on purpose: `alerts.json` in practice mixes literal STIX2
indicator matches (`matched_indicator` populated) with mvt's own built-in
heuristics (`matched_indicator: null` — e.g. the fast-redirect and
lockdown-mode checks). Both are equally "mvt's own judgment about this
backup," so both are stored as the same source_type rather than
arbitrarily treating one as more legitimate than the other.

```json
{
  "level": "MEDIUM",
  "source_module": "safari_history",
  "message": "Redirect took less than a second! (0.27 milliseconds)",
  "matched_indicator": null,
  "original_event": { "...": "the full, unfiltered event object from alerts.json" }
}
```

`event_time` = parsed `event_time` (null for alerts that don't carry
one — e.g. a global-preference flag; these are still written, they just
can't participate in the report's correlation window). `bundle_id` /
`process_name` / `pid` are populated when present on the alert's `event`
object, null otherwise. `incident_id` = null (no natural per-alert
correlation key in the source format).

## `source_type: timestamp_anomaly`

One row per event, **across every module** in `timeline.csv`, whose own
timestamp is later than the backup itself was taken — plus a small grace
period to absorb ordinary clock/timezone slop. This is a check no
individual mvt module performs; each one only validates its own record
shape, never plausibility against the backup as a whole. Modules that
legitimately contain forward-looking data (currently just `Calendar` —
recurring holidays, upcoming events) are excluded, since a future
timestamp there isn't evidence of anything. New forward-looking modules
should be added to `FORWARD_LOOKING_PLUGINS` in `main.py`, not have their
false positives tolerated downstream.

```json
{
  "plugin": "SafariBrowserState",
  "event": "tab",
  "description": "Notifications — OnlyFans - https://onlyfans.com/my/notifications",
  "backup_date": "2026-05-28T11:23:38+00:00",
  "delta_from_backup_seconds": 977616042.69
}
```

`event_time` = the anomalous timestamp itself, so it lands on the same
time axis as everything else for correlation purposes.

## `raw_payload` — one documented deviation from the usual pattern

`ingested_files.raw_payload` normally holds the complete untouched
original (see `EXTRACTOR_CONTRACT.md` §4). For `alerts.json` that's
exactly what happens — it's small, and the full JSON is stored as-is.

For `timeline.csv`, a full-row dump isn't: a busy device's timeline can
run past 250k rows, and that already exists on disk as the literal raw
artifact — duplicating it wholesale into a JSONB column buys nothing.
`raw_payload` for `timeline.csv` instead stores summary metadata (row
count, per-plugin counts, the resolved backup date). Nothing is actually
lost: every row this extractor flags as an anomaly has its **complete**
original CSV row preserved in that record's own `fields`, which is the
part anyone auditing a specific finding will actually want.

## Partial-failure behavior

Per-file, not all-or-nothing between the two files: `alerts.json` and
`timeline.csv` are processed independently, so one missing/malformed file
doesn't block the other. Within `alerts.json`, one malformed entry is
skipped and logged (matching `crash`'s per-file model at one level down);
within `timeline.csv`, a malformed row is skipped (`len(row) < 4`) since
there's no plausible partial-corruption case worth failing loudly over at
that granularity — mirrors the `mvt_iocs` design in `Extractor
Requirements.md` §5's "small, structured, no plausible partial-corruption
case" reasoning, extended here to timeline rows specifically.

If the backup date can't be determined from `backup_info.json`, the
timestamp-anomaly check is skipped (not silently — it's counted as a
failure and logged) while `alerts.json` processing still proceeds
normally; missing one input shouldn't block the other.

## Known limitation

The correlation report section (`reporting/generate_report.py`) currently
correlates `mvt_ioc_detection` / `timestamp_anomaly` rows against whatever
else has landed in `forensic_records` for the same run — today, just
`crash_report`. Once safari/sms/network land, the same query
automatically picks them up with no changes needed here. Until then, the
report supplements with a direct (unvalidated, clearly labeled) read of
`timeline.csv` for domains that don't have their own extractor yet —
see that file's own docstring for the caveat.
