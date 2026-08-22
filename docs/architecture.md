# Architecture

## The current project shape

The repository is not a monolithic service. It is a mixed workspace that combines:

- `epoch/` for the desktop client
- `packages-ts/` for TypeScript orchestration, shared contracts, and the
  `mvt-runner` helper
- `packages-py/` for Python-based analysis and extractor/reporting logic
- `extractors/` for project-specific entrypoints and compatibility wrappers
- `infra/` for local infrastructure and Postgres

This is a real-world repo layout, and the architecture reflects it:
components are split by language and concern, but the integration boundary is
still a single shared contract.

## Shared-contract ETL, not a microservice mesh

Each source domain is parsed by an independent extractor. Extractors do not
call each other at runtime and they do not share a live process. They only
share a data contract: a normalized record shape and a Postgres-backed state
model.

That makes the design a shared-contract ETL pipeline rather than a
microservices architecture. There is no queue, no service-to-service network,
and no long-lived process that every source must pass through. The only real
coupling is the schema and the stage contract.

This is the right tradeoff for an investigation workload with a single user,
a single backup at a time, and a strong need for honest failure reporting.

## Why polyglot is intentional

Some sources fit Python better (forensic parsing and ad hoc data work), while
TypeScript owns orchestration and process invocation. The repo intentionally
keeps those concerns separate instead of forcing one runtime to own all
parsing.

The boundary is not "one service". It is "one shared contract". Extractors are
designed to be independent subprocesses that output normalized records and
fail in a recoverable way. That keeps the project flexible without losing the
ability to reason about the data across domains.

## The live orchestration model

The current orchestration entrypoint lives in
`packages-ts/orchestrator/main-orchestrator/main.ts`. It performs the same
high-level role the older docs described:

1. Create a `pipeline_runs` row for each backup.
2. Create one `pipeline_stage_status` row per stage.
3. Invoke each extractor as an isolated subprocess.
4. Record success or failure separately for each stage.
5. Continue to the next stage even when one fails.
6. Run the reporting stage last so the report can be honest about what is and
   is not present.

This is an important design decision: a failed stage should be visible and
recoverable, not fatal to the entire run.

## Failure is isolated, not fatal

The guiding principle is still: the user should not be punished for one bad
stage.

Concretely:

- Each extractor is responsible for catching its own errors and exiting
  non-zero with enough detail to debug.
- The orchestrator records stage status and continues.
- A re-run is safe because extractors dedupe by source hash before writing
  rows.
- The report reads stage status first and explicitly marks missing or failed
  domains instead of silently omitting them.

This matches the original design goal of being honest about uncertainty and
keeping failed work recoverable.

## Where the repo currently differs from older docs

Older documentation still described a monolithic folder layout (`orchestrator/`,
`db/`, `mvt-runner/` at the repo root). That structure no longer matches the
current tree.

The correct references today are:

- `packages-ts/orchestrator/main-orchestrator` for stage orchestration
- `packages-ts/orchestrator/mvt-runner` for the decrypt/workspace wrapper
- `packages-py/db/migrate.py` for migration entrypoints
- `reporting/generate_report.py` for report rendering
- `contracts/` for the canonical shared schema and documentation; see `packages-ts/contracts-adapter` and `packages-py/contracts_adapter` for language-native helpers

The architecture itself remains compatible with the original design intent;
what changed is the package layout and the exact execution paths.

## Adding a new source

The process remains the same:

1. pick the language that fits the source format
2. normalize records to the shared contract
3. validate against the shared schema before writing
4. register the stage in the orchestrator
5. document the extractor's own `fields` shape and failure behavior

The contract is intentionally thin and process-based rather than library-based,
which keeps the integration boundary stable even as the codebase evolves.
