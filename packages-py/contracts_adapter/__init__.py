"""Small adapter module that exposes the canonical JSON schema to Python runtimes.

Usage:
    from packages_py.contracts_adapter import load_schema, validate

    schema = load_schema()
    validate(record, schema)  # requires jsonschema; otherwise raises informative error

This adapter intentionally keeps validation optional and fails with a clear
message if jsonschema is not installed. That keeps the repo free of hard
runtime deps while guiding contributors to run `pip install jsonschema` in
environments that need validation.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict

_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "contracts", "normalized-record.schema.json")

def load_schema() -> Dict[str, Any]:
    """Return the canonical normalized-record JSON schema as a Python dict."""
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate(instance: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate an instance against the canonical schema.

    If the `jsonschema` package is not installed, raise ImportError with a
    helpful message describing how to install it.
    """
    try:
        import jsonschema
    except Exception as e:  # pragma: no cover - helpful runtime message
        raise ImportError(
            "jsonschema is required to validate records locally. Install with: pip install jsonschema"
        ) from e

    jsonschema.validate(instance=instance, schema=schema)
