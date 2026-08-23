# Plan

## Current status
- Repository review is complete and the extractor architecture is consistent with the Postgres-backed ETL contract.
- Non-logging setup and contract work is in progress and centered on making the local extractor workflow reproducible.
- The remaining work is operational and validation focused rather than observability work.

## Completed
- Reviewed repo docs and extractor setup assumptions.
- Documented the extractor setup flow for Postgres + MVT + iLEAPP.
- Verified the schema and migration flow that underpins forensic writes.

## In progress / next
- Finalize the local credentials and dependency setup for Postgres and Python tooling.
- Ensure the iLEAPP submodule and `.venv` are initialized correctly.
- Confirm the MVT runner prerequisites and default `mvt-ios` path.
- Add the TypeScript db-writer pattern for future extractor implementations.
- Add lightweight smoke validation for extractor ingestion.

## Next milestone
- Run the venv setup, initialize the iLEAPP submodule, and verify a minimal extractor run against a local Postgres instance.
- Then move on to logging and infrastructure integration as a separate concern.
