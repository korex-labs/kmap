"""Relationship classification and aggregate statistics."""

from typing import Any, Dict, List, Tuple

from ..config import clean_metadata_string
from .relationship_rendering import render_relationship_group, render_system_stats
from .relationship_stats import (
    initial_system_stats,
    record_relationship_group,
    record_relationship_system_stats,
    relationship_stats_context,
)

RELATIONSHIP_TYPE_TOKENS = (
    ("kafka", ("kafka",)),
    ("redis", ("redis",)),
    ("db", ("mysql", "postgres", "pgsql", "mongo", "clickhouse")),
    ("https", ("http", "https", "url", "uri")),
    ("amqp", ("amqp", "rabbit")),
    ("grpc", ("grpc",)),
)

ORIGIN_LABELS = {
    "Env": "env",
    "VaultEnv": "vault",
    "Secret": "secret",
    "ConfigMap": "config",
}


def relationship_type_from_dependency(dep_key: str, source_var: str, mapping: Dict[str, Any] | None = None) -> str:
    text = " ".join(
        [
            dep_key or "",
            source_var or "",
            clean_metadata_string((mapping or {}).get("name")),
        ]
    ).lower()
    for rel_type, tokens in RELATIONSHIP_TYPE_TOKENS:
        if any(token in text for token in tokens):
            return rel_type
    return "tcp"


def relation_origin_label(source_origin: str) -> str:
    return ORIGIN_LABELS.get(source_origin or "", "config")


def build_relationship_statistics(
    systems: List[Dict[str, Any]],
    containers: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]],
) -> Dict[str, Any]:
    systems_by_id = {system.get("id"): system for system in systems}
    containers_by_id = {container.get("id"): container for container in containers}
    system_stats: Dict[str, Dict[str, Any]] = {}
    for system in systems:
        system_id = system.get("id") or ""
        system_stats[system_id] = initial_system_stats(system, system_id)

    aggregate_pairs: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}

    for rel in relationships:
        context = relationship_stats_context(rel, systems_by_id, containers_by_id)
        if context is None:
            continue

        record_relationship_system_stats(
            system_stats,
            containers_by_id,
            context=context,
        )
        record_relationship_group(
            aggregate_pairs,
            containers_by_id,
            rel=rel,
            context=context,
        )

    rendered_system_stats = [render_system_stats(stats) for stats in system_stats.values()]
    rendered_aggregates = [render_relationship_group(aggregate) for aggregate in aggregate_pairs.values()]

    rendered_system_stats.sort(key=lambda item: item.get("system_id", ""))
    rendered_aggregates.sort(key=lambda item: item.get("id", ""))

    return {
        "summary": {
            "raw_relationship_count": len(relationships),
            "system_relationship_group_count": len(rendered_aggregates),
        },
        "systems": rendered_system_stats,
        "system_relationship_groups": rendered_aggregates,
    }


__all__ = [
    "build_relationship_statistics",
    "relation_origin_label",
    "relationship_type_from_dependency",
]
