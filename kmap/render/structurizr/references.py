"""Structurizr alias and reference map helpers."""

from typing import Any, Dict, List

from ...identifiers import ident


def structurizr_alias(value: str) -> str:
    return ident(str(value or "").replace(".", "_").replace("-", "_"))


def structurizr_system_alias(system: Dict[str, Any]) -> str:
    return structurizr_alias(system.get("id") or system.get("name") or "system")


def workspace_names(architecture: Dict[str, Any]) -> tuple[str, str]:
    workspace = architecture.get("workspace") or {}
    product = architecture.get("product") or {}
    return (
        workspace.get("org") or "org",
        product.get("name") or workspace.get("product") or "product",
    )


def is_external_endpoint(container: Dict[str, Any], systems_by_id: Dict[str, Dict[str, Any]]) -> bool:
    system = systems_by_id.get(container.get("system_id") or "") or {}
    return not system.get("project_id")


def has_external_endpoint_containers(
    system: Dict[str, Any], containers_by_system: Dict[str, List[Dict[str, Any]]]
) -> bool:
    return bool(containers_by_system.get(system.get("id") or ""))


def structurizr_external_alias(
    system: Dict[str, Any],
    architecture: Dict[str, Any],
    containers_by_system: Dict[str, List[Dict[str, Any]]] | None = None,
) -> str:
    org_name, product_name = workspace_names(architecture)
    title = system.get("title") or system.get("name") or system.get("id") or "external"
    if containers_by_system is not None and has_external_endpoint_containers(system, containers_by_system):
        return structurizr_alias(f"extsys_{org_name}_{product_name}_external_mapped_{title}")
    return structurizr_alias(f"ext_{org_name}_{product_name}_external_{system.get('name') or title}")


def structurizr_external_container_alias(container: Dict[str, Any], architecture: Dict[str, Any]) -> str:
    org_name, product_name = workspace_names(architecture)
    name = container.get("name") or container.get("title") or container.get("id") or "external"
    return structurizr_alias(f"extc_{org_name}_{product_name}_external_{name}")


def structurizr_reference_map(architecture: Dict[str, Any]) -> Dict[str, str]:
    refs: Dict[str, str] = {}
    systems_by_id = {system.get("id"): system for system in architecture.get("systems") or []}
    containers = architecture.get("containers") or []
    containers_by_system = containers_grouped_by_system(containers)
    for system in architecture.get("systems") or []:
        register_system_reference(refs, system, architecture, containers_by_system)
    for container in containers:
        register_container_reference(refs, container, architecture, systems_by_id)
    return refs


def containers_grouped_by_system(containers: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for container in containers:
        grouped.setdefault(container.get("system_id") or "", []).append(container)
    return grouped


def register_system_reference(
    refs: Dict[str, str],
    system: Dict[str, Any],
    architecture: Dict[str, Any],
    containers_by_system: Dict[str, List[Dict[str, Any]]],
) -> None:
    system_id = system.get("id") or ""
    if not system_id:
        return
    if system.get("project_id"):
        refs[system_id] = structurizr_system_alias(system)
        return
    refs[system_id] = structurizr_external_alias(system, architecture, containers_by_system)


def register_container_reference(
    refs: Dict[str, str],
    container: Dict[str, Any],
    architecture: Dict[str, Any],
    systems_by_id: Dict[str, Dict[str, Any]],
) -> None:
    container_id = container.get("id") or ""
    if not container_id:
        return
    if is_external_endpoint(container, systems_by_id):
        refs[container_id] = structurizr_external_container_alias(container, architecture)
        return
    refs[container_id] = structurizr_alias(container_id)


__all__ = [
    "containers_grouped_by_system",
    "has_external_endpoint_containers",
    "is_external_endpoint",
    "register_container_reference",
    "register_system_reference",
    "structurizr_alias",
    "structurizr_external_alias",
    "structurizr_external_container_alias",
    "structurizr_reference_map",
    "structurizr_system_alias",
    "workspace_names",
]
