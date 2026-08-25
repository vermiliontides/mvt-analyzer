# Security and Data Handling

Verichron Epoch ingests full iOS device backups. Every run touches browsing
history, message content, account identifiers, per-app network usage, and crash
telemetry belonging to a real person. This file states how that data is
expected to be handled, because the tooling cannot enforce judgment.

## Repository visibility

**This repository must remain private.** It is a forensic analysis pipeline
whose working directories, reports, and databases contain third-party personal
data by design. There is no configuration in which committing pipeline output
to a public repository is acceptable.

## Data that must never be committed

Pipeline output is ignored in `.gitignore` and blocked by
`.githooks/pre-commit`. This covers, at minimum:

| Pattern | What it holds |
| :--- | :--- |
| `*.db`, `*.sqlite`, `*.sqlite3` | Extracted records, checkpoints, normalized findings |
| `correlation_report.md`, `investigation_report.md`, `*_report.md` | Rendered findings: URLs, message senders, app usage |
| `ileapp_raw_output/`, `*_raw_output/` | Raw iLEAPP artifact exports |
| `mvt-workspace/`, `results/`, `decrypted/` | Decrypted backups and `mvt-ios` output |
| `*.plist`, `*.ips` | Device configuration and crash reports |

Install the guard once per clone:

```bash
git config core.hooksPath .githooks
```

`scripts/bootstrap-dev.sh` does this automatically. CI independently fails any
push that tracks a matching path, so the hook is a fast local signal rather
than the only line of defense.

### If forensic data is committed anyway

Treat it as disclosed, not as a mistake to quietly undo.

1. Set the repository private immediately if it is not already.
2. `git rm --cached <path>` and commit.
3. Purge from history:
   `git filter-repo --invert-paths --path <path>` then force-push.
4. Delete every stale branch and tag that still reaches the old commits —
   merged PR branches keep them alive otherwise.
5. Ask GitHub Support to garbage-collect the repository. Commits referenced by
   `refs/pull/*` stay retrievable through the API after a force-push until
   GitHub runs GC server-side; only they can do this.
6. Rotate anything credential-shaped that appeared in the data.
7. If the backup is not your own device, notify the data subject. Step 3 does
   not undo exposure — clones, forks, and API caches are outside your control.

## Credentials

`postgresql://forensics:forensics_dev_only@localhost:5432/forensics` is a
local-development-only default and is intentionally in the source. It is safe
only because it binds to localhost against a throwaway container.

Anything that is not a local dev container must supply `DATABASE_URL`
explicitly. Do not add a non-local default. Do not commit a `.env` — it is
ignored, keep it that way.

## Handling backups on disk

- Keep decrypted backups outside the repository tree. `--workspace` exists so
  that the pipeline never needs to write inside the checkout.
- Backup passwords are read interactively by `mvt-runner` and are never
  persisted. Do not add a `--password` flag or an environment-variable
  fallback.
- Prefer full-disk encryption on any machine holding decrypted backups.
- Delete workspaces when an investigation closes. `ingested_files` retains the
  SHA-256 of every source file, so chain of custody survives deletion of the
  source material.

## Reporting a vulnerability

Open a private security advisory through GitHub, or email the maintainer at the
address on the repository owner's profile. Do not open a public issue, and do
not include real forensic data in a report — synthesize a fixture that
reproduces the problem instead.
