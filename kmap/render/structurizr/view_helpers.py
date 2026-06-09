"""Structurizr view planning helpers."""

from collections import defaultdict
from typing import Any, Dict, List, Set

from ...identifiers import ident


def view_key(prefix: str, value: str) -> str:
    return ident(f"{prefix}_{value or 'view'}")


def deployment_view_key(product_name: str, env: str) -> str:
    return view_key("deployment", f"{product_name}_{env}")


def internal_systems(architecture: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [system for system in architecture.get("systems") or [] if system.get("project_id")]


def internal_project_views(architecture: Dict[str, Any]) -> List[Dict[str, Any]]:
    projects_by_id = {project.get("id"): project for project in architecture.get("projects") or []}
    seen: set[str] = set()
    views: List[Dict[str, Any]] = []
    for system in internal_systems(architecture):
        project_id = system.get("project_id") or ""
        if not project_id or project_id in seen:
            continue
        project = projects_by_id.get(project_id) or {"id": project_id, "name": project_id, "title": project_id}
        views.append(
            {
                "id": project_id,
                "title": project.get("title") or project.get("name") or project_id,
                "system_ids": [
                    item.get("id") or ""
                    for item in internal_systems(architecture)
                    if item.get("project_id") == project_id
                ],
            }
        )
        seen.add(project_id)
    return views


def connected_system_ids(
    system_id: str,
    container_ids: Set[str],
    containers_by_id: Dict[str, Dict[str, Any]],
    relationships: List[Dict[str, Any]],
) -> Set[str]:
    connected: Set[str] = set()
    ids = set(container_ids)
    ids.add(system_id)
    for relationship in relationships:
        source_id = relationship.get("source_id") or ""
        target_id = relationship.get("target_id") or ""
        if source_id in ids:
            target = containers_by_id.get(target_id)
            connected.add((target or {}).get("system_id") or target_id)
        if target_id in ids:
            source = containers_by_id.get(source_id)
            connected.add((source or {}).get("system_id") or source_id)
    connected.discard(system_id)
    connected.discard("")
    return connected


def connected_element_ids(
    system_id: str,
    container_ids: Set[str],
    containers_by_id: Dict[str, Dict[str, Any]],
    relationships: List[Dict[str, Any]],
) -> Set[str]:
    connected: Set[str] = set()
    ids = set(container_ids)
    ids.add(system_id)
    for relationship in relationships:
        source_id = relationship.get("source_id") or ""
        target_id = relationship.get("target_id") or ""
        if source_id in ids:
            connected.add(target_id)
        if target_id in ids:
            connected.add(source_id)

    normalized: Set[str] = set()
    for element_id in connected:
        if not element_id or element_id in ids:
            continue
        container = containers_by_id.get(element_id)
        if container and container.get("system_id") == system_id:
            continue
        normalized.add(element_id)
    return normalized


def containers_by_system(containers: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for container in containers:
        grouped[container.get("system_id") or ""].append(container)
    return grouped


def system_project_ids(systems: List[Dict[str, Any]]) -> Dict[str, str]:
    return {system.get("id") or "": system.get("project_id") or "" for system in systems}


def project_view_connection_ids(
    system_ids: List[str],
    container_ids: Set[str],
    containers_by_id: Dict[str, Dict[str, Any]],
    relationships: List[Dict[str, Any]],
) -> tuple[Set[str], Set[str]]:
    project_connected_system_ids: Set[str] = set()
    project_connected_element_ids: Set[str] = set()
    for system_id in system_ids:
        project_connected_system_ids.update(
            connected_system_ids(system_id, container_ids, containers_by_id, relationships)
        )
        project_connected_element_ids.update(
            connected_element_ids(system_id, container_ids, containers_by_id, relationships)
        )
    return project_connected_system_ids, project_connected_element_ids


__all__ = [
    "connected_element_ids",
    "connected_system_ids",
    "containers_by_system",
    "deployment_view_key",
    "internal_project_views",
    "internal_systems",
    "project_view_connection_ids",
    "system_project_ids",
    "view_key",
]
