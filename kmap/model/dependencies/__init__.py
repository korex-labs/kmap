"""Dependency relationship construction for architecture models."""

from typing import Any, Dict, List

from .dependency_relationships import (
    DependencyRelationshipContext,
    dependency_relationship,
    dependency_relationship_from_context,
)
from .state import DependencyBuildState, RelationContext, TargetResolution
from .targets import relation_context, resolve_dependency_target


def build_dependency_relationships(
    *,
    dependency_relations: List[Dict[str, Any]],
    workload_primary_container_ids: Dict[str, str],
    workload_project_ids: Dict[str, str],
    external_mappings: List[Dict[str, Any]],
    systems_by_id: Dict[str, Dict[str, Any]],
    containers_by_id: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    relationships = []
    state = DependencyBuildState(
        external_mappings=external_mappings,
        systems_by_id=systems_by_id,
        containers_by_id=containers_by_id,
    )

    for rel in dependency_relations:
        context = relation_context(rel, workload_primary_container_ids, workload_project_ids)
        if context is None:
            continue

        target = resolve_dependency_target(
            rel=rel,
            context=context,
            state=state,
            workload_primary_container_ids=workload_primary_container_ids,
            workload_project_ids=workload_project_ids,
        )
        if not target.target_id:
            continue

        relationships.append(relationship_from_resolution(context, target))

    return relationships


def relationship_from_resolution(context: RelationContext, target: TargetResolution) -> Dict[str, Any]:
    return dependency_relationship_from_context(
        DependencyRelationshipContext(
            source_id=context.source_id,
            target_id=target.target_id,
            dep_key=context.dep_key,
            source_var=context.source_var,
            mapping=target.mapping,
            match_type=context.match_type,
            category=target.category,
            boundary_kind=target.boundary_kind,
            source_project_id=context.source_project_id,
            target_project_id=target.target_project_id,
            rel_metadata=context.rel_metadata,
            evidence=context.evidence,
            source_origin=context.source_origin,
        )
    )


__all__ = [
    "DependencyBuildState",
    "DependencyRelationshipContext",
    "RelationContext",
    "TargetResolution",
    "build_dependency_relationships",
    "dependency_relationship",
    "dependency_relationship_from_context",
    "relationship_from_resolution",
]
