"""Final architecture model assembly helpers."""

from dataclasses import dataclass
from typing import Any, Dict, List

from .deployments import deployment_entries_from_envs
from .relationships import build_relationship_statistics
from .traffic_flows import traffic_flows_from_workloads


@dataclass(frozen=True)
class ArchitectureDocumentContext:
    naming: Any
    product_id: str
    product_name: str
    product_metadata: Dict[str, Any]
    generated_at: str
    generator: Dict[str, str]
    config_file: str
    discovery_config: Dict[str, Any]
    projects_by_id: Dict[str, Dict[str, Any]]
    systems_by_id: Dict[str, Dict[str, Any]]
    containers_by_id: Dict[str, Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    traffic_flows: List[Dict[str, Any]]
    deployments: List[Dict[str, Any]]
    external_mapping_summaries: List[Dict[str, Any]]
    dependency_hotspots_config: Dict[str, Any]
    report_count: int
    workload_count: int


def architecture_document_from_context(context: ArchitectureDocumentContext) -> Dict[str, Any]:
    collections = _sorted_architecture_collections(
        projects_by_id=context.projects_by_id,
        systems_by_id=context.systems_by_id,
        containers_by_id=context.containers_by_id,
        relationships=context.relationships,
        traffic_flows=context.traffic_flows,
    )
    relationship_statistics = build_relationship_statistics(
        collections["systems"],
        collections["containers"],
        collections["relationships"],
    )

    return {
        "schema_version": "1.0",
        "workspace": {
            "org": context.naming.org,
            "product": context.product_name,
            "default_env": context.naming.env or "prod",
            "generated_at": context.generated_at,
            "generator": context.generator,
            "source": {
                "tool": context.generator["tool"],
                "version": context.generator["version"],
                "rules_file": context.generator["rules_file"],
                "config_file": context.config_file,
            },
            "discovery": context.discovery_config,
        },
        "product": _product_entry(context.product_id, context.product_name, context.product_metadata),
        "projects": collections["projects"],
        "systems": collections["systems"],
        "containers": collections["containers"],
        "relationships": collections["relationships"],
        "relationship_statistics": relationship_statistics,
        "traffic_flows": collections["traffic_flows"],
        "deployments": context.deployments,
        "external_mappings": context.external_mapping_summaries,
        "dependency_hotspots": context.dependency_hotspots_config,
        "generation_hints": _generation_hints(
            context.report_count,
            context.workload_count,
            context.relationships,
            context.traffic_flows,
        ),
    }


def architecture_document(**document_options: Any) -> Dict[str, Any]:
    return architecture_document_from_context(
        ArchitectureDocumentContext(
            naming=document_options["naming"],
            product_id=document_options["product_id"],
            product_name=document_options["product_name"],
            product_metadata=document_options["product_metadata"],
            generated_at=document_options["generated_at"],
            generator=document_options["generator"],
            config_file=document_options["config_file"],
            discovery_config=document_options["discovery_config"],
            projects_by_id=document_options["projects_by_id"],
            systems_by_id=document_options["systems_by_id"],
            containers_by_id=document_options["containers_by_id"],
            relationships=document_options["relationships"],
            traffic_flows=document_options["traffic_flows"],
            deployments=document_options["deployments"],
            external_mapping_summaries=document_options["external_mapping_summaries"],
            dependency_hotspots_config=document_options["dependency_hotspots_config"],
            report_count=document_options["report_count"],
            workload_count=document_options["workload_count"],
        )
    )


def _sorted_architecture_collections(
    *,
    projects_by_id: Dict[str, Dict[str, Any]],
    systems_by_id: Dict[str, Dict[str, Any]],
    containers_by_id: Dict[str, Dict[str, Any]],
    relationships: List[Dict[str, Any]],
    traffic_flows: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    return {
        "projects": sorted(projects_by_id.values(), key=lambda item: item["id"]),
        "systems": sorted(systems_by_id.values(), key=lambda item: item["id"]),
        "containers": sorted(containers_by_id.values(), key=lambda item: item["id"]),
        "relationships": sorted(relationships, key=lambda item: item["id"]),
        "traffic_flows": sorted(traffic_flows, key=lambda item: item["id"]),
    }


def _product_entry(product_id: str, product_name: str, product_metadata: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": product_id,
        "name": product_name,
        "title": product_metadata.get("title") or product_name,
        "owner_team": product_metadata.get("owner_team", ""),
        "domain": product_metadata.get("domain", ""),
        "description": product_metadata.get("description", ""),
        "tags": list(product_metadata.get("tags", [])),
    }


def _generation_hints(
    report_count: int,
    workload_count: int,
    relationships: List[Dict[str, Any]],
    traffic_flows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "report_count": report_count,
        "workload_count": workload_count,
        "relationships_included": bool(relationships),
        "relationship_count": len(relationships),
        "traffic_flow_count": len(traffic_flows),
    }


__all__ = [
    "ArchitectureDocumentContext",
    "architecture_document",
    "architecture_document_from_context",
    "deployment_entries_from_envs",
    "traffic_flows_from_workloads",
]
