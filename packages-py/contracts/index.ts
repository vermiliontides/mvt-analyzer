/**
 * Public entry point for `@verichron/contracts`.
 *
 * `epoch` and `@verichron/db-writer` both declare a dependency on this
 * package, and its package.json has always pointed `main` at `dist/index.js` --
 * but no `index.ts` existed, so the package resolved to nothing. Consumers
 * worked around it by deep-importing the source file across package
 * boundaries (`import { ... } from '../../contracts/normalizedRecord'`), which
 * bypasses the package's own build output and breaks the moment either package
 * moves. This barrel is what those imports were reaching for.
 *
 * TypeScript consumers validate with the Zod model exported here. The
 * canonical JSON Schema (`contracts/normalized-record.schema.json`) is
 * deliberately not re-exported through TypeScript: importing JSON from outside
 * this package's rootDir fights `composite`/`outDir` emit, and Zod already
 * gives TS callers the same guarantee. Python callers that want raw JSON
 * Schema validation use `packages-py/contracts_adapter`.
 */
 
export { NormalizedRecord, SourceType } from "./normalizedRecord.js";
 