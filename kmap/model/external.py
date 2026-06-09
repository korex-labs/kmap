"""Helpers for generated external dependency model elements."""

from typing import Any, Dict

from ..config import clean_metadata_string
from ..external.mappings import normalized_likec4_external_type
from ..identifiers import architecture_id_part
from ..naming import endpoint_label

EXTERNAL_TITLE_ACRONYMS = {"API", "URL", "URI", "DSN", "DNS", "VM", "PPROF", "HTTP", "HTTPS", "TCP", "GRPC", "ID"}
EXTERNAL_TITLE_REPLACEMENTS = {"ADDR": "Address"}


def external_identity_name(
    dep_key: str, source_var: str, mapping: Dict[str, Any] | None, aggregate_mapping: bool
) -> str:
    if aggregate_mapping and mapping:
        return clean_metadata_string(mapping.get("name")) or "external"
    return clean_metadata_string(source_var) or endpoint_label(dep_key) or dep_key or "external"


def external_type_name(
    external_name: str,
    dep_key: str,
    mapping: Dict[str, Any] | None,
    aggregate_mapping: bool,
    source_var: str,
) -> str:
    effective_mapping = mapping if aggregate_mapping else None
    configured_type = clean_metadata_string((effective_mapping or {}).get("element_type"))
    tag = clean_metadata_string((effective_mapping or {}).get("tag")) or "External System"
    detection_name = " ".join(part for part in (external_name, dep_key) if part)
    element_type = normalized_likec4_external_type(detection_name, tag, configured_type)
    if source_var and not aggregate_mapping and element_type in {"system", "Website"}:
        return "External_API"
    return element_type


def external_variable_title(source_var: str) -> str:
    words = [_external_title_word(part) for part in architecture_id_part(source_var).split("_")]
    return " ".join(words) or clean_metadata_string(source_var)


def _external_title_word(part: str) -> str:
    raw = part.upper()
    if raw in EXTERNAL_TITLE_ACRONYMS:
        return raw
    if raw in EXTERNAL_TITLE_REPLACEMENTS:
        return EXTERNAL_TITLE_REPLACEMENTS[raw]
    return part.capitalize()


def append_metadata_value(system: Dict[str, Any], key: str, value: str) -> None:
    cleaned = clean_metadata_string(value)
    if not cleaned:
        return
    metadata = system.setdefault("metadata", {})
    _append_metadata_list_value(metadata, key, cleaned)


def _append_metadata_list_value(metadata: Dict[str, Any], key: str, cleaned: str) -> None:
    values = metadata.setdefault(key, [])
    if isinstance(values, list):
        if cleaned not in values:
            values.append(cleaned)
    elif values != cleaned:
        metadata[key] = [values, cleaned]


__all__ = [
    "append_metadata_value",
    "external_identity_name",
    "external_type_name",
    "external_variable_title",
]
