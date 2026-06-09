"""Table data builders for generated LikeC4 READMEs."""

from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List

from ...config import clean_int, clean_metadata_string
from ...naming import humanize_slug
from ...rendering_resources import project_resource_items
from ..markdown import short_join
from .readme_table_external import external_dependency_maps, external_readme_rows, external_rows
from .readme_table_indexes import generic_system_names, split_systems, system_for_element, system_indexes


@dataclass
class ReadmeTables:
    internal_systems: List[Dict[str, Any]]
    external_systems: List[Dict[str, Any]]
    relationship_type_counts: Counter
    boundary_counts: Counter
    project_rows: List[List[Any]]
    project_resource_rows: List[List[Any]]
    top_incoming_rows: List[List[Any]]
    top_outgoing_rows: List[List[Any]]
    external_rows: List[List[Any]]
    external_evidence_rows: List[List[Any]]
    cross_project_rows: List[List[Any]]
    generic_external: List[str]
    generic_internal: List[str]
    missing_owner_projects: List[str]
    deployment_rows: List[List[Any]]
    traffic_flow_rows: List[List[Any]]


def readme_tables(context: Dict[str, Any]) -> ReadmeTables:
    internal_systems, external_systems = split_systems(context["systems"])
    relationship_type_counts = Counter(rel.get("type") or "unknown" for rel in context["relationships"])
    boundary_counts = Counter((rel.get("boundary") or {}).get("kind") or "unknown" for rel in context["relationships"])
    project_rows, project_resource_rows = project_rows_for_readme(
        context["projects"], internal_systems, context["containers"]
    )
    external_rows, external_evidence_rows = external_readme_rows(context, external_systems)
    generic_external = [name for name in generic_system_names(external_systems) if name]
    generic_internal = [name for name in generic_system_names(internal_systems) if name]
    missing_owner_projects = [
        project.get("name") or project.get("id") for project in context["projects"] if not project.get("owner_team")
    ]
    return ReadmeTables(
        internal_systems=internal_systems,
        external_systems=external_systems,
        relationship_type_counts=relationship_type_counts,
        boundary_counts=boundary_counts,
        project_rows=project_rows,
        project_resource_rows=project_resource_rows,
        top_incoming_rows=top_incoming_rows(context["system_stats"]),
        top_outgoing_rows=top_outgoing_rows(context["system_stats"]),
        external_rows=external_rows,
        external_evidence_rows=external_evidence_rows,
        cross_project_rows=cross_project_rows(context["relationships"], context["projects"]),
        generic_external=generic_external,
        generic_internal=generic_internal,
        missing_owner_projects=missing_owner_projects,
        deployment_rows=deployment_rows(context["deployments"], context["default_env"]),
        traffic_flow_rows=traffic_flow_rows(context["traffic_flows"]),
    )


def project_rows_for_readme(
    projects: List[Dict[str, Any]], internal_systems: List[Dict[str, Any]], containers: List[Dict[str, Any]]
) -> tuple[List[List[Any]], List[List[Any]]]:
    project_rows = []
    project_resource_rows = []
    for project in sorted(projects, key=lambda item: item.get("name") or ""):
        project_systems = [system for system in internal_systems if system.get("project_id") == project.get("id")]
        project_containers = [container for container in containers if container.get("project_id") == project.get("id")]
        namespaces = (project.get("discovery") or {}).get("namespaces") or []
        project_title = project.get("title") or project.get("name") or project.get("id") or ""
        project_rows.append(
            [
                project_title,
                project.get("owner_team") or "-",
                len(project_systems),
                len(project_containers),
                short_join(namespaces, limit=3) or "-",
            ]
        )
        for key, value in project_resource_items(project):
            project_resource_rows.append([project_title, humanize_slug(key), value])
    return project_rows, project_resource_rows


def top_incoming_rows(system_stats: List[Dict[str, Any]]) -> List[List[Any]]:
    sorted_stats = sorted(
        system_stats,
        key=lambda row: (
            clean_int(row.get("incoming_distinct_source_container_count"), 0, minimum=0),
            clean_int(row.get("incoming_relationship_count"), 0, minimum=0),
        ),
        reverse=True,
    )
    return [
        [
            item.get("title") or item.get("system_id") or "",
            item.get("kind") or "",
            item.get("category") or "",
            item.get("incoming_distinct_source_container_count") or 0,
            item.get("incoming_relationship_count") or 0,
        ]
        for item in sorted_stats[:10]
    ]


def top_outgoing_rows(system_stats: List[Dict[str, Any]]) -> List[List[Any]]:
    sorted_stats = sorted(
        system_stats,
        key=lambda row: clean_int(row.get("outgoing_relationship_count"), 0, minimum=0),
        reverse=True,
    )
    return [
        [
            item.get("title") or item.get("system_id") or "",
            item.get("category") or "",
            item.get("outgoing_relationship_count") or 0,
            item.get("outgoing_distinct_target_system_count") or 0,
        ]
        for item in sorted_stats[:10]
    ]


def cross_project_rows(relationships: List[Dict[str, Any]], projects: List[Dict[str, Any]]) -> List[List[Any]]:
    projects_by_id = {project.get("id"): project for project in projects}
    cross_project_counts: Counter = Counter()
    for rel in relationships:
        boundary = rel.get("boundary") or {}
        if boundary.get("kind") != "cross_project":
            continue
        source_project = projects_by_id.get(boundary.get("source_project_id") or "")
        target_project = projects_by_id.get(boundary.get("target_project_id") or "")
        source_name = (source_project or {}).get("name") or boundary.get("source_project_id") or ""
        target_name = (target_project or {}).get("name") or boundary.get("target_project_id") or ""
        cross_project_counts[source_name, target_name] += 1
    return [
        [source, target, count]
        for (source, target), count in sorted(cross_project_counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def deployment_rows(deployments: List[Dict[str, Any]], default_env: str) -> List[List[Any]]:
    rows = []
    for deployment in deployments:
        clusters = deployment.get("clusters") or []
        namespace_count = sum(len(cluster.get("namespaces") or []) for cluster in clusters)
        instance_count = sum(
            len(namespace.get("instances") or [])
            for cluster in clusters
            for namespace in (cluster.get("namespaces") or [])
        )
        rows.append([deployment.get("env") or default_env, len(clusters), namespace_count, instance_count])
    return rows


def traffic_flow_rows(traffic_flows: List[Dict[str, Any]]) -> List[List[Any]]:
    rows = []
    for flow in sorted(traffic_flows, key=lambda item: item.get("id") or "")[:20]:
        hops = " -> ".join(
            clean_metadata_string(hop.get("type") or "") + ":" + clean_metadata_string(hop.get("name") or "")
            for hop in flow.get("hops") or []
            if clean_metadata_string(hop.get("type") or hop.get("name"))
        )
        source = flow.get("source") or {}
        rows.append(
            [flow.get("direction") or "inbound", source.get("name") or "-", flow.get("namespace") or "-", hops or "-"]
        )
    return rows


__all__ = [
    "ReadmeTables",
    "cross_project_rows",
    "deployment_rows",
    "external_dependency_maps",
    "external_readme_rows",
    "external_rows",
    "generic_system_names",
    "project_rows_for_readme",
    "readme_tables",
    "split_systems",
    "system_for_element",
    "system_indexes",
    "top_incoming_rows",
    "top_outgoing_rows",
    "traffic_flow_rows",
]
