# crash extractor

Parses `.ips` files (crash reports + adjacent telemetry: Siri feedback, SFA
analytics, xp_amp) found in an MVT-decrypted backup and writes normalized
`forensic_records` rows.

## Status

Migrating from the original standalone `deep_ips_report.py`. That script's
**parsing logic** (classification, per-source-type field extraction) moves
here; its **rendering logic** moves to `/reporting`. The classify → parse →
normalize architecture discussed for this extractor:

- Classifier: filename pattern first (`ExcUserFault_*` → crash, `SiriSearchFeedback*`
  → siri_feedback, `SFA-*` → sfa_analytics, `xp_amp_*` → xp_amp_telemetry),
  payload-shape sniffing as fallback/verification.
- Parser registry: one function per `source_type`, each owning its own
  field extraction — see `/contracts/EXTRACTOR_CONTRACT.md`.
- `bug_type` is stored but is NOT the primary classifier signal (308/309 are
  well-corroborated as genuine crash schemas; 313/226/237 are inferred from
  this dataset only, not public Apple documentation — treat as
  confirmatory, not authoritative).

## fields (JSONB) shape — crash_report

```
{
  "exception": { "type": ..., "signal": ..., "code": ..., "subcode": ... },
  "termination": { "namespace": ..., "code": ..., "by": ... },
  "parent_proc": ..., "parent_pid": ...,
  "proc_launch": ..., "proc_role": ..., "proc_path": ...,
  "os_build": ...,          -- flattened from the osVersion dict, not the raw dict itself
  "time_awake_since_boot": ...,
  "asi": [...]
}
```

## fields (JSONB) shape — siri_feedback / sfa_analytics / xp_amp_telemetry

TBD once payload shapes for these are fully characterized — see the crash
analysis review earlier in this project for why these were previously
mis-extracted using the crash schema.

## Partial-failure behavior

TBD — decide and document per `/contracts/EXTRACTOR_CONTRACT.md` §5 when
this extractor is filled in (per-file, so one malformed `.ips` shouldn't
block the rest of the batch, consistent with the idempotent per-file hash
tracking already proven out in the original script).
