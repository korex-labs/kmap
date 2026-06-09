"""LikeC4 view context construction."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List

from ...config import clean_int, normalize_dependency_hotspots_config

MAJOR_EXTERNAL_MIN_SOURCE_SYSTEMS = 3
MAJOR_EXTERNAL_MIN_RELATIONSHIPS = 5


@dataclass
class LikeC4ViewContext:
    product_name: str
    systems_by_id: Dict[str, Dict[str, Any]]
    containers_by_id: Dict[str, Dict[str, Any]]
    project_by_id: Dict[str, Dict[str, Any]]
    internal_systems: List[Dict[str, Any]]
    project_systems: Dict[str, List[Dict[str, Any]]]
    internal_title_counts: Counter
    hotspot_config: Dict[str, Any]
    relationship_stats_by_system: Dict[str, Dict[str, Any]]
    relationship_context: "ExternalRelationshipContext"
    major_external_refs: set
    app_systems: List[Dict[str, Any]]
    platform_systems: List[Dict[str, Any]]
    deployments: List[Dict[str, Any]]


@dataclass
class ExternalRelationshipContext:
    external_refs: set
    external_source_systems: set
    external_refs_by_category: Dict[str, set]
    external_source_systems_by_category: Dict[str, set]
    direct_dependency_systems: Dict[str, set]

    @classmethod
    def empty(cls) -> "ExternalRelationshipContext":
        return cls(
            external_refs=set(),
            external_source_systems=set(),
            external_refs_by_category=defaultdict(set),
            external_source_systems_by_category=defaultdict(set),
            direct_dependency_systems=defaultdict(set),
        )


def likec4_view_context(architecture: Dict[str, Any]) -> LikeC4ViewContext:
    product_name = architecture.get("product", {}).get("name") or "product"
    systems = architecture.get("systems") or []
    containers = architecture.get("containers") or []
    relationships = architecture.get("relationships") or []
    project_by_id = {project.get("id"): project for project in architecture.get("projects") or []}
    containers_by_id = {container.get("id"): container for container in containers}
    systems_by_id = {system.get("id"): system for system in systems}
    internal_systems = internal_likec4_systems(systems)
    internal_title_counts = internal_system_title_counts(internal_systems)
    hotspot_config = architecture.get("dependency_hotspots") or normalize_dependency_hotspots_config({})
    relationship_stats_by_system = relationship_stats_by_system_id(architecture)
    relationship_context = external_relationship_context(relationships, systems_by_id, containers_by_id)
    major_external_refs = major_external_system_refs(
        relationship_context.external_refs,
        relationship_stats_by_system,
    )
    app_systems = application_likec4_systems(internal_systems)
    platform_systems = platform_likec4_systems(internal_systems)
    return LikeC4ViewContext(
        product_name=product_name,
        systems_by_id=systems_by_id,
        containers_by_id=containers_by_id,
        project_by_id=project_by_id,
        internal_systems=internal_systems,
        project_systems=project_systems(internal_systems),
        internal_title_counts=internal_title_counts,
        hotspot_config=hotspot_config,
        relationship_stats_by_system=relationship_stats_by_system,
        relationship_context=relationship_context,
        major_external_refs=major_external_refs,
        app_systems=app_systems,
        platform_systems=platform_systems,
        deployments=architecture.get("deployments") or [],
    )


def system_id_for_element(
    element_id: str,
    systems_by_id: Dict[str, Dict[str, Any]],
    containers_by_id: Dict[str, Dict[str, Any]],
) -> str:
    if element_id in systems_by_id:
        return element_id
    container = containers_by_id.get(element_id)
    return (container or {}).get("system_id") or ""


def project_systems(internal_systems: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for system in internal_systems:
        grouped.setdefault(system.get("project_id") or "", []).append(system)
    return grouped


def external_relationship_context(
    relationships: List[Dict[str, Any]],
    systems_by_id: Dict[str, Dict[str, Any]],
    containers_by_id: Dict[str, Dict[str, Any]],
) -> ExternalRelationshipContext:
    context = ExternalRelationshipContext.empty()
    for rel in relationships:
        source_system_id = system_id_for_element(rel.get("source_id") or "", systems_by_id, containers_by_id)
        target_system_id = system_id_for_element(rel.get("target_id") or "", systems_by_id, containers_by_id)
        source_system = systems_by_id.get(source_system_id)
        target_system = systems_by_id.get(target_system_id)
        record_direct_dependency_context(context, source_system_id, source_system, target_system_id, target_system)
        record_external_dependency_context(context, target_system_id, target_system, source_system_id, source_system)
        record_external_dependency_context(context, source_system_id, source_system, target_system_id, target_system)
    return context


def is_external_system_ref(system: Dict[str, Any] | None) -> bool:
    return bool(system and "External" in (system.get("tags") or []))


def record_direct_dependency_context(
    context: ExternalRelationshipContext,
    source_system_id: str,
    source_system: Dict[str, Any] | None,
    target_system_id: str,
    target_system: Dict[str, Any] | None,
) -> None:
    if not (source_system_id and target_system_id and source_system_id != target_system_id):
        return
    if source_system and not is_external_system_ref(source_system):
        context.direct_dependency_systems[source_system_id].add(target_system_id)
    if target_system and not is_external_system_ref(target_system):
        context.direct_dependency_systems[target_system_id].add(source_system_id)


def record_external_dependency_context(
    context: ExternalRelationshipContext,
    external_system_id: str,
    external_system: Dict[str, Any] | None,
    source_system_id: str,
    source_system: Dict[str, Any] | None,
) -> None:
    if not is_external_system_ref(external_system):
        return
    context.external_refs.add(external_system_id)
    category = external_system.get("category") or "External"
    context.external_refs_by_category[category].add(external_system_id)
    if source_system and not is_external_system_ref(source_system):
        context.external_source_systems.add(source_system_id)
        context.external_source_systems_by_category[category].add(source_system_id)


def is_major_external(system_id: str, relationship_stats_by_system: Dict[str, Dict[str, Any]]) -> bool:
    stats = relationship_stats_by_system.get(system_id) or {}
    return (
        clean_int(stats.get("incoming_distinct_source_system_count"), 0, minimum=0) >= MAJOR_EXTERNAL_MIN_SOURCE_SYSTEMS
        or clean_int(stats.get("incoming_relationship_count"), 0, minimum=0) >= MAJOR_EXTERNAL_MIN_RELATIONSHIPS
    )


def internal_likec4_systems(systems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [system for system in systems if "External" not in (system.get("tags") or [])]


def internal_system_title_counts(internal_systems: List[Dict[str, Any]]) -> Counter:
    return Counter(system.get("title") or system.get("name") or system.get("id") or "" for system in internal_systems)


def relationship_stats_by_system_id(architecture: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        item.get("system_id"): item
        for item in ((architecture.get("relationship_statistics") or {}).get("systems") or [])
    }


def major_external_system_refs(
    external_refs: set,
    relationship_stats_by_system: Dict[str, Dict[str, Any]],
) -> set:
    return {system_id for system_id in external_refs if is_major_external(system_id, relationship_stats_by_system)}


def application_likec4_systems(internal_systems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [system for system in internal_systems if system.get("category") in {"App", "Gateway"}]


def platform_likec4_systems(internal_systems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        system
        for system in internal_systems
        if system.get("category") in {"Data", "Messaging", "Monitoring", "Support"}
    ]


__all__ = [
    "ExternalRelationshipContext",
    "LikeC4ViewContext",
    "application_likec4_systems",
    "external_relationship_context",
    "internal_likec4_systems",
    "internal_system_title_counts",
    "likec4_view_context",
    "major_external_system_refs",
    "platform_likec4_systems",
    "relationship_stats_by_system_id",
]
