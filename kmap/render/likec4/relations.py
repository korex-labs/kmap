"""LikeC4 relationships renderer."""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List

from ..generated_paths import unique_generated_path
from ..markdown import short_join
from .common import likec4_alias, likec4_metadata_lines, likec4_quote, likec4_reference_map


@dataclass
class _LikeC4RelationsContext:
    refs: Dict[str, str]


def likec4_relationship_kind(rel_type: str) -> str:
    rel_type = (rel_type or "").lower()
    if rel_type in {"http", "https"}:
        return "http_s"
    if rel_type == "kafka":
        return "KafkaPub"
    return "tcp"


def _element_project_map(architecture: Dict[str, Any]) -> Dict[str, str]:
    systems_by_id = {system.get("id"): system for system in architecture.get("systems") or []}
    out: Dict[str, str] = {}
    for system in architecture.get("systems") or []:
        system_id = system.get("id") or ""
        if system_id:
            out[system_id] = system.get("project_id") or ""
    for container in architecture.get("containers") or []:
        container_id = container.get("id") or ""
        system = systems_by_id.get(container.get("system_id") or "") or {}
        if container_id:
            out[container_id] = system.get("project_id") or container.get("project_id") or ""
    return out


def _render_likec4_relations(
    architecture: Dict[str, Any],
    relationships: List[Dict[str, Any]],
    *,
    comment: str = "Generated relationships by kmap. Do not edit manually.",
) -> str:
    context = _likec4_relations_context(architecture)
    lines = [
        "model {",
        f"  // {comment}",
        "",
    ]
    for rel in sorted(relationships, key=lambda item: item.get("id", "")):
        lines.extend(_relationship_lines(rel, context))
    lines.append("")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _likec4_relations_context(architecture: Dict[str, Any]) -> _LikeC4RelationsContext:
    return _LikeC4RelationsContext(refs=likec4_reference_map(architecture))


def _relationship_lines(rel: Dict[str, Any], context: _LikeC4RelationsContext) -> List[str]:
    source, target = _relationship_endpoints(rel, context)
    if not source or not target or source == target:
        return []
    kind = likec4_relationship_kind(rel.get("type") or "")
    title = rel.get("title") or "uses"
    lines = [f'  {source} -[{kind}]-> {target} "{likec4_quote(title)}" {{']
    if rel.get("technology"):
        lines.append(f'    technology "{likec4_quote(rel.get("technology"))}"')
    boundary = (rel.get("boundary") or {}).get("kind")
    if boundary:
        lines.append(f'    description "Boundary: {likec4_quote(boundary)}"')
    lines.extend(_relationship_database_metadata_lines(rel))
    lines.append("  }")
    return lines


def _relationship_endpoints(rel: Dict[str, Any], context: _LikeC4RelationsContext) -> tuple[str, str]:
    source_id = rel.get("source_id") or ""
    target_id = rel.get("target_id") or ""
    if not source_id or not target_id:
        return "", ""
    return context.refs.get(source_id) or likec4_alias(source_id), context.refs.get(target_id) or likec4_alias(
        target_id
    )


def _relationship_database_metadata_lines(rel: Dict[str, Any]) -> List[str]:
    database = ((rel.get("metadata") or {}).get("database")) or {}
    return likec4_metadata_lines(
        [
            ("database_engine", database.get("engine") or ""),
            ("databases", short_join(database.get("names") or [], limit=8)),
        ],
        indent="    ",
    )


def render_likec4_relations(architecture: Dict[str, Any]) -> str:
    return _render_likec4_relations(architecture, architecture.get("relationships") or [])


def render_likec4_relation_files(architecture: Dict[str, Any]) -> Dict[str, str]:
    projects = architecture.get("projects") or []
    project_by_id = {project.get("id"): project for project in projects}
    element_projects = _element_project_map(architecture)
    external_relationships: List[Dict[str, Any]] = []
    relationships_by_project: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for rel in architecture.get("relationships") or []:
        source_project_id = element_projects.get(rel.get("source_id") or "")
        target_project_id = element_projects.get(rel.get("target_id") or "")
        if not source_project_id or not target_project_id:
            external_relationships.append(rel)
            continue
        relationships_by_project[source_project_id].append(rel)

    files: Dict[str, str] = {
        "model/relations/00-external.c4": _render_likec4_relations(
            architecture,
            external_relationships,
            comment="Generated external relationships by kmap. Do not edit manually.",
        )
    }
    used_paths: set[str] = set()
    for project_id, relationships in sorted(relationships_by_project.items()):
        project = project_by_id.get(project_id) or {"id": project_id, "name": project_id}
        path = unique_generated_path(project, used_paths, directory="model/relations", extension="c4")
        files[path] = _render_likec4_relations(
            architecture,
            relationships,
            comment=f"Generated relationships for project {project.get('name') or project_id} by kmap. Do not edit manually.",
        )
    return files


__all__ = ["likec4_relationship_kind", "render_likec4_relation_files", "render_likec4_relations"]
