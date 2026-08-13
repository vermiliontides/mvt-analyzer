# Extractor Contract

This is the interface a new extractor must satisfy to be wired into the
orchestrator. It's deliberately thin — a subprocess contract, not a shared
library — because extractors are polyglot on purpose (see
`/docs/architecture.md`). Satisfying this contract is what makes adding a
new source additive instead of a change to `orchestrator/main.ts`.

## 1. Invocation

The orchestrator runs each extractor as a subprocess:

```
<extractor-entrypoint> --run-id <uuid> --backup-path <path> --db-url <postgres-url>
```

- `--run-id` — the `pipeline_runs.run_id` for this invocation. Every row the
  extractor writes (to `ingested_files` and `forensic_records`) must carry
  this run_id.
- `--backup-path` — path to the decrypted MVT backup (or relevant subset —
  e.g. the gcloud extractor may be pointed at a log export directory instead;
  document your extractor's expected input shape in its own README).
- `--db-url` — Postgres connection string. Extractors write directly; there
  is no intermediate queue or API for the current scale of this pipeline.

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
  retention is what keeps that acceptable.

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

## 6. Adding a new source_type

1. Add the value to the `source_type` enum in all three contract files
   (`.schema.json`, `.py`, `.ts`) — same commit.
2. Add a migration if you need a new index on something inside `fields`
   you'll query often (GIN index already covers ad hoc lookups; a
   dedicated index is only needed if a query is slow in practice).
3. Write your extractor under `/extractors/<name>/` with its own README
   documenting: expected input shape, the sub-shape of `fields` it
   produces, and its chosen partial-failure behavior (see #5).
4. Register the stage name in `orchestrator/main.ts`'s stage list.
