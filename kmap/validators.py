"""Shared validation message helpers."""

from typing import Any


def unknown_keys(config: dict[str, Any], known_keys: set[str]) -> list[str]:
    return sorted(set(config) - known_keys)


def unknown_key_errors(config: dict[str, Any], known_keys: set[str], path: str, label: str = "") -> list[str]:
    prefix = f"{path}." if path else ""
    key_label = label or (f"{path} config key" if path else "kmap config key")
    return [f"{prefix}{key}: unknown {key_label}" for key in unknown_keys(config, known_keys)]


__all__ = ["unknown_key_errors", "unknown_keys"]
