"""External mapping config validation."""

import re
from typing import Any, Dict, List

from .metadata import clean_metadata_string

LIKEC4_EXTERNAL_ELEMENT_TYPES = {
    "system",
    "API",
    "External_API",
    "External_Endpoint",
    "Mobile_App",
    "VueJS_App",
    "GoLang_App",
    "PHP_App",
    "container",
    "bucket",
    "AWS_S3_Bucket",
    "ServersCom_Object_Storage",
    "MySQL_DB",
    "PgSQL_DB",
    "Mongo_DB",
    "Redis_DB",
    "ClickHouse_DB",
    "Vault",
    "Website",
    "Kafka",
    "NATS",
    "Hydra_Consent",
}


def validate_element_type(path: str, item: Dict[str, Any], errors: List[str]) -> None:
    element_type = clean_metadata_string(item.get("element_type") or item.get("likec4_type"))
    if element_type and element_type not in LIKEC4_EXTERNAL_ELEMENT_TYPES:
        errors.append(f"{path}.element_type: unknown element type {element_type!r}")


def validate_external_mapping_regexes(mapping_path: str, regexes: Any, errors: List[str]) -> None:
    if regexes and not isinstance(regexes, list):
        errors.append(f"{mapping_path}.match_regex: expected list")
        return
    if not isinstance(regexes, list):
        return

    for regex_index, raw_regex in enumerate(regexes):
        try:
            re.compile(str(raw_regex))
        except re.error as exc:
            errors.append(f"{mapping_path}.match_regex[{regex_index}]: invalid regex: {exc}")


def validate_external_mapping_item(mapping_path: str, item: Any, errors: List[str]) -> None:
    if not isinstance(item, dict):
        errors.append(f"{mapping_path}: expected mapping")
        return
    if not clean_metadata_string(item.get("name")):
        errors.append(f"{mapping_path}.name: required")
    validate_element_type(mapping_path, item, errors)
    validate_external_mapping_match_fields(mapping_path, item, errors)


def validate_external_mapping_match_fields(mapping_path: str, item: Dict[str, Any], errors: List[str]) -> None:
    matches = item.get("match") or []
    regexes = item.get("match_regex") or []
    if not matches and not regexes:
        errors.append(f"{mapping_path}: at least one of match or match_regex is required")
    if matches and not isinstance(matches, list):
        errors.append(f"{mapping_path}.match: expected list")
    validate_external_mapping_regexes(mapping_path, regexes, errors)


def validate_external_mappings(config: Dict[str, Any], errors: List[str]) -> None:
    raw_mappings = config.get("external_mappings") or []
    if raw_mappings and not isinstance(raw_mappings, list):
        errors.append("external_mappings: expected list")
    for index, item in enumerate(raw_mappings if isinstance(raw_mappings, list) else []):
        validate_external_mapping_item(f"external_mappings[{index}]", item, errors)


__all__ = [
    "LIKEC4_EXTERNAL_ELEMENT_TYPES",
    "validate_element_type",
    "validate_external_mapping_item",
    "validate_external_mapping_match_fields",
    "validate_external_mapping_regexes",
    "validate_external_mappings",
]
