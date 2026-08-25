"""Raw JSON Schema validation against the canonical normalized-record contract.

Two ways to validate a record in Python, and they are not redundant:

- ``packages-py/contracts/normalized_record.py`` (Pydantic) is what extractors
  build records *with*. It validates at construction time and gives you a typed
  object.
- This module validates an already-built ``dict`` against
  ``contracts/normalized-record.schema.json`` itself -- the canonical file, not
  a mirror of it. Use it when you want to confirm the mirrors and the canonical
  schema actually agree about a specific record, which is exactly the check that
  would have caught ``ileapp_record`` being present in Pydantic and Zod but
  absent from the canonical enum.

Usage::

    import sys
    sys.path.insert(0, "packages-py")          # see note on the dash, below
    from contracts_adapter import load_schema, validate

    validate(record, load_schema())

The obvious ``from packages_py.contracts_adapter import ...`` does not work and
never did: the directory is ``packages-py`` with a hyphen, which is not a legal
Python identifier, so it cannot be imported as a package at all. The previous
version of this docstring advertised that import, so anyone following it hit an
ImportError on their first line. Under pytest, ``packages-py/conftest.py``
already puts the right directories on ``sys.path``, so tests just
``from contracts_adapter import ...``.

Validation stays optional: if ``jsonschema`` is not installed this raises an
ImportError explaining how to install it, rather than making the whole repo
depend on it for code paths that never validate.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

#: Canonical schema location, resolved from this file rather than the caller's
#: working directory -- an extractor invoked by the orchestrator does not run
#: from the repo root.
SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "contracts" / "normalized-record.schema.json"


@lru_cache(maxsize=1)
def _cached_schema_text() -> str:
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(
            f"canonical contract schema not found at {SCHEMA_PATH}. "
            "It is expected at <repo-root>/contracts/normalized-record.schema.json; "
            "if this module was vendored out of the repository, pass a schema dict to "
            "validate() explicitly instead."
        )
    return SCHEMA_PATH.read_text(encoding="utf-8")


def load_schema() -> dict[str, Any]:
    """Return the canonical normalized-record JSON schema as a dict.

    Re-parsed per call so a caller mutating the result cannot poison another
    caller's copy; the file read itself is cached.
    """
    return json.loads(_cached_schema_text())


def source_types() -> list[str]:
    """The canonical ``source_type`` enum values.

    Exposed so a caller can assert against the canonical list rather than
    against a language mirror of it.
    """
    return list(load_schema()["properties"]["source_type"]["enum"])


def validate(instance: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    """Validate a record against the canonical schema. Raises on failure.

    ``schema`` defaults to the canonical schema, so the common case is
    ``validate(record)`` and there is no way to accidentally validate against
    a stale copy someone loaded earlier.
    """
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise ImportError(
            "jsonschema is required to validate records against the canonical schema. "
            "Install with: pip install jsonschema  (it is already listed in "
            "packages-py/requirements.txt)"
        ) from exc

    jsonschema.validate(instance=instance, schema=schema if schema is not None else load_schema())


__all__ = ["SCHEMA_PATH", "load_schema", "source_types", "validate"]
