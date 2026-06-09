"""Config validation rules."""

import re
from typing import Any, Dict, List, Tuple

from .metadata import clean_metadata_string
from .options import normalize_system_naming_config
from .projects import PRODUCT_OWNER_ALIASES
from .validation_external import LIKEC4_EXTERNAL_ELEMENT_TYPES, validate_element_type, validate_external_mappings
from .validation_resources import (
    is_string_like,
    path_join,
    validate_namespace_resources,
    validate_product_resources,
    validate_url_like,
)

DISCOVERY_CONFIG_KEYS = {"context", "kubeconfig"}


def _unknown_keys(item: Dict[str, Any], allowed_keys: set[str]) -> List[str]:
    return sorted(set(item.keys()) - allowed_keys)


def _validate_required_fields(config: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    errors.extend(
        f"{field}: required" for field in ("product", "title", "env") if not clean_metadata_string(config.get(field))
    )
    if not any(clean_metadata_string(config.get(alias)) for alias in PRODUCT_OWNER_ALIASES):
        warnings.append("owner_team: recommended")


def _validate_namespace_project(ns_path: str, project: Any, errors: List[str]) -> None:
    if project is not None and not isinstance(project, (dict, str)):
        errors.append(f"{ns_path}.project: expected mapping or string")
    if isinstance(project, dict):
        validate_element_type(f"{ns_path}.project", project, errors)
        tags = project.get("tags")
        if tags is not None and not isinstance(tags, (list, str)):
            errors.append(f"{ns_path}.project.tags: expected list or comma-separated string")


def _validate_discovery_mapping(
    path: str,
    discovery: Any,
    unknown_key_message: str,
    errors: List[str],
    warnings: List[str],
) -> None:
    if discovery is None:
        return
    if not isinstance(discovery, dict):
        errors.append(f"{path}: expected mapping")
        return

    errors.extend(
        f"{path}.{field}: expected string"
        for field in DISCOVERY_CONFIG_KEYS
        if discovery.get(field) is not None and not is_string_like(discovery.get(field))
    )
    warnings.extend(
        unknown_key_message.format(unknown_key=unknown_key)
        for unknown_key in _unknown_keys(discovery, DISCOVERY_CONFIG_KEYS)
    )


def _validate_namespace_mapping_entry(
    namespace: Any,
    entry: Any,
    errors: List[str],
    warnings: List[str],
) -> None:
    ns_path = path_join("namespaces", namespace)
    if not clean_metadata_string(namespace):
        errors.append(f"{ns_path}: namespace name must not be empty")
    if entry is None:
        return
    if isinstance(entry, str):
        if not clean_metadata_string(entry):
            errors.append(f"{ns_path}: project name must not be empty")
        return
    if not isinstance(entry, dict):
        errors.append(f"{ns_path}: expected mapping, string project name, or empty mapping")
        return

    _validate_namespace_project(ns_path, entry.get("project"), errors)
    validate_namespace_resources(ns_path, entry.get("resources"), errors)
    _validate_discovery_mapping(
        f"{ns_path}.discovery",
        entry.get("discovery"),
        f"{ns_path}.discovery.{{unknown_key}}: unknown discovery target key",
        errors,
        warnings,
    )
    warnings.extend(
        f"{ns_path}.{unknown_key}: unknown namespace config key"
        for unknown_key in _unknown_keys(entry, {"project", "resources", "discovery"})
    )


def _validate_namespaces(config: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    raw_namespaces = config.get("namespaces") or config.get("namespace")
    if not raw_namespaces:
        errors.append("namespaces: required and must not be empty")
    elif not isinstance(raw_namespaces, (dict, list)):
        errors.append("namespaces: expected mapping or list")
    elif isinstance(raw_namespaces, list):
        for index, item in enumerate(raw_namespaces):
            if not clean_metadata_string(item):
                errors.append(f"namespaces[{index}]: expected non-empty namespace name")
    elif isinstance(raw_namespaces, dict):
        for namespace, entry in raw_namespaces.items():
            _validate_namespace_mapping_entry(namespace, entry, errors, warnings)


def _validate_projects(config: Dict[str, Any], errors: List[str]) -> None:
    projects = config.get("projects")
    if projects is not None and not isinstance(projects, dict):
        errors.append("projects: expected mapping")
    elif isinstance(projects, dict):
        for project_name, project in projects.items():
            project_path = path_join("projects", project_name)
            if not isinstance(project, dict):
                errors.append(f"{project_path}: expected mapping")
                continue
            validate_element_type(project_path, project, errors)


def _validate_system_naming(config: Dict[str, Any], errors: List[str]) -> None:
    try:
        normalized = normalize_system_naming_config(config)
    except Exception as exc:
        errors.append(f"system_naming: invalid: {exc}")
        return

    for index, rewrite in enumerate(normalized.get("service_aliases", {}).get("rewrites", [])):
        try:
            re.compile(rewrite["match_regex"])
        except re.error as exc:
            errors.append(f"system_naming.service_aliases.rewrites[{index}].match_regex: invalid regex: {exc}")


def _validate_misc_config(config: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    _validate_dependency_hotspots_config(config, errors)
    _validate_render_config(config, errors)

    discovery = config.get("discovery")
    _validate_discovery_mapping(
        "discovery",
        discovery,
        "discovery.{unknown_key}: unknown discovery config key",
        errors,
        warnings,
    )


def _validate_dependency_hotspots_config(config: Dict[str, Any], errors: List[str]) -> None:
    hotspot = config.get("dependency_hotspots")
    if hotspot is not None and not isinstance(hotspot, dict):
        errors.append("dependency_hotspots: expected mapping")


def _validate_render_config(config: Dict[str, Any], errors: List[str]) -> None:
    render = clean_metadata_string(config.get("render"))
    if render and render not in {"structurizr", "likec4", "both"}:
        errors.append("render: expected one of structurizr, likec4, both")


def validate_config_shape(config: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    _validate_required_fields(config, errors, warnings)
    validate_product_resources(config, errors)
    _validate_namespaces(config, errors, warnings)
    _validate_projects(config, errors)
    validate_external_mappings(config, errors)
    _validate_system_naming(config, errors)
    _validate_misc_config(config, errors, warnings)

    return errors, warnings


__all__ = ["LIKEC4_EXTERNAL_ELEMENT_TYPES", "validate_config_shape", "validate_url_like"]
