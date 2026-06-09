"""Validation helpers for kmap tool-level config."""

import re
from typing import Any

VIEW_CONFIG_KEYS = {"likec4_image", "structurizr_args", "structurizr_image"}
TOOL_CONFIG_KEYS = {"inventory", "recommendations", "view"}
INVENTORY_CONFIG_KEYS = {"namespace_heuristics", "repositories", "storage_type_labels"}
INVENTORY_NAMESPACE_HEURISTIC_KEYS = {"project_id_suffix", "stage_tokens", "strip_project_id_suffix"}
INVENTORY_REPOSITORIES_KEYS = {"base_url", "cache_file", "enabled", "provider", "token_env", "url"}
PROJECT_ID_SUFFIX_KEYS = {"enabled", "pattern", "repository_format"}
STORAGE_TYPE_LABEL_KEYS = {"label", "match"}
RECOMMENDATIONS_CONFIG_KEYS = {"resources"}
RECOMMENDATION_RESOURCE_KEYS = {"optional", "required"}
STRING_TYPES = (str, int, float)


def validate_tool_config(config: dict[str, Any]) -> list[str]:
    errors = unknown_key_errors(config, TOOL_CONFIG_KEYS, "")
    errors.extend(validate_inventory_config(config.get("inventory")))
    errors.extend(validate_recommendations_config(config.get("recommendations")))
    view = config.get("view")
    if view is None:
        return errors
    if not isinstance(view, dict):
        errors.append("view: expected mapping")
        return errors
    errors.extend(unknown_key_errors(view, VIEW_CONFIG_KEYS, "view"))
    errors.extend(string_field_errors(view, VIEW_CONFIG_KEYS, "view"))
    return errors


def unknown_key_errors(config: dict[str, Any], known_keys: set[str], path: str, label: str = "") -> list[str]:
    prefix = f"{path}." if path else ""
    key_label = label or (f"{path} config key" if path else "kmap config key")
    return [f"{prefix}{key}: unknown {key_label}" for key in sorted(set(config) - known_keys)]


def string_field_errors(config: dict[str, Any], keys: set[str] | tuple[str, ...], path: str) -> list[str]:
    return [
        f"{path}.{key}: expected string"
        for key in sorted(keys)
        if config.get(key) is not None and not isinstance(config.get(key), STRING_TYPES)
    ]


def validate_inventory_config(inventory: Any) -> list[str]:
    if inventory is None:
        return []
    if not isinstance(inventory, dict):
        return ["inventory: expected mapping"]
    errors = unknown_key_errors(inventory, INVENTORY_CONFIG_KEYS, "inventory")
    errors.extend(validate_inventory_repositories_config(inventory.get("repositories")))
    errors.extend(validate_storage_type_labels_config(inventory.get("storage_type_labels")))
    heuristics = inventory.get("namespace_heuristics")
    if heuristics is None:
        return errors
    if not isinstance(heuristics, dict):
        errors.append("inventory.namespace_heuristics: expected mapping")
        return errors
    errors.extend(
        unknown_key_errors(
            heuristics,
            INVENTORY_NAMESPACE_HEURISTIC_KEYS,
            "inventory.namespace_heuristics",
            "namespace heuristics config key",
        )
    )

    project_id_suffix = heuristics.get("project_id_suffix")
    if project_id_suffix is not None:
        errors.extend(validate_project_id_suffix_config(project_id_suffix))
    stage_tokens = heuristics.get("stage_tokens")
    if stage_tokens is not None and not string_list(stage_tokens):
        errors.append("inventory.namespace_heuristics.stage_tokens: expected list of strings")
    strip_suffix = heuristics.get("strip_project_id_suffix")
    if strip_suffix is not None and not isinstance(strip_suffix, bool):
        errors.append("inventory.namespace_heuristics.strip_project_id_suffix: expected boolean")
    return errors


def validate_inventory_repositories_config(config: Any) -> list[str]:
    if config is None:
        return []
    if not isinstance(config, dict):
        return ["inventory.repositories: expected mapping"]
    path = "inventory.repositories"
    errors = unknown_key_errors(config, INVENTORY_REPOSITORIES_KEYS, path, "repositories config key")
    if config.get("enabled") is not None and not isinstance(config.get("enabled"), bool):
        errors.append(f"{path}.enabled: expected boolean")
    errors.extend(string_field_errors(config, ("base_url", "cache_file", "provider", "token_env", "url"), path))
    return errors


def validate_storage_type_labels_config(config: Any) -> list[str]:
    if config is None:
        return []
    if not isinstance(config, list):
        return ["inventory.storage_type_labels: expected list of mappings"]
    errors = []
    for index, item in enumerate(config):
        path = f"inventory.storage_type_labels[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path}: expected mapping")
            continue
        errors.extend(unknown_key_errors(item, STORAGE_TYPE_LABEL_KEYS, path, "storage type label key"))
        errors.extend(
            f"{path}.{key}: expected string"
            for key in ("match", "label")
            if item.get(key) is None or not isinstance(item.get(key), STRING_TYPES)
        )
        pattern = item.get("match")
        if isinstance(pattern, STRING_TYPES):
            try:
                re.compile(str(pattern))
            except re.error as exc:
                errors.append(f"{path}.match: invalid regex: {exc}")
    return errors


def validate_project_id_suffix_config(config: Any) -> list[str]:
    if not isinstance(config, dict):
        return ["inventory.namespace_heuristics.project_id_suffix: expected mapping"]
    path = "inventory.namespace_heuristics.project_id_suffix"
    errors = unknown_key_errors(config, PROJECT_ID_SUFFIX_KEYS, path, "project id suffix config key")
    if config.get("enabled") is not None and not isinstance(config.get("enabled"), bool):
        errors.append("inventory.namespace_heuristics.project_id_suffix.enabled: expected boolean")
    errors.extend(string_field_errors(config, ("pattern", "repository_format"), path))
    return errors


def validate_recommendations_config(recommendations: Any) -> list[str]:
    if recommendations is None:
        return []
    if not isinstance(recommendations, dict):
        return ["recommendations: expected mapping"]

    errors = unknown_key_errors(recommendations, RECOMMENDATIONS_CONFIG_KEYS, "recommendations")
    resources = recommendations.get("resources")
    if resources is None:
        return errors
    if not isinstance(resources, dict):
        errors.append("recommendations.resources: expected mapping")
        return errors
    errors.extend(
        unknown_key_errors(
            resources, RECOMMENDATION_RESOURCE_KEYS, "recommendations.resources", "resources recommendation key"
        )
    )
    errors.extend(
        f"recommendations.resources.{key}: expected list of strings"
        for key in sorted(RECOMMENDATION_RESOURCE_KEYS)
        if resources.get(key) is not None and not string_list(resources.get(key))
    )
    return errors


def string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, STRING_TYPES) for item in value)


__all__ = [
    "RECOMMENDATION_RESOURCE_KEYS",
    "STRING_TYPES",
    "TOOL_CONFIG_KEYS",
    "VIEW_CONFIG_KEYS",
    "string_list",
    "validate_inventory_config",
    "validate_inventory_repositories_config",
    "validate_recommendations_config",
    "validate_storage_type_labels_config",
    "validate_tool_config",
]
