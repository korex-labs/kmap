"""Dependency relationship record construction."""

from dataclasses import dataclass
from typing import Any, Dict, List

from ...identifiers import architecture_id
from ...naming import dependency_display_name, short_hash
from ..relationships import relation_origin_label, relationship_type_from_dependency


@dataclass(frozen=True)
class DependencyRelationshipContext:
    source_id: str
    target_id: str
    dep_key: str
    source_var: str
    mapping: Dict[str, Any] | None
    match_type: str
    category: str
    boundary_kind: str
    source_project_id: str | None
    target_project_id: str | None
    rel_metadata: Dict[str, Any]
    evidence: str
    source_origin: str


def dependency_relationship_from_context(context: DependencyRelationshipContext) -> Dict[str, Any]:
    rel_type = relationship_type_from_dependency(context.dep_key, context.source_var, context.mapping)
    rel_id = dependency_relationship_id(
        context.source_id,
        context.target_id,
        context.dep_key,
        context.source_var,
        context.match_type,
    )
    relationship = {
        "id": rel_id,
        "source_id": context.source_id,
        "target_id": context.target_id,
        "category": context.category,
        "type": rel_type,
        "title": dependency_display_name(context.dep_key) if context.dep_key else rel_type,
        "technology": rel_type,
        "tags": dependency_tags(context.boundary_kind),
        "evidence": [
            dependency_evidence(context.source_origin, context.source_var, context.evidence, context.match_type)
        ],
        "confidence": 1.0,
        "boundary": dependency_boundary(
            context.source_project_id,
            context.target_project_id,
            context.boundary_kind,
        ),
    }
    if context.rel_metadata:
        relationship["metadata"] = context.rel_metadata
    return relationship


def dependency_tags(boundary_kind: str) -> List[str]:
    tags = ["Generated"]
    if boundary_kind != "same_project":
        tags.append("CrossBoundary")
    return tags


def dependency_relationship(**relationship_options: Any) -> Dict[str, Any]:
    return dependency_relationship_from_context(
        DependencyRelationshipContext(
            source_id=relationship_options["source_id"],
            target_id=relationship_options["target_id"],
            dep_key=relationship_options["dep_key"],
            source_var=relationship_options["source_var"],
            mapping=relationship_options["mapping"],
            match_type=relationship_options["match_type"],
            category=relationship_options["category"],
            boundary_kind=relationship_options["boundary_kind"],
            source_project_id=relationship_options["source_project_id"],
            target_project_id=relationship_options["target_project_id"],
            rel_metadata=relationship_options["rel_metadata"],
            evidence=relationship_options["evidence"],
            source_origin=relationship_options["source_origin"],
        )
    )


def dependency_relationship_id(
    source_id: str,
    target_id: str,
    dep_key: str,
    source_var: str,
    match_type: str,
) -> str:
    return architecture_id(
        "rel",
        short_hash("|".join([source_id, target_id, dep_key, source_var, match_type]), 12),
    )


def dependency_evidence(source_origin: str, source_var: str, evidence: str, match_type: str) -> Dict[str, Any]:
    return {
        "kind": relation_origin_label(source_origin),
        "source": source_var,
        "value": evidence,
        "match_type": match_type,
    }


def dependency_boundary(
    source_project_id: str | None,
    target_project_id: str | None,
    boundary_kind: str,
) -> Dict[str, str | None]:
    return {
        "source_project_id": source_project_id,
        "target_project_id": target_project_id,
        "kind": boundary_kind,
    }


__all__ = [
    "DependencyRelationshipContext",
    "dependency_boundary",
    "dependency_evidence",
    "dependency_relationship",
    "dependency_relationship_from_context",
    "dependency_relationship_id",
    "dependency_tags",
]
