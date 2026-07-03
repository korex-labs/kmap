"""Configured inventory matching for full discovery."""

from dataclasses import replace
from pathlib import Path

from .heuristics import inferred_inventory_row, namespace_heuristics, namespace_project_id
from .namespaces import InventoryRow, collect_inventory_rows


def config_inventory_by_namespace(config_dir: Path) -> dict[str, InventoryRow]:
    if not config_dir.exists():
        return {}
    return {row.namespace: row for row in collect_inventory_rows(config_dir)}


def discovered_namespace_rows(
    cluster: str,
    namespaces: list[str],
    inventory_index: dict[str, InventoryRow],
    tool_config: dict | None = None,
    *,
    labels_by_namespace: dict[str, dict[str, str]] | None = None,
) -> list[InventoryRow]:
    tool_config = tool_config or {}
    labels_by_namespace = labels_by_namespace or {}
    repository_index = config_inventory_by_repository_id(inventory_index, tool_config)
    return [
        replace(
            inferred_inventory_row(
                cluster=cluster,
                namespace=namespace,
                configured=inventory_index.get(namespace)
                or configured_inventory_for_repository_id(namespace, repository_index, tool_config),
                tool_config=tool_config,
            ),
            labels=labels_by_namespace.get(namespace, {}),
        )
        for namespace in namespaces
    ]


def config_inventory_by_repository_id(
    inventory_index: dict[str, InventoryRow],
    tool_config: dict | None = None,
) -> dict[str, InventoryRow]:
    heuristics = namespace_heuristics(tool_config or {})
    repository_index: dict[str, InventoryRow] = {}
    for row in inventory_index.values():
        project_id = namespace_project_id(row.namespace, heuristics)
        if not project_id or not row.repository:
            continue
        repository_index.setdefault(project_id, row)
    return repository_index


def configured_inventory_for_repository_id(
    namespace: str,
    repository_index: dict[str, InventoryRow],
    tool_config: dict | None = None,
) -> InventoryRow | None:
    project_id = namespace_project_id(namespace, namespace_heuristics(tool_config or {}))
    if not project_id:
        return None
    configured = repository_index.get(project_id)
    if not configured:
        return None
    return replace(configured, namespace=namespace, stage="")


__all__ = [
    "config_inventory_by_namespace",
    "config_inventory_by_repository_id",
    "configured_inventory_for_repository_id",
    "discovered_namespace_rows",
]
