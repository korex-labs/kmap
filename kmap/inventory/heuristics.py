"""Configurable inventory inference heuristics."""

import re
from dataclasses import replace
from typing import Any

from .namespaces import InventoryRow, infer_stage_from_namespace

DEFAULT_STAGE_TOKENS = ["prod", "stage", "staging", "dev", "review", "sandbox", "test", "qa"]
DEFAULT_REPOSITORY_FORMAT = "repository:{project_id}"
PROJECT_ID_SUFFIX_CONFIG = "project_id_suffix"


def inferred_inventory_row(
    *,
    cluster: str,
    namespace: str,
    configured: InventoryRow | None,
    tool_config: dict[str, Any],
) -> InventoryRow:
    heuristics = namespace_heuristics(tool_config)
    project_id = namespace_project_id(namespace, heuristics)
    stage = inferred_stage(namespace, configured, heuristics)
    repository = inferred_repository(project_id, configured, heuristics)

    if configured:
        return replace(
            configured,
            cluster=cluster,
            namespace=namespace,
            repository=repository,
            stage=stage,
        )

    return InventoryRow(
        cluster=cluster,
        product="",
        product_title="",
        namespace=namespace,
        repository=repository,
        owner_team="",
        stage=stage,
    )


def inferred_stage(namespace: str, configured: InventoryRow | None, heuristics: dict[str, Any]) -> str:
    if configured and configured.stage:
        return configured.stage
    return namespace_stage(namespace, heuristics)


def inferred_repository(project_id: str, configured: InventoryRow | None, heuristics: dict[str, Any]) -> str:
    repository = configured.repository if configured else ""
    if repository:
        return repository
    if project_id:
        return repository_identity(project_id, heuristics)
    return ""


def namespace_heuristics(tool_config: dict[str, Any]) -> dict[str, Any]:
    return ((tool_config or {}).get("inventory") or {}).get("namespace_heuristics") or {}


def project_id_suffix_config(heuristics: dict[str, Any]) -> dict[str, Any]:
    config = heuristics.get(PROJECT_ID_SUFFIX_CONFIG)
    return config if isinstance(config, dict) else {}


def namespace_project_id(namespace: str, heuristics: dict[str, Any]) -> str:
    config = project_id_suffix_config(heuristics)
    if not config.get("enabled", False):
        return ""
    pattern = str(config.get("pattern") or "")
    if not pattern:
        return ""
    match = re.search(pattern, namespace)
    if not match:
        return ""
    if "project_id" in match.groupdict():
        return match.group("project_id")
    return match.group(match.lastindex or 0)


def repository_identity(project_id: str, heuristics: dict[str, Any]) -> str:
    config = project_id_suffix_config(heuristics)
    template = str(config.get("repository_format") or DEFAULT_REPOSITORY_FORMAT)
    return template.format(project_id=project_id)


def namespace_stage(namespace: str, heuristics: dict[str, Any]) -> str:
    tokens = stage_tokens(heuristics)
    parts = namespace_parts(namespace, heuristics)
    for part in reversed(parts):
        if part in tokens:
            return "stage" if part == "staging" else part
    return infer_stage_from_namespace(namespace)


def namespace_product(namespace: str, heuristics: dict[str, Any]) -> str:
    tokens = stage_tokens(heuristics)
    parts = namespace_parts(namespace, heuristics)
    while parts and parts[-1] in tokens:
        parts.pop()
    return "-".join(parts)


def namespace_parts(namespace: str, heuristics: dict[str, Any]) -> list[str]:
    value = namespace.lower().strip("-")
    if heuristics.get("strip_project_id_suffix"):
        value = namespace_without_project_id_suffix(value, heuristics)
    return [part for part in re.split(r"[-_]+", value) if part]


def namespace_without_project_id_suffix(namespace: str, heuristics: dict[str, Any]) -> str:
    project_id = namespace_project_id(namespace, heuristics)
    if project_id and namespace.endswith(f"-{project_id}"):
        return namespace[: -(len(project_id) + 1)]
    return namespace


def stage_tokens(heuristics: dict[str, Any]) -> set[str]:
    return {str(token).lower() for token in heuristics.get("stage_tokens", DEFAULT_STAGE_TOKENS) if str(token)}


__all__ = [
    "DEFAULT_STAGE_TOKENS",
    "inferred_inventory_row",
    "namespace_product",
    "namespace_project_id",
    "namespace_stage",
    "repository_identity",
]
