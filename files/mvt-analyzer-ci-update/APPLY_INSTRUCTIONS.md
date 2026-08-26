# Applying this changeset

Copy every file in this bundle into the repo at the matching relative path,
overwriting what's there. Two new files, the rest are modifications to
existing tracked files:

- `.github/workflows/ci.yml` — new
- `epoch/tsconfig.main.json` — new
- `packages-ts/orchestrator/main-orchestrator/tsconfig.json` — new
- everything else — overwrite in place

## Deletions (not included as downloads — just delete these)

```bash
git rm epoch/main/index.js epoch/src/App.js epoch/src/main.js
git rm packages-ts/orchestrator/mvt-runner/package-lock.json
```

These are stale compiled JS committed alongside their `.ts`/`.tsx` sources
(M4), and a stray npm lockfile inside a pnpm workspace. `.gitignore` already
covers regeneration of the JS files.

## Then

```bash
git add -A
git status   # sanity-check the diff matches what you expect
git commit -m "fix: repair CI-blocking bugs and add CI workflow"
git push
```

## What's in this changeset

| File | Why |
| :--- | :--- |
| `pnpm-workspace.yaml` | Widened glob so `main-orchestrator`/`mvt-runner` actually register as workspace packages (H3) |
| `packages-ts/orchestrator/main-orchestrator/package.json` | Renamed `orchestrator` → `@verichron/main-orchestrator` (avoid ambiguity with `@verichron/orchestrator`); added `build`/`typecheck` scripts; dropped unused `zod` dep |
| `packages-ts/orchestrator/main-orchestrator/tsconfig.json` | New — this package had no tsconfig at all, so it was never typechecked |
| `pnpm-lock.yaml` | Regenerated to match the two changes above |
| `epoch/package.json` | Fixed broken `build` script target; added `build:ci` (skips `electron-builder` packaging); added `"type": "module"` (silences an ESLint warning) |
| `epoch/tsconfig.main.json` | New — this was referenced by `build`/`dev` scripts but never existed, so `epoch`'s build was broken on main |
| `packages-py/extractors/test_extractor_ingest_atomicity.py` | 8 tests were failing — stale tuple-unpacking against extractors that now return `ETLRunResult` objects post-refactor. Fixed all 8 call sites. |
| `.gitignore` | Added `epoch/main-dist/` (the new build output dir) |
| `.github/workflows/ci.yml` | New — 4 jobs: forensic-output guard, contract-mirror sync check, Python tests, TS lint/typecheck/build |

## Verified locally before packaging

All of the following were run from a clean state (no `node_modules`, no
`.venv`, no build output) exactly as CI will run them:

- `pnpm install --frozen-lockfile` — succeeds, registers all 6 workspace packages
- `pnpm lint` — clean
- `pnpm --filter '!@verichron/epoch' --recursive build` — succeeds
- `pnpm --recursive typecheck` — succeeds (must run *after* the build step above,
  since `@verichron/orchestrator` imports `@verichron/contracts`'s emitted
  `dist/index.d.ts`)
- `pnpm --filter @verichron/epoch build:ci` — succeeds
- `python -m pytest packages-py` — 124 passed
- `python3 scripts/sync_contracts.py --check` — passes
- Forensic-output guard script (from `ci.yml`) — clean against current tree

## Not included, needs your input

- **Repo visibility** — couldn't verify from a clone whether the repo is
  actually private now. Worth a manual check.
- **H4 (zod)** — `packages-ts/contracts` is on zod v4; nothing else in the
  workspace pins a version now that `main-orchestrator`'s unused dep is gone.
  Not a live conflict today, but worth a conscious call once something else
  needs zod.
