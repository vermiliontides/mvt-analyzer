# Extractor Contract

> **Canonical location.** `contracts/EXTRACTOR_CONTRACT.md` -- this file -- is
> the contract. There used to be two copies: this path held a short summary
> that declared *itself* canonical, while the full reference text (below) lived
> at `packages-ts/contracts/EXTRACTOR_CONTRACT.md` and was described as the
> "existing" copy. Contributors reading the canonical path got the summary and
> missed the actual requirements. The full text now lives at the canonical
> path and the duplicate is deleted.
>
> Language-native helpers live in `packages-py/contracts/` (Pydantic) and
> `packages-ts/contracts/` (Zod), both generated from
> `contracts/normalized-record.schema.json` -- see section 6.

This is the interface a new extractor must satisfy to be wired into the
orchestrator. It's deliberately thin — a subprocess contract, not a shared
library — because extractors are polyglot on purpose (see
`/docs/architecture.md`). Satisfying this contract is what makes adding a
new source additive instead of a change to
`packages-ts/orchestrator/main-orchestrator/main.ts`.

## 1. Invocation

The orchestrator runs each extractor as a subprocess:

```
<extractor-entrypoint> --run-id <uuid> --backup-path <path> --db-url <postgres-url> [--results-path <path>]
```

- `--run-id` — the `pipeline_runs.run_id` for this invocation. Every row the
  extractor writes (to `ingested_files` and `forensic_records`) must carry
  this run_id.
- `--backup-path` — path to the decrypted MVT backup (or relevant subset —
  e.g. the gcloud extractor may be pointed at a log export directory instead;
  document your extractor's expected input shape in its own README).
- `--db-url` — Postgres connection string. Extractors write directly; there
  is no intermediate queue or API for the current scale of this pipeline.
- `--results-path` — **optional**, `mvt-ios check-backup`'s output
  directory (`<workspace>/results/<name>/`, the sibling of
  `<workspace>/decrypted/<name>/`). The orchestrator derives and passes
  this best-effort for every stage; extractors that only need the
  decrypted backup (safari, sms, network — see §Option A note below)
  ignore it. Extractors that consume mvt-ios's own analysis output as
  primary evidence rather than re-parsing a raw artifact (currently just
  `extractors/mvt_iocs/`) require it, and should derive a sensible
  fallback from `--backup-path` and fail with a clear message if neither
  is usable — see `extractors/mvt_iocs/main.py`'s `resolve_results_path`
  for the reference implementation.

## 2. Exit codes

- `0` — stage succeeded. The orchestrator marks `pipeline_stage_status` as
  `succeeded`.
- non-zero — stage failed. The orchestrator marks the stage `failed`,
  records stderr as `error_message`, and **continues to the next stage**.
  A failing extractor must never take down the rest of the run — see
  "Failure handling" below.

## 3. Idempotency

Extractors must dedupe on `file_hash` (sha256 of the source file) before
writing to `ingested_files`. Re-running an extractor against a backup
that's already been ingested should be a fast no-op, not a duplicate-row
write. This is the same pattern already proven out in the original
`deep_ips_report.py` SQLite state table — just pointed at the shared
Postgres tables now.

## 4. Output shape

Every row written to `forensic_records` must be constructible as a
`NormalizedRecord` (see `normalized-record.schema.json` /
`normalized_record.py` / `normalizedRecord.ts`). Concretely:

- Validate against the shared envelope before writing — don't hand-write
  SQL inserts that bypass the Pydantic/Zod model, or a typo becomes a
  silent schema drift bug (this is exactly the class of bug the original
  crash-report extractor had, just one layer down).
- Anything specific to your domain goes in `fields` (JSONB) — you own that
  sub-shape and document it in your extractor's own README, since the
  top-level contract intentionally doesn't validate inside it.
- Always also write the untouched original payload to
  `ingested_files.raw_payload` — normalization is lossy by design, raw
  retention is what keeps that acceptable. (For a source file large enough
  that a full dump is impractical rather than merely inconvenient — e.g.
  `extractors/mvt_iocs/`'s `timeline.csv` input, which can run past 250k
  rows — a documented, justified deviation to summary metadata is
  acceptable; see that extractor's README for the reasoning and what it
  preserves instead.)
- The back-reference from a `forensic_records` row to its source file is
  `forensic_records.file_hash` (an enforced FK to `ingested_files`), passed
  explicitly as an argument to `write_record`/`write_records` — it is not,
  and should not become, a field on `NormalizedRecord` itself. Keeping it
  out of the record model is what lets one ingested file produce multiple
  `forensic_records` rows without each row needing to independently carry
  and keep correct the same reference.

## 5. Failure handling

Failure is expected and must be recoverable, not fatal:

- Catch your own errors. Don't let an unhandled exception propagate past
  your entrypoint — catch it, write a clear message to stderr, exit
  non-zero. The orchestrator's job is to isolate stage failures; your job
  is to fail with enough information that someone can actually fix it.
- Partial progress within a stage should still be visible. If you're
  processing 500 SMS attachments and #340 throws, prefer writing rows for
  1–339 and exiting non-zero over an all-or-nothing transaction that
  discards everything on one bad record. (Exception: if a partial write
  would be actively misleading — e.g. you can't tell which records are
  trustworthy — an all-or-nothing failure is the more honest choice. Use
  judgment; document which behavior your extractor chose in its README.)
- Re-running your extractor after a fix should pick up where it left off,
  not require a clean slate — this falls out of the idempotency
  requirement in #3.
- A stage that depends on more than one input file (e.g. `mvt_iocs`
  reading both `alerts.json` and `timeline.csv`) should process each
  input independently — one missing/malformed file shouldn't block
  output from the other.

## 6. Adding a new source_type

1. Add the value to the `source_type` enum in
   `contracts/normalized-record.schema.json` — the canonical schema — and
   then run:

   ```
   python3 scripts/sync_contracts.py --write
   ```

   That regenerates the enum in `packages-py/contracts/normalized_record.py`
   and `packages-ts/contracts/normalizedRecord.ts`. Do not hand-edit the enum
   in either mirror; the generated block is overwritten.

   This step used to read "add the value in all three files in the same
   commit". That instruction was followed for the mirrors and missed for the
   canonical schema, so `ileapp_record` existed in Pydantic and Zod but not in
   the JSON schema the adapters load — every iLEAPP record constructed fine
   and then failed JSON-schema validation. `sync_contracts.py --check` runs in
   CI and fails the build on that class of drift, so the agreement is no
   longer something anyone has to remember.
2. Add a migration if you need a new index on something inside `fields`
   you'll query often (GIN index already covers ad hoc lookups; a
   dedicated index is only needed if a query is slow in practice).
3. Write your extractor under `/extractors/<name>/` with its own README
   documenting: expected input shape, the sub-shape of `fields` it
   produces, and its chosen partial-failure behavior (see #5).
4. Register the stage name in `packages-ts/orchestrator/main-orchestrator/main.ts`'s stage list.
