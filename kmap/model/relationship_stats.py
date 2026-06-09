"""Relationship statistics recording helpers."""

from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from ..identifiers import architecture_id
from ..identifiers import short_hash as _short_hash


@dataclass(frozen=True)
class RelationshipStatsContext:
    source_id: str
    target_id: str
    source_system_id: str
    target_system_id: str
    rel_type: str
    boundary_kind: str


def system_id_for_element(
    element_id: str,
    systems_by_id: Dict[str, Dict[str, Any]],
    containers_by_id: Dict[str, Dict[str, Any]],
) -> str:
    if element_id in systems_by_id:
        return element_id
    container = containers_by_id.get(element_id)
    return (container or {}).get("system_id") or ""


def relationship_stats_context(
    rel: Dict[str, Any],
    systems_by_id: Dict[str, Dict[str, Any]],
    containers_by_id: Dict[str, Dict[str, Any]],
) -> RelationshipStatsContext | None:
    source_id = rel.get("source_id") or ""
    target_id = rel.get("target_id") or ""
    source_system_id = system_id_for_element(source_id, systems_by_id, containers_by_id)
    target_system_id = system_id_for_element(target_id, systems_by_id, containers_by_id)
    if not source_system_id or not target_system_id:
        return None
    return RelationshipStatsContext(
        source_id=source_id,
        target_id=target_id,
        source_system_id=source_system_id,
        target_system_id=target_system_id,
        rel_type=rel.get("type") or rel.get("technology") or "dependency",
        boundary_kind=((rel.get("boundary") or {}).get("kind")) or rel.get("category") or "",
    )


def record_relationship_system_stats(
    system_stats: Dict[str, Dict[str, Any]],
    containers_by_id: Dict[str, Dict[str, Any]],
    *,
    context: RelationshipStatsContext,
) -> None:
    target_stats = system_stats.get(context.target_system_id)
    if target_stats is not None:
        target_stats["incoming_relationship_count"] += 1
        if context.source_system_id != context.target_system_id:
            target_stats["incoming_source_system_ids"].add(context.source_system_id)
        if context.source_id in containers_by_id:
            target_stats["incoming_source_container_ids"].add(context.source_id)
        target_stats["incoming_by_type"][context.rel_type] += 1
        target_stats["incoming_by_boundary"][context.boundary_kind] += 1

    source_stats = system_stats.get(context.source_system_id)
    if source_stats is not None:
        source_stats["outgoing_relationship_count"] += 1
        if context.target_system_id != context.source_system_id:
            source_stats["outgoing_target_system_ids"].add(context.target_system_id)
        if context.target_id in containers_by_id:
            source_stats["outgoing_target_container_ids"].add(context.target_id)
        source_stats["outgoing_by_type"][context.rel_type] += 1
        source_stats["outgoing_by_boundary"][context.boundary_kind] += 1


def record_relationship_group(
    aggregate_pairs: Dict[Tuple[str, str, str, str], Dict[str, Any]],
    containers_by_id: Dict[str, Dict[str, Any]],
    *,
    rel: Dict[str, Any],
    context: RelationshipStatsContext,
) -> None:
    aggregate_key = (
        context.source_system_id,
        context.target_system_id,
        context.rel_type,
        context.boundary_kind,
    )
    aggregate = aggregate_pairs.setdefault(aggregate_key, initial_relationship_group(aggregate_key))
    aggregate["relationship_count"] += 1
    aggregate["relationship_ids"].append(rel.get("id") or "")
    if context.source_id in containers_by_id:
        aggregate["source_container_ids"].add(context.source_id)
    if context.target_id in containers_by_id:
        aggregate["target_container_ids"].add(context.target_id)


def initial_system_stats(system: Dict[str, Any], system_id: str) -> Dict[str, Any]:
    return {
        "system_id": system_id,
        "title": system.get("title") or system.get("name") or system_id,
        "kind": system.get("kind") or "",
        "category": system.get("category") or "",
        "project_id": system.get("project_id") or "",
        "incoming_relationship_count": 0,
        "outgoing_relationship_count": 0,
        "incoming_source_system_ids": set(),
        "incoming_source_container_ids": set(),
        "outgoing_target_system_ids": set(),
        "outgoing_target_container_ids": set(),
        "incoming_by_type": Counter(),
        "outgoing_by_type": Counter(),
        "incoming_by_boundary": Counter(),
        "outgoing_by_boundary": Counter(),
    }


def initial_relationship_group(aggregate_key: Tuple[str, str, str, str]) -> Dict[str, Any]:
    source_system_id, target_system_id, rel_type, boundary_kind = aggregate_key
    return {
        "id": architecture_id("relagg", _short_hash("|".join(aggregate_key), 12)),
        "source_system_id": source_system_id,
        "target_system_id": target_system_id,
        "type": rel_type,
        "boundary_kind": boundary_kind,
        "relationship_count": 0,
        "source_container_ids": set(),
        "target_container_ids": set(),
        "relationship_ids": [],
    }


__all__ = [
    "RelationshipStatsContext",
    "initial_relationship_group",
    "initial_system_stats",
    "record_relationship_group",
    "record_relationship_system_stats",
    "relationship_stats_context",
    "system_id_for_element",
]
