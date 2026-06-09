"""External dependency mapping helpers."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..config import clean_bool, clean_metadata_string
from ..io import load_yaml_file
from .types import generated_external_category, normalized_likec4_external_type


def external_dependency_tag(dep_key: str) -> str:
    return "External System"


def external_mapping_configs(config_path: Optional[str]) -> List[Tuple[str, Dict[str, Any]]]:
    configs: List[Tuple[str, Dict[str, Any]]] = []
    if not config_path:
        return configs
    path = Path(config_path)
    product_config = load_yaml_file(path, {})
    if isinstance(product_config, dict):
        configs.append((str(path), product_config))
    common_path = path.parent / "common" / "external_mappings.yaml"
    common_config = load_yaml_file(common_path, {})
    if isinstance(common_config, dict):
        configs.append((str(common_path), common_config))
    return configs


def external_mapping_items(config_path: Optional[str]) -> List[Tuple[str, Dict[str, Any]]]:
    return [
        (source, item)
        for source, config in external_mapping_configs(config_path)
        for item in config.get("external_mappings") or []
        if isinstance(item, dict)
    ]


def _mapping_name(item: Dict[str, Any]) -> str:
    return clean_metadata_string(item.get("name"))


def _mapping_match_values(item: Dict[str, Any], key: str, *, lowercase: bool = False) -> List[str]:
    values = []
    for raw in item.get(key) or []:
        value = str(raw).strip()
        if not value:
            continue
        values.append(value.lower() if lowercase else value)
    return values


def _mapping_element_type(item: Dict[str, Any]) -> str:
    return clean_metadata_string(item.get("element_type") or item.get("likec4_type"))


def _mapping_tag(item: Dict[str, Any]) -> str:
    return clean_metadata_string(item.get("tag")) or "External System"


def load_external_mappings(config_path: Optional[str]) -> List[Dict[str, Any]]:
    if not config_path:
        return []

    out: List[Dict[str, Any]] = []
    for source, item in external_mapping_items(config_path):
        mapping = external_mapping_entry(source, item)
        if mapping:
            out.append(mapping)
    return out


def load_external_mapping_summaries(config_path: Optional[str]) -> List[Dict[str, Any]]:
    if not config_path:
        return []

    out = []
    for source, item in external_mapping_items(config_path):
        summary = external_mapping_summary_entry(source, item)
        if summary:
            out.append(summary)
    return out


def external_mapping_entry(source: str, item: Dict[str, Any]) -> Dict[str, Any]:
    name = _mapping_name(item)
    if not name:
        return {}
    return {
        "name": name,
        "patterns": _mapping_match_values(item, "match", lowercase=True),
        "regexes": compiled_mapping_regexes(item),
        "tag": _mapping_tag(item),
        "element_type": _mapping_element_type(item),
        "source": source,
    }


def external_mapping_summary_entry(source: str, item: Dict[str, Any]) -> Dict[str, Any]:
    name = _mapping_name(item)
    if not name:
        return {}
    return {
        "name": name,
        "match": _mapping_match_values(item, "match"),
        "match_regex": _mapping_match_values(item, "match_regex"),
        "tag": _mapping_tag(item),
        "element_type": _mapping_element_type(item),
        "source": source,
    }


def compiled_mapping_regexes(item: Dict[str, Any]) -> List[re.Pattern]:
    regexes = []
    for raw in item.get("match_regex") or []:
        try:
            regexes.append(re.compile(str(raw), re.I))
        except re.error:
            continue
    return regexes


def external_mapping_for_key(dep_key: str, mappings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    raw = (dep_key or "").strip().lower()
    if not raw:
        return None
    for mapping in mappings:
        if any(pattern and pattern in raw for pattern in mapping.get("patterns") or []):
            return mapping
        if any(regex.search(raw) for regex in mapping.get("regexes") or []):
            return mapping
    return None


def external_mapping_should_aggregate(mapping: Optional[Dict[str, Any]], dep_key: str = "") -> bool:
    if not mapping:
        return False
    if "aggregate" in mapping:
        return clean_bool(mapping.get("aggregate"), True)

    mapped_name = clean_metadata_string(mapping.get("name"))
    mapped_type = normalized_likec4_external_type(
        mapped_name,
        clean_metadata_string(mapping.get("tag")),
        clean_metadata_string(mapping.get("element_type")),
    )
    return not (mapped_type == "Website" and mapped_name.lower() in {"website", "websites"})


__all__ = [
    "compiled_mapping_regexes",
    "external_dependency_tag",
    "external_mapping_configs",
    "external_mapping_entry",
    "external_mapping_for_key",
    "external_mapping_items",
    "external_mapping_should_aggregate",
    "external_mapping_summary_entry",
    "generated_external_category",
    "load_external_mapping_summaries",
    "load_external_mappings",
    "normalized_likec4_external_type",
]
