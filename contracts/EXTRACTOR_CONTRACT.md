# Extractor Contract

This is the interface a new extractor must satisfy to be wired into the
orchestrator. It's deliberately thin — a subprocess contract, not a shared
library — because extractors are polyglot on purpose (see
`/docs/architecture.md`). Satisfying this contract is what makes adding a
new source additive instead of a change to
`packages-ts/orchestrator/main-orchestrator/main.ts`.

This top-level copy is the canonical contract location for the repository; runtime adapters in `packages-ts/contracts-adapter` and
`packages-py/contracts_adapter` expose language-native helpers.

## Key points (summary)

- Validate every row against `contracts/normalized-record.schema.json` before writing to the database.
- Put domain-specific shapes inside `fields` and document them in the extractor's README.
- Keep raw payloads in `ingested_files.raw_payload`.
- Add new `source_type` enum values in the schema (and adapters) in the same commit as the extractor that uses them.

(See the existing `packages-ts/contracts/EXTRACTOR_CONTRACT.md` for the full original reference text; this file is a convenience pointer for contributors.)
