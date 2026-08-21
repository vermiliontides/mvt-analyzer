# iOS Forensic Investigation Pipeline

## What this is

A pipeline that takes an MVT-decrypted iOS backup and produces a single,
honest report correlating findings across multiple domains — crash
telemetry, Safari history, SMS, network usage, and gcloud logs — on a
shared time axis.

## Architecture at a glance

Each top-level directory answers one question:

| Directory | Question it answers |
| :--- | :--- |
| `orchestrator/` | How does a run happen? |
| `extractors/` | How does one source format become normalized data? |
| `reporting/` | How does normalized data become a human-readable artifact? |
| `contracts/` | What does normalized data look like? |
| `db/` | Where does it live? |
| `infra/` | How do I stand up dependencies locally? |
| `docs/` | Why is it built this way? |

Full rationale, including why this is a shared-contract ETL pattern rather
than microservices, and why extractors are deliberately polyglot: see
[`docs/architecture.md`](docs/architecture.md).

## Why not one service

Different source formats (`.ips` crash JSON, SQLite Safari history, SMS
attachments, network usage tables, gcloud log exports) favor different
tooling — Python for ad hoc forensic parsing, TypeScript where process
orchestration already lives. Rather than force a single runtime, every
extractor normalizes into one shared schema and writes to one Postgres
store. Language choice per extractor is a local decision; the contract is
the only thing that has to stay consistent. Details in
[`docs/architecture.md`](docs/architecture.md).

## How a run works

1. `orchestrator/main.ts` creates a `pipeline_runs` row and a `pending`
   `pipeline_stage_status` row per stage.
2. Each extractor runs as an isolated subprocess. **A failing stage does
   not abort the run** — the orchestrator records the failure and moves
   on to the next stage.
3. `reporting/generate_report.py` runs last, reads `pipeline_stage_status`
   first, and renders an honest preface: what succeeded, what failed
   (and why), what was never attempted — before rendering any findings.
4. Fixing a failed extractor and re-running the pipeline against the same
   backup is safe and cheap: extractors dedupe on file hash, so only the
   previously-failed work actually re-runs.

This is a deliberate design choice, not an afterthought — see "Failure is
isolated, not fatal" in [`docs/architecture.md`](docs/architecture.md).

## Running it locally

```bash
# 1. Start Postgres (fresh volume: migrations auto-apply via docker-entrypoint-initdb.d)
cd infra && docker compose up -d

# 1a. Applying a new migration to an already-running database (not a fresh
#     volume)? The docker-entrypoint hook above only fires once, on first
#     boot, so use the migration runner instead:
python3 ../db/migrate.py --db-url postgresql://forensics:forensics_dev_only@localhost:5432/forensics

# 2. Decrypt your backups with mvt-runner (separate tool, see mvt-runner/)
cd ../mvt-runner && npm install && npm run build
node dist/main.js --source ~/iPhone-Backups --workspace ~/mvt-workspace

# 3. Install orchestrator deps
cd ../orchestrator && pnpm install   # or npm/yarn — see package.json

# 4. Run the pipeline against everything mvt-runner just decrypted
DATABASE_URL=postgresql://forensics:forensics_dev_only@localhost:5432/forensics \
  pnpm run investigate --workspace ~/mvt-workspace

# ...or against specific decrypted-backup directories directly:
DATABASE_URL=postgresql://forensics:forensics_dev_only@localhost:5432/forensics \
  pnpm run investigate /path/to/decrypted/backup-a /path/to/decrypted/backup-b
```

Re-running `pnpm run investigate --workspace ...` after new backups have
been decrypted only processes what's new — a backup with a prior
fully-succeeded run (no failed stages) is skipped automatically.

## Adding a new extractor

See [`contracts/EXTRACTOR_CONTRACT.md`](contracts/EXTRACTOR_CONTRACT.md)
for the full process-level contract (invocation, exit codes, idempotency,
output shape, failure handling). Short version: any language is fine as
long as it satisfies that contract and validates every record it writes
against the shared `NormalizedRecord` schema
(`contracts/normalized-record.schema.json`).

## Status

| Domain | Extractor status |
| :--- | :--- |
| Crash telemetry (`.ips`) | Migrating from standalone script — see `extractors/crash/README.md` |
| Safari history | Not yet built — design notes in `extractors/safari/README.md` |
| SMS | Not yet built — design notes in `extractors/sms/README.md` |
| Network usage | Not yet built — design notes in `extractors/network/README.md` |
| gcloud logs | Not yet built — design notes in `extractors/gcloud/README.md` |
