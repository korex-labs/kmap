"""Project partitioning for generated LikeC4 model files."""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ProjectModelPartition:
    project: Dict[str, Any]
    systems: List[Dict[str, Any]]
    comment: str


def project_model_partitions(
    systems: List[Dict[str, Any]],
    projects: List[Dict[str, Any]],
) -> List[ProjectModelPartition]:
    partitions = configured_project_model_partitions(systems, projects)
    partitions.extend(orphan_project_model_partitions(systems, projects))
    return partitions


def configured_project_model_partitions(
    systems: List[Dict[str, Any]],
    projects: List[Dict[str, Any]],
) -> List[ProjectModelPartition]:
    partitions: List[ProjectModelPartition] = []
    for project in sorted(projects, key=lambda item: item.get("name") or item.get("id") or ""):
        project_id = project.get("id") or ""
        project_systems = project_model_systems(systems, project_id)
        if not project_systems:
            continue
        partitions.append(
            ProjectModelPartition(
                project=project,
                systems=project_systems,
                comment=f"Generated model for project {project.get('name') or project_id} by kmap. Do not edit manually.",
            )
        )
    return partitions


def orphan_project_model_partitions(
    systems: List[Dict[str, Any]],
    projects: List[Dict[str, Any]],
) -> List[ProjectModelPartition]:
    project_by_id = {project.get("id"): project for project in projects}
    known_project_ids = set(project_by_id)
    return [
        ProjectModelPartition(
            project=project_by_id.get(project_id) or {"id": project_id, "name": project_id},
            systems=project_systems,
            comment=f"Generated model for project {project_id} by kmap. Do not edit manually.",
        )
        for project_id, project_systems in sorted(orphan_model_systems_by_project(systems, known_project_ids).items())
    ]


def external_model_systems(systems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [system for system in systems if is_external_system(system)]


def project_model_systems(systems: List[Dict[str, Any]], project_id: str) -> List[Dict[str, Any]]:
    return [system for system in systems if system.get("project_id") == project_id and not is_external_system(system)]


def orphan_model_systems_by_project(
    systems: List[Dict[str, Any]],
    known_project_ids: set,
) -> Dict[str, List[Dict[str, Any]]]:
    orphan_systems_by_project: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for system in systems:
        project_id = system.get("project_id") or ""
        if project_id and project_id not in known_project_ids and not is_external_system(system):
            orphan_systems_by_project[project_id].append(system)
    return orphan_systems_by_project


def is_external_system(system: Dict[str, Any]) -> bool:
    return not system.get("project_id") or "External" in (system.get("tags") or [])


__all__ = [
    "ProjectModelPartition",
    "configured_project_model_partitions",
    "external_model_systems",
    "is_external_system",
    "orphan_model_systems_by_project",
    "orphan_project_model_partitions",
    "project_model_partitions",
    "project_model_systems",
]
