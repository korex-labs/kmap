"""System lookup helpers for LikeC4 README tables."""

from typing import Any, Dict, List


def system_indexes(
    systems: List[Dict[str, Any]], containers: List[Dict[str, Any]]
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    systems_by_id = {system.get("id"): system for system in systems}
    containers_by_id = {container.get("id"): container for container in containers}
    return systems_by_id, containers_by_id


def system_for_element(
    element_id: str,
    systems_by_id: Dict[str, Dict[str, Any]],
    containers_by_id: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    if element_id in systems_by_id:
        return systems_by_id[element_id]
    container = containers_by_id.get(element_id) or {}
    return systems_by_id.get(container.get("system_id")) or {}


def split_systems(systems: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    external_systems = [system for system in systems if "External" in (system.get("tags") or [])]
    internal_systems = [system for system in systems if "External" not in (system.get("tags") or [])]
    return internal_systems, external_systems


def generic_system_names(systems: List[Dict[str, Any]]) -> List[str]:
    return [
        system.get("title") or system.get("name") or system.get("id")
        for system in systems
        if (system.get("element_type") or "system") == "system"
    ]


__all__ = ["generic_system_names", "split_systems", "system_for_element", "system_indexes"]
