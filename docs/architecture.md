# Architecture

## The shape: shared-contract ETL, not microservices

Each source domain (crash reports, Safari history, SMS, network usage,
gcloud logs) is parsed by an independent extractor. Extractors don't call
each other and share no runtime — the only thing they share is a **data
contract**: every extractor normalizes its domain into the same envelope
(`contracts/normalized-record.schema.json`) and writes to the same two
Postgres tables (`ingested_files`, `forensic_records`).

This is deliberately an ETL/data-mesh pattern, not a microservices
architecture. There's no service-to-service networking, no queue, no shared
process to keep alive. That's the right amount of infrastructure for a
single-investigator pipeline running against one backup at a time — adding
service orchestration now would be solving a scaling problem this project
doesn't have yet.

## Why polyglot instead of one language/runtime

The existing crash extractor is Python (strong ecosystem for ad hoc
binary/JSON forensic parsing). The orchestrator is TypeScript (already
owns MVT subprocess invocation via `spawn()`). Forcing everything into one
runtime to get "one service" would be a rewrite for its own sake — it buys
nothing before a demo and risks breaking working forensic logic under time
pressure. The contract-based integration means language choice per
extractor is a local decision, not a project-wide one: pick whatever fits
the source format best.

## Two axes, decided independently

**Integration** (how components share data) — via the shared normalized
schema in Postgres. This is the only coupling that exists between
extractors, and it's intentionally the *only* coupling.

**Invocation** (how components get run) — via `orchestrator/main.ts`
spawning each extractor as a subprocess, sequentially, per
`contracts/EXTRACTOR_CONTRACT.md`. Extractors could be parallelized later,
or moved to containers with independent lifecycles, if the pipeline ever
needs to run unattended/continuously (e.g. ingesting a live gcloud log
stream rather than a static backup snapshot) — that's the trigger to
revisit this, not a reason to build it preemptively.

## Failure is isolated, not fatal

A guiding principle for this pipeline: **the user should be able to fix an
error without being punished for having had one.** Concretely:

- Every stage's success/failure is recorded independently in
  `pipeline_stage_status`. One extractor failing does not abort the run —
  the orchestrator continues to the next stage regardless.
- Re-running the orchestrator against the same backup is safe and cheap.
  Extractors dedupe on `file_hash`, so already-ingested files are skipped;
  only the previously-failed (or never-run) work actually happens.
- The report never silently omits a failed domain. It reads
  `pipeline_stage_status` first and states plainly what's present, what
  failed and why, and what was never attempted — matching the same
  "don't overstate what the data shows" principle applied to the crash
  report's original incident-count problem.

## Why row-per-line for high-volume sources (e.g. gcloud logs, syslog)

Considered pre-aggregating at ingest time instead. Chose raw retention
(one normalized row per source line, aggregation as a queryable view on
top) because this pipeline may need to support a conclusion under
scrutiny, not just present a summary — every row traces back to an exact
source line via `raw_ref` → `ingested_files.raw_payload`. Aggregation
logic can then live in SQL/application code and change without
re-ingesting, whereas aggregating at ingest time bakes a clustering
decision into storage and makes it expensive to reconsider.

## Adding a new source

See `contracts/EXTRACTOR_CONTRACT.md` for the full process-level contract.
Short version: pick a language, satisfy the CLI/exit-code/idempotency
contract, validate every written record against the shared
`NormalizedRecord` schema, document your `fields` sub-shape in your
extractor's own README, register the stage in `orchestrator/main.ts`.
