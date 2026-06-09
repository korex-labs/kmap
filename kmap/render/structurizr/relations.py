"""Structurizr relationship rendering helpers."""

from typing import Any, Dict, List, Tuple

from ...identifiers import q
from ..generated_paths import unique_generated_path


def structurizr_relationship_technology(relationship: Dict[str, Any]) -> str:
    parts: List[str] = []
    for evidence in relationship.get("evidence") or []:
        kind = str(evidence.get("kind") or "").strip()
        if kind:
            parts.append(kind)
            break
    if not parts:
        fallback = str(relationship.get("technology") or relationship.get("type") or "").strip()
        if fallback:
            parts.append(fallback)
    boundary_kind = ((relationship.get("boundary") or {}).get("kind")) or ""
    if boundary_kind == "cross_project":
        parts.append("cross-project")
    return ", ".join(dict.fromkeys(parts))


def structurizr_relationship_line(relationship: Dict[str, Any], refs: Dict[str, str]) -> str:
    source = refs.get(relationship.get("source_id") or "")
    target = refs.get(relationship.get("target_id") or "")
    if not source or not target:
        return ""
    return f'{source} -> {target} "uses" "{q(structurizr_relationship_technology(relationship))}"'


def deduplicated_structurizr_relationships(
    relationships: List[Dict[str, Any]], refs: Dict[str, str]
) -> List[Dict[str, Any]]:
    emitted: set[tuple[str, str]] = set()
    result: List[Dict[str, Any]] = []
    for relationship in relationships:
        source = refs.get(relationship.get("source_id") or "")
        target = refs.get(relationship.get("target_id") or "")
        if not source or not target:
            continue
        relationship_key = (source, target)
        if relationship_key in emitted:
            continue
        emitted.add(relationship_key)
        result.append(relationship)
    return result


def render_structurizr_relationships(relationships: List[Dict[str, Any]], refs: Dict[str, str]) -> str:
    lines = [line for relationship in relationships if (line := structurizr_relationship_line(relationship, refs))]
    return "\n".join(lines) + ("\n" if lines else "")


def relationship_project_id(
    relationship: Dict[str, Any],
    systems_by_id: Dict[str, Dict[str, Any]],
    containers_by_id: Dict[str, Dict[str, Any]],
) -> str:
    source_id = relationship.get("source_id") or ""
    if source_id in systems_by_id:
        return systems_by_id[source_id].get("project_id") or ""
    container = containers_by_id.get(source_id) or {}
    system = systems_by_id.get(container.get("system_id") or "") or {}
    return system.get("project_id") or container.get("project_id") or ""


def relationship_has_external_endpoint(
    relationship: Dict[str, Any],
    systems_by_id: Dict[str, Dict[str, Any]],
    containers_by_id: Dict[str, Dict[str, Any]],
) -> bool:
    for endpoint in (relationship.get("source_id") or "", relationship.get("target_id") or ""):
        if endpoint in systems_by_id:
            if not systems_by_id[endpoint].get("project_id"):
                return True
            continue
        container = containers_by_id.get(endpoint) or {}
        system = systems_by_id.get(container.get("system_id") or "") or {}
        if endpoint and not system.get("project_id"):
            return True
    return False


def split_structurizr_relationships_by_file(
    architecture: Dict[str, Any],
    refs: Dict[str, str],
    systems_by_id: Dict[str, Dict[str, Any]],
    containers_by_id: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    external_relationships: List[Dict[str, Any]] = []
    relationships_by_project: Dict[str, List[Dict[str, Any]]] = {}
    for relationship in deduplicated_structurizr_relationships(architecture.get("relationships") or [], refs):
        if relationship_has_external_endpoint(relationship, systems_by_id, containers_by_id):
            external_relationships.append(relationship)
            continue
        project_id = relationship_project_id(relationship, systems_by_id, containers_by_id)
        relationships_by_project.setdefault(project_id, []).append(relationship)
    return external_relationships, relationships_by_project


def structurizr_relationship_file_path(project: Dict[str, Any], used_paths: set[str]) -> str:
    return unique_generated_path(project, used_paths, directory="model/relations", extension="dsl")


__all__ = [
    "deduplicated_structurizr_relationships",
    "relationship_has_external_endpoint",
    "relationship_project_id",
    "render_structurizr_relationships",
    "split_structurizr_relationships_by_file",
    "structurizr_relationship_file_path",
    "structurizr_relationship_line",
    "structurizr_relationship_technology",
]
