"""Common metadata value normalization helpers."""

from typing import Any, Dict, List

from ..config import clean_metadata_string


def metadata_bool(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return ""


def metadata_scalar(value: Any) -> str:
    if value is None:
        return ""
    return clean_metadata_string(value)


def metadata_list(values: Any) -> List[str]:
    return [value for value in (clean_metadata_string(item) for item in values or []) if value]


def pod_spec(workload: Dict[str, Any]) -> Dict[str, Any]:
    return ((((workload or {}).get("spec") or {}).get("template") or {}).get("spec")) or {}


def metadata_bool_fields(source: Dict[str, Any], fields: tuple[tuple[str, str], ...]) -> Dict[str, str]:
    out = {}
    for source_key, target_key in fields:
        set_metadata_value(out, target_key, metadata_bool(source.get(source_key)))
    return out


def metadata_scalar_fields(source: Dict[str, Any], fields: tuple[tuple[str, str], ...]) -> Dict[str, str]:
    out = {}
    for source_key, target_key in fields:
        set_metadata_value(out, target_key, metadata_scalar(source.get(source_key)))
    return out


def metadata_bool_or_scalar_fields(source: Dict[str, Any], fields: tuple[tuple[str, str], ...]) -> Dict[str, str]:
    out = {}
    for source_key, target_key in fields:
        set_metadata_value(
            out, target_key, metadata_bool(source.get(source_key)) or metadata_scalar(source.get(source_key))
        )
    return out


def set_metadata_value(target: Dict[str, str], key: str, value: str) -> None:
    if value:
        target[key] = value


__all__ = [
    "metadata_bool",
    "metadata_bool_fields",
    "metadata_bool_or_scalar_fields",
    "metadata_list",
    "metadata_scalar",
    "metadata_scalar_fields",
    "pod_spec",
    "set_metadata_value",
]
