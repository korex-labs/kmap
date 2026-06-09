"""External dependency table builders for LikeC4 READMEs."""

from collections import Counter, defaultdict
from typing import Any, Dict, List

from ..markdown import short_join
from .readme_table_indexes import system_for_element, system_indexes


def external_dependency_maps(
    relationships: List[Dict[str, Any]],
    external_systems: List[Dict[str, Any]],
    systems_by_id: Dict[str, Dict[str, Any]],
    containers_by_id: Dict[str, Dict[str, Any]],
) -> tuple[Counter, Dict[str, set], Dict[str, List[str]], Dict[str, List[str]]]:
    def local_system_for_element(element_id: str) -> Dict[str, Any]:
        return system_for_element(element_id, systems_by_id, containers_by_id)

    consumers_by_external: Dict[str, set] = defaultdict(set)
    relationship_titles_by_external: Dict[str, List[str]] = defaultdict(list)
    database_names_by_external: Dict[str, List[str]] = defaultdict(list)
    relationship_count_by_external: Counter = Counter()
    external_ids = {system.get("id") for system in external_systems}
    for rel in relationships:
        target_system = local_system_for_element(rel.get("target_id") or "")
        source_system = local_system_for_element(rel.get("source_id") or "")
        target_system_id = target_system.get("id")
        if target_system_id and target_system_id in external_ids:
            relationship_count_by_external[target_system_id] += 1
            if source_system.get("title"):
                consumers_by_external[target_system_id].add(source_system.get("title"))
            if rel.get("title"):
                relationship_titles_by_external[target_system_id].append(rel.get("title"))
            database = ((rel.get("metadata") or {}).get("database")) or {}
            for name in database.get("names") or []:
                if name and name not in database_names_by_external[target_system_id]:
                    database_names_by_external[target_system_id].append(name)
    return (
        relationship_count_by_external,
        consumers_by_external,
        relationship_titles_by_external,
        database_names_by_external,
    )


def external_rows(
    external_systems: List[Dict[str, Any]],
    relationship_count_by_external: Counter,
    consumers_by_external: Dict[str, set],
    relationship_titles_by_external: Dict[str, List[str]],
    database_names_by_external: Dict[str, List[str]],
) -> tuple[List[List[Any]], List[List[Any]]]:
    external_rows_result = []
    external_evidence_rows = []
    for system in sorted(external_systems, key=lambda item: item.get("title") or ""):
        system_id = system.get("id") or ""
        external_title = system.get("title") or system.get("name") or system_id
        external_rows_result.append(
            [
                external_title,
                system.get("element_type") or "system",
                relationship_count_by_external.get(system_id, 0),
                short_join(sorted(consumers_by_external.get(system_id, [])), limit=4) or "-",
            ]
        )
        external_evidence_rows.append(
            [
                external_title,
                short_join(
                    [
                        *relationship_titles_by_external.get(system_id, []),
                        f"databases: {short_join(database_names_by_external.get(system_id, []), limit=8)}",
                    ]
                    if database_names_by_external.get(system_id)
                    else relationship_titles_by_external.get(system_id, []),
                    limit=4,
                )
                or "-",
            ]
        )
    return external_rows_result, external_evidence_rows


def external_readme_rows(
    context: Dict[str, Any],
    external_systems: List[Dict[str, Any]],
) -> tuple[List[List[Any]], List[List[Any]]]:
    systems_by_id, containers_by_id = system_indexes(context["systems"], context["containers"])
    return external_rows(
        external_systems,
        *external_dependency_maps(context["relationships"], external_systems, systems_by_id, containers_by_id),
    )


__all__ = ["external_dependency_maps", "external_readme_rows", "external_rows"]
