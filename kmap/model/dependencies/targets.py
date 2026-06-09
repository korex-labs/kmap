"""Dependency relation context and target resolution."""

from typing import Any, Dict

from ...config import clean_metadata_string
from .external import resolve_external_target
from .state import DependencyBuildState, RelationContext, TargetResolution


def relation_context(
    rel: Dict[str, Any],
    workload_primary_container_ids: Dict[str, str],
    workload_project_ids: Dict[str, str],
) -> RelationContext | None:
    source_service = clean_metadata_string(rel.get("source_service"))
    source_id = workload_primary_container_ids.get(source_service)
    if not source_id:
        return None

    rel_metadata = relation_metadata(rel)
    return RelationContext(
        source_service=source_service,
        source_id=source_id,
        source_project_id=workload_project_ids.get(source_service),
        dep_key=clean_metadata_string(rel.get("dependency_key")),
        source_var=clean_metadata_string(rel.get("source_var")),
        rel_metadata=rel_metadata,
        database_metadata=dict(rel_metadata.get("database") or {}),
        dependency_type=clean_metadata_string(rel.get("dependency_type")).upper(),
        match_type=clean_metadata_string(rel.get("match_type")),
        evidence=rel.get("evidence") or "",
        source_origin=rel.get("source_origin") or "",
    )


def relation_metadata(rel: Dict[str, Any]) -> Dict[str, Any]:
    return dict(rel.get("metadata") or {})


def resolve_dependency_target(
    *,
    rel: Dict[str, Any],
    context: RelationContext,
    state: DependencyBuildState,
    workload_primary_container_ids: Dict[str, str],
    workload_project_ids: Dict[str, str],
) -> TargetResolution:
    if context.dependency_type == "INTERNAL":
        return resolve_internal_target(rel, context, workload_primary_container_ids, workload_project_ids)
    return resolve_external_target(context, state)


def resolve_internal_target(
    rel: Dict[str, Any],
    context: RelationContext,
    workload_primary_container_ids: Dict[str, str],
    workload_project_ids: Dict[str, str],
) -> TargetResolution:
    target_service = clean_metadata_string(rel.get("target_service"))
    target_project_id = workload_project_ids.get(target_service)
    boundary_kind = (
        "same_project"
        if context.source_project_id and context.source_project_id == target_project_id
        else "cross_project"
    )
    return TargetResolution(
        target_id=workload_primary_container_ids.get(target_service, ""),
        category="internal",
        boundary_kind=boundary_kind,
        target_project_id=target_project_id,
    )


__all__ = [
    "relation_context",
    "relation_metadata",
    "resolve_dependency_target",
    "resolve_internal_target",
]
