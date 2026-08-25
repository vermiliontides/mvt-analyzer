"""
Shared pytest configuration for the Python packages.

Import path setup lives here, in one place, rather than as a `sys.path.insert`
prologue repeated at the top of every test module. The repository directory is
named `packages-py` (hyphen), which is not a legal Python identifier, so it
cannot be imported as a package and the shims are currently unavoidable — but
they should exist once, not per-file. Collapsing them here also means the
eventual fix (rename to `packages_py`, add a `pyproject.toml`, `pip install
-e .`) touches this file and deletes it, instead of touching every module that
grew its own copy.

pytest imports conftest.py before collecting any test module in this directory
tree, so anything registered below is in place for all of them.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PACKAGES_PY = Path(__file__).resolve().parent

# Order matters: `extractors` must precede `contracts` because `db_writer` and
# `etl_run` live under extractors while `normalized_record` lives under
# contracts, and both are imported by bare module name.
for _path in (
    _PACKAGES_PY,
    _PACKAGES_PY / "extractors",
    _PACKAGES_PY / "contracts",
    _PACKAGES_PY / "analysis",
):
    _resolved = str(_path)
    if _path.is_dir() and _resolved not in sys.path:
        sys.path.insert(0, _resolved)
