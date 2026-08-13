# Runbook: running the pipeline end to end

One-time setup, then the four commands you'll actually run repeatedly.
Every step here is idempotent — re-running any of them after a fix only
redoes the part that failed.

## One-time setup

```bash
git clone https://github.com/vermiliontides/mvt-analyzer.git
cd mvt-analyzer

cd orchestrator && pnpm install && cd ..      # or npm/yarn
cd mvt-runner && npm install && npm run build && cd ..
pip install psycopg2-binary pydantic --break-system-packages   # for extractors + reporting
```

## Every time you have new backups to process

Run these four in order. Each one is a separate stage of the system; none
of them start the next one automatically except step 4, which runs all the
extractors + the report as its own last internal stage.

### 1. Start Postgres

```bash
cd infra && docker compose up -d
cd ..
```

First boot of the `forensics_pgdata` volume auto-applies
`db/migrations/0001_init.sql` via `docker-entrypoint-initdb.d`. That hook
never fires again after the first boot.

### 2. Apply any migrations newer than 0001

```bash
python3 db/migrate.py --db-url postgresql://forensics:forensics_dev_only@localhost:5432/forensics
```

Safe to run every time, including the very first time (it detects
migrations the docker hook already applied and doesn't double-apply them).
Prints `up to date, nothing to apply` when there's nothing to do.

### 3. Decrypt backups with mvt-runner

```bash
cd mvt-runner
node dist/main.js --source ~/iPhone-Backups --workspace ~/mvt-workspace
cd ..
```

- `--source` — directory containing your raw `idevicebackup2` backup
  folders (one subfolder per backup)
- `--workspace` — where decrypted output, results, hashes, and logs go
- Prompts once for a password and reuses it across all backups by default;
  pass `--different-passwords` if they're not all the same
- Re-running skips any backup/stage already completed. Use `--force` to
  re-run `check-backup` only, or `--force-decrypt` to redo
  decrypt+repair+check for that backup

### 4. Run the extraction + reporting pipeline

```bash
cd orchestrator
DATABASE_URL=postgresql://forensics:forensics_dev_only@localhost:5432/forensics \
  pnpm run investigate --workspace ~/mvt-workspace
cd ..
```

This is the one command that runs everything downstream of decryption:
`crash` → `safari` → `sms` → `network` → `gcloud` → `report`, once per
backup mvt-runner decrypted under `~/mvt-workspace/decrypted/`. Extractor
stages that fail (or don't exist yet, like `safari`/`sms`/`network`/
`gcloud` right now) are recorded as failed and skipped over — they don't
block `crash` or `report` from running.

Prefer explicit backup paths instead of a whole workspace:

```bash
pnpm run investigate /path/to/decrypted/backup-a /path/to/decrypted/backup-b
```

## Re-running just the report

If you fixed something and only want to re-render the Markdown for a run
you already have (no need to re-run any extractor):

```bash
python3 reporting/generate_report.py \
  --run-id <uuid-from-orchestrator-output> \
  --db-url postgresql://forensics:forensics_dev_only@localhost:5432/forensics \
  --output investigation_report.md
```

The `run_id` is printed by the orchestrator at the start of each backup's
run (`[orchestrator] run <uuid> started against ...`) and in its final
per-backup summary.

## Quick sanity checks

```bash
# Is Postgres actually reachable and current?
python3 db/migrate.py --db-url postgresql://forensics:forensics_dev_only@localhost:5432/forensics
# -> "up to date, nothing to apply" means healthy + current

# What backups has mvt-runner decrypted so far?
ls ~/mvt-workspace/decrypted/

# What did the last orchestrator run actually do?
psql postgresql://forensics:forensics_dev_only@localhost:5432/forensics \
  -c "SELECT run_id, backup_source, started_at, finished_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 5;"
```
