#!/usr/bin/env bash
set -euo pipefail

# Bootstrap developer environment for the repo.
# - Creates repo-local .venv (if missing) and installs Python requirements
# - Runs pnpm install for workspace packages
# - Syncs and updates git submodules
# Usage: ./scripts/bootstrap-dev.sh

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "[bootstrap] Repo root: $REPO_ROOT"

# 1) Python venv and pip deps
if [ ! -d ".venv" ]; then
  echo "[bootstrap] Creating Python venv at .venv"
  python3 -m venv .venv
else
  echo "[bootstrap] .venv already exists — reusing"
fi

# Activate and install
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --upgrade pip
if [ -f "packages-py/requirements.txt" ]; then
  echo "[bootstrap] Installing Python requirements"
  python -m pip install -r packages-py/requirements.txt
else
  echo "[bootstrap] No Python requirements found at packages-py/requirements.txt"
fi

# 2) Node workspace install
if command -v pnpm >/dev/null 2>&1; then
  echo "[bootstrap] Installing pnpm workspace dependencies"
  pnpm install
else
  echo "[bootstrap] pnpm not found — please install pnpm and re-run the script"
  exit 1
fi

# 3) Sync and initialize submodules
if [ -f .gitmodules ]; then
  echo "[bootstrap] Syncing and initializing git submodules"
  git submodule sync --recursive
  git submodule update --init --recursive
else
  echo "[bootstrap] No .gitmodules file found — skipping submodule init"
fi

echo "[bootstrap] Bootstrap complete. Next steps:"
echo "  - Start Postgres (infra/docker-compose.yml) and run migrations: python3 packages-py/db/migrate.py --db-url <DB_URL>"
echo "  - Optionally build TypeScript packages: pnpm --recursive build"
echo "  - Run smoke checks or orchestrator as needed."

exit 0
