# Verichron Epoch / MVT Analyzer

This repository is a mixed workspace for a forensic investigation pipeline and
its local desktop client. The code is organized by responsibility and runtime,
not by a single monolithic service layout.

## What is in this repo

| Path | Purpose |
| :--- | :--- |
| `epoch/` | Electron + React desktop client for reviewing findings and timelines. |
| `packages-ts/` | TypeScript orchestration, contracts, and the mvt-runner wrapper. |
| `packages-py/` | Python analysis, database migration tooling, and extractor/reporting code. |
| `extractors/` | Project-specific extractor entrypoints and compatibility shims. |
| `reporting/` | Human-readable report generation. |
| `infra/` | Local infrastructure definition for Postgres. |
| `docs/` | Design and architecture rationale. |

The important point is that the runtime architecture is still a
shared-contract ETL pipeline: each extractor normalizes its own domain into a
common record schema, writes to Postgres, and the reporting layer renders a
single honest view over the results. The current repo split reflects the real
project structure, not an old one-folder mental model.

## Current architecture in plain English

The design remains intentionally simple:

1. `packages-ts/orchestrator/main-orchestrator` creates a `pipeline_runs` row
   and per-stage status rows for each backup.
2. Extractors are invoked as isolated subprocesses. A failure in one stage is
   recorded and isolated instead of aborting the rest of the run.
3. `packages-py/reporting/generate_report.py` runs last and renders a completeness section
   before any domain findings, so failed or skipped stages remain visible in
   the report.
4. The underlying record contract is shared across extractors and the rest of
   the pipeline, while each extractor remains free to choose its own language
   and parsing strategy.

This is the same conceptual model described in [`docs/architecture.md`](docs/architecture.md); the main fix here is that the docs now point at the actual code paths in this repo.

## Repository-specific notes

The current codebase still uses a few older names in narrative docs, but the
live sources are organized like this:

- The orchestrator entrypoint is in `packages-ts/orchestrator/main-orchestrator`.
- The mvt-ios helper is in `packages-ts/orchestrator/mvt-runner`.
- The Python migrations live in `packages-py/db/migrate.py`.
- Shared contracts live under `packages-ts/contracts` and `packages-py/contracts`.
- The desktop app is `epoch/`, not a root-level `app/` or `ui/` package.

The repo is intentionally mixed by language and runtime; the contract is the
stable boundary, not a shared library or monolithic process.

## Local setup

```bash
# install the workspace dependencies
pnpm install

# start Postgres for local forensic runs
cd infra && docker compose up -d
cd ..

# apply migrations if needed
python3 packages-py/db/migrate.py --db-url postgresql://localhost:5432/forensics

# build the mvt-ios helper used to decrypt and prepare backups
cd packages-ts/orchestrator/mvt-runner && npm install && npm run build
cd ../../..
```

## Running a backup through the analysis pipeline

```bash
# from the repo root
cd packages-ts/orchestrator/mvt-runner
node dist/main.js --source ~/iPhone-Backups --workspace ~/mvt-workspace

cd ../main-orchestrator
DATABASE_URL=postgresql://localhost:5432/forensics \
  pnpm run investigate --workspace ~/mvt-workspace
```

This runs the full pipeline against every decrypted backup in
`~/mvt-workspace/decrypted/*`, recording stage status and continuing past
failed stages instead of aborting the rest of the run.

You can also target specific backup directories directly:

```bash
DATABASE_URL=postgresql://localhost:5432/forensics \
  pnpm run investigate /path/to/decrypted/backup-a /path/to/decrypted/backup-b
```

## Adding a new extractor

See [`packages-ts/contracts/EXTRACTOR_CONTRACT.md`](packages-ts/contracts/EXTRACTOR_CONTRACT.md) for the process-level contract.
The short version is still the same: satisfy the CLI contract, validate your
normalized rows against the shared schema, record your stage status, and keep
failure isolated rather than fatal.

## Status

The repo is still evolving; some extractor domains are intentionally not yet
wired in. The current project history is consistent with the architecture in
[`docs/architecture.md`](docs/architecture.md), but the actual living layout is
best understood by the package map above rather than the older monolithic
folder names.
