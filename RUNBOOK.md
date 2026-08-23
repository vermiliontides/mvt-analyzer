# Runbook: running the pipeline end to end

This project is currently organized as a mixed workspace, so the operational
sequence is slightly different from the older monolithic path names. The live
layout is:

- `infra/` for Postgres
- `packages-ts/orchestrator/mvt-runner` for the mvt-ios wrapper
- `packages-ts/orchestrator/main-orchestrator` for the orchestration CLI
- `packages-py/db/migrate.py` for DB migrations
- `packages-py/reporting/generate_report.py` for report rendering

The logic is the same as the architecture describes: decrypt backups,
normalize them into a shared contract, run extractor stages, and render an
honest report that shows what succeeded and what failed.

## One-time setup

```bash
git clone https://github.com/vermiliontides/mvt-analyzer.git
cd mvt-analyzer
pnpm install
```

## Every time you have new backups to process

### 1. Start Postgres

```bash
cd infra && docker compose up -d
cd ..
```

### 2. Apply migrations

```bash
python3 packages-py/db/migrate.py --db-url postgresql://forensics:forensics_dev_only@localhost:5432/forensics
```

This is safe to run repeatedly; it is idempotent and will report when nothing
new needs to be applied.

### 3. Decrypt backups with the mvt-runner helper

```bash
cd packages-ts/orchestrator/mvt-runner
npm install
npm run build
node dist/main.js --source ./backups --workspace ./mvt-workspace
cd ../../..
```

- `--source` is the directory containing the raw encrypted backup folders.
- `--workspace` is where `mvt-runner` writes decrypted output, results, and
  logs.
- Re-running is intentionally incremental; already-completed work is skipped.

### 4. Run the extraction + reporting pipeline

```bash
cd packages-ts/orchestrator/main-orchestrator
DATABASE_URL=postgresql://forensics:forensics_dev_only@localhost:5432/forensics \
  pnpm run investigate --workspace ./mvt-workspace
cd ../../..
```

The orchestrator runs each extractor stage under the same backup run and keeps
failing stages isolated instead of aborting the whole job. It records stage
status, so the final report can say exactly what succeeded, what failed, and
what was never attempted.

You can also target explicit decrypted backups directly:

```bash
cd packages-ts/orchestrator/main-orchestrator
DATABASE_URL=postgresql://forensics:forensics_dev_only@localhost:5432/forensics \
  pnpm run investigate /path/to/decrypted/backup-a /path/to/decrypted/backup-b
```

## Re-running just the report

If you already have a `run_id` and only want to render the Markdown output again:

```bash
python3 packages-py/reporting/generate_report.py \\
  --run-id <uuid-from-orchestrator-output> \
  --db-url postgresql://forensics:forensics_dev_only@localhost:5432/forensics \
  --output investigation_report.md
```

The `run_id` is emitted by the orchestrator and can be used to regenerate the
report without re-running the extractors.

## Quick sanity checks

```bash
# Is Postgres reachable and up to date?
python3 packages-py/db/migrate.py --db-url postgresql://forensics:forensics_dev_only@localhost:5432/forensics

# What backups are already decrypted?
ls ./mvt-workspace/decrypted/

# What runs have happened recently?
psql postgresql://forensics:forensics_dev_only@localhost:5432/forensics \
  -c "SELECT run_id, backup_source, started_at, finished_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 5;"
```
