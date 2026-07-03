"""Shared persisted inventory schema-version checks."""

from typing import Any


def require_schema_version(payload: dict[str, Any], *, expected: int, source: object, kind: str) -> None:
    try:
        schema_version = int(payload.get("schema_version") or 0)
    except (TypeError, ValueError):
        schema_version = 0
    if schema_version != expected:
        raise SystemExit(f"Unsupported {kind} schema version in {source}")


__all__ = ["require_schema_version"]
