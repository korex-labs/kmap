"""Dependency relation construction and grouping helpers."""

from collections import defaultdict
from typing import Any

from ...inspection.source_rank import source_rank
from ...lists import append_truthy_unique
from .indexing import build_entry_index, dependency_entry_hits


def merge_relation_metadata(rows: list[dict[str, Any]]) -> dict[str, Any]:
    database_names = []
    database_source_vars = []
    database_sources = []
    database_engine = ""
    for row in rows:
        database = ((row.get("metadata") or {}).get("database")) or {}
        if not database:
            continue
        if not database_engine:
            database_engine = database.get("engine") or ""
        append_unique_values(database_names, database.get("names") or [])
        append_unique_values(database_source_vars, database.get("source_vars") or [])
        append_unique_values(database_sources, database.get("sources") or [])

    if not (database_engine or database_names):
        return {}
    database_out = {
        "engine": database_engine,
        "names": sorted(database_names),
        "source_vars": sorted(database_source_vars),
        "sources": database_sources,
    }
    return {"database": {key: value for key, value in database_out.items() if value}}


def append_unique_values(target: list[Any], values: list[Any]) -> None:
    for value in values:
        append_truthy_unique(target, value)


def merge_relation_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    best = dict(best_relation_candidate(rows))
    metadata = merge_relation_metadata(rows)
    if metadata:
        best["metadata"] = metadata
    return best


def best_relation_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    priority = {
        "Service:same_namespace": 100,
        "Ingress:same_namespace": 90,
        "implicit_workload:same_namespace": 80,
        "Service:same_cluster": 70,
        "Ingress:same_cluster": 60,
        "implicit_workload:same_cluster": 50,
        "external": 10,
    }

    def key(row: dict[str, Any]) -> tuple[int, int, Any]:
        match_type = row.get("match_type") or ""
        source_origin = row.get("source_origin") or ""
        origin_rank = source_rank(source_origin)
        return (priority.get(match_type, 0), origin_rank, row.get("source_var", ""))

    return sorted(rows, key=key, reverse=True)[0]


def build_dependency_rows(
    services: list[dict[str, Any]],
    system_naming_config: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    entry_index = build_entry_index(services, system_naming_config)

    relations: list[dict[str, Any]] = []
    for service in services:
        for dependency in service.get("dependency_candidates", []):
            hits = dependency_entry_hits(dependency, service, entry_index, system_naming_config)
            if hits:
                relations.append(merge_relation_group(internal_dependency_rows(service, dependency, hits)))
            else:
                relations.append(external_dependency_row(service, dependency))

    grouped = defaultdict(list)
    for relationship in relations:
        group_key = (
            relationship["source_service"],
            relationship["target_service"]
            if relationship["dependency_type"] == "INTERNAL"
            else relationship["dependency_key"],
            relationship["dependency_type"],
        )
        grouped[group_key].append(relationship)

    final_rows = [merge_relation_group(rows) for rows in grouped.values()]
    final_rows.sort(
        key=lambda row: (
            row["source_service"],
            row["dependency_type"],
            row["target_service"],
            row["dependency_key"],
            row["source_var"],
        )
    )
    return final_rows


def external_dependency_row(service: dict[str, Any], dependency: dict[str, Any]) -> dict[str, Any]:
    row = {
        "source_service": service["service_id"],
        "source_var": dependency.get("var") or "",
        "dependency_key": dependency.get("key") or "",
        "dependency_type": "EXTERNAL",
        "target_service": "",
        "source_origin": dependency.get("source") or "",
        "match_type": "external",
        "evidence": dependency.get("value") or "",
    }
    if dependency.get("metadata"):
        row["metadata"] = dependency.get("metadata") or {}
    return row


def internal_dependency_rows(
    service: dict[str, Any], dependency: dict[str, Any], hits: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    same_namespace = [
        hit for hit in hits if hit["cluster"] == service["cluster"] and hit["namespace"] == service["namespace"]
    ]
    same_cluster = [hit for hit in hits if hit["cluster"] == service["cluster"]]
    candidates = same_namespace or same_cluster or hits
    for hit in candidates:
        entrypoint_type = hit["entrypoint_type"]
        scope = (
            "same_namespace" if hit in same_namespace else ("same_cluster" if hit in same_cluster else "cross_cluster")
        )
        row = {
            "source_service": service["service_id"],
            "source_var": dependency.get("var") or "",
            "dependency_key": dependency.get("key") or "",
            "dependency_type": "INTERNAL",
            "target_service": hit["service_id"],
            "source_origin": dependency.get("source") or "",
            "match_type": f"{entrypoint_type}:{scope}",
            "evidence": dependency.get("value") or "",
        }
        if dependency.get("metadata"):
            row["metadata"] = dependency.get("metadata") or {}
        rows.append(row)
    return rows


__all__ = [
    "append_unique_values",
    "best_relation_candidate",
    "build_dependency_rows",
    "external_dependency_row",
    "internal_dependency_rows",
    "merge_relation_group",
    "merge_relation_metadata",
]
