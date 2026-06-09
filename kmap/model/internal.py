"""Internal system model adjustment helpers."""

from collections import defaultdict
from typing import Any, Dict, List

from ..config import LIKEC4_EXTERNAL_ELEMENT_TYPES, clean_metadata_string


def apply_single_system_project_overrides(
    systems_by_id: Dict[str, Dict[str, Any]],
    projects_by_id: Dict[str, Dict[str, Any]],
    project_metadata: Dict[str, Dict[str, Any]],
) -> None:
    for project_id, project_systems in internal_systems_by_project(systems_by_id).items():
        if len(project_systems) != 1:
            continue
        project = projects_by_id.get(project_id) or {}
        apply_project_title_override(project_systems[0], project)
        apply_project_element_type_override(project_systems[0], project, project_metadata)


def internal_systems_by_project(systems_by_id: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    systems_by_project: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for system in systems_by_id.values():
        if system.get("kind") == "internal":
            systems_by_project[system.get("project_id") or ""].append(system)
    return systems_by_project


def apply_project_title_override(system: Dict[str, Any], project: Dict[str, Any]) -> None:
    project_title = clean_metadata_string(project.get("title"))
    if project_title:
        system["title"] = project_title


def apply_project_element_type_override(
    system: Dict[str, Any],
    project: Dict[str, Any],
    project_metadata: Dict[str, Dict[str, Any]],
) -> None:
    project_name = clean_metadata_string(project.get("name"))
    project_meta = project_metadata.get(project_name, {})
    configured_element_type = clean_metadata_string(project_meta.get("element_type"))
    if configured_element_type in LIKEC4_EXTERNAL_ELEMENT_TYPES:
        system["element_type"] = configured_element_type


__all__ = [
    "apply_project_element_type_override",
    "apply_project_title_override",
    "apply_single_system_project_overrides",
    "internal_systems_by_project",
]
