"""Structurizr generated model-file rendering."""

from typing import Any, Dict, List, Set

from ..generated_paths import unique_generated_path
from .model_content import render_external_model, render_project_model, structurizr_model_context
from .relations import (
    render_structurizr_relationships,
    split_structurizr_relationships_by_file,
    structurizr_relationship_file_path,
)


def generated_fragment(comment: str, content: str) -> str:
    return f"// {comment}\n" + content


def render_structurizr_model_files(architecture: Dict[str, Any]) -> Dict[str, str]:
    context = structurizr_model_context(architecture)
    files: Dict[str, str] = {}
    files.update(_external_model_file(architecture, context))
    files.update(_project_model_files(architecture, context))
    files.update(_relationship_model_files(architecture, context))
    return files


def _external_model_file(architecture: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, str]:
    external_systems = [system for system in architecture.get("systems") or [] if not system.get("project_id")]
    return {
        "model/external/00-external.dsl": generated_fragment(
            "Generated external dependencies by kmap. Do not edit manually.",
            render_external_model(architecture, external_systems, context),
        )
    }


def _project_model_files(architecture: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, str]:
    files: Dict[str, str] = {}
    projects_by_id = context["projects_by_id"]
    project_ids_with_systems = {
        system.get("project_id") or "" for system in architecture.get("systems") or [] if system.get("project_id")
    }
    used_project_paths: set[str] = set()
    emitted_project_ids: set[str] = set()
    for project in sorted(
        architecture.get("projects") or [], key=lambda item: item.get("name") or item.get("id") or ""
    ):
        project_id = project.get("id") or ""
        if project_id not in project_ids_with_systems:
            continue
        path = unique_generated_path(project, used_project_paths, directory="model/projects", extension="dsl")
        files[path] = generated_fragment(
            f"Generated model for project {project.get('name') or project_id} by kmap. Do not edit manually.",
            render_project_model(architecture, project, context),
        )
        emitted_project_ids.add(project_id)

    for project_id in _orphan_project_ids(project_ids_with_systems, emitted_project_ids):
        project = projects_by_id.get(project_id) or {"id": project_id, "name": project_id}
        path = unique_generated_path(project, used_project_paths, directory="model/projects", extension="dsl")
        files[path] = generated_fragment(
            f"Generated model for project {project.get('name') or project_id} by kmap. Do not edit manually.",
            render_project_model(architecture, project, context),
        )
    return files


def _orphan_project_ids(project_ids_with_systems: Set[str], emitted_project_ids: Set[str]) -> List[str]:
    return [project_id for project_id in sorted(project_ids_with_systems) if project_id not in emitted_project_ids]


def _relationship_model_files(architecture: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, str]:
    files: Dict[str, str] = {}
    refs = context["refs"]
    external_relationships, relationships_by_project = split_structurizr_relationships_by_file(
        architecture,
        refs,
        context["systems_by_id"],
        {container.get("id"): container for container in architecture.get("containers") or []},
    )

    files["model/relations/00-external.dsl"] = generated_fragment(
        "Generated external relationships by kmap. Do not edit manually.",
        render_structurizr_relationships(external_relationships, refs),
    )
    used_relation_paths: set[str] = set()
    for project_id, relationships in sorted(relationships_by_project.items()):
        project = context["projects_by_id"].get(project_id) or {"id": project_id, "name": project_id}
        path = structurizr_relationship_file_path(project, used_relation_paths)
        files[path] = generated_fragment(
            f"Generated relationships for project {project.get('name') or project_id} by kmap. Do not edit manually.",
            render_structurizr_relationships(relationships, refs),
        )

    return files


__all__ = [
    "generated_fragment",
    "render_structurizr_model_files",
]
