"""Workload container and deployment-instance entry construction."""

from dataclasses import dataclass
from typing import Any, Dict

from ...config import clean_metadata_string
from ...identifiers import architecture_id, architecture_id_part
from ...metadata import workload_instance_runtime_metadata
from ...naming import (
    display_title_from_discovered_name_with_context,
    short_hash,
    should_collapse_container_title_to_app,
)


@dataclass
class WorkloadContainerEntryOptions:
    container_id: str
    container: Dict[str, Any]
    product_id: str
    project_id: str
    system_id: str
    system_name: str
    project_name: str
    product_name: str
    product_metadata: Dict[str, Any]
    system_title: str
    system_element_type: str
    system_category: str
    raw_container_name: str


@dataclass
class WorkloadInstanceOptions:
    env: str
    project_name: str
    system_name: str
    svc: Dict[str, Any]
    raw_container_name: str
    container_id: str


def set_primary_workload_id(index: Dict[str, str], service_id: str, value: str) -> None:
    if service_id and service_id not in index:
        index[service_id] = value


def resolved_container_title(
    *,
    raw_container_name: str,
    product_name: str,
    project_name: str,
    product_metadata: Dict[str, Any],
    system_title: str,
    system_element_type: str,
    system_category: str,
) -> str:
    container_title = display_title_from_discovered_name_with_context(
        raw_container_name,
        product_name,
        project_name,
        product_metadata,
    )
    if should_collapse_container_title_to_app(system_element_type, system_category) and architecture_id_part(
        container_title
    ) == architecture_id_part(system_title):
        return "App"
    return container_title


def container_title(options: WorkloadContainerEntryOptions) -> str:
    return (
        resolved_container_title(
            raw_container_name=options.raw_container_name,
            product_name=options.product_name,
            project_name=options.project_name,
            product_metadata=options.product_metadata,
            system_title=options.system_title,
            system_element_type=options.system_element_type,
            system_category=options.system_category,
        )
        or options.raw_container_name
    )


def container_entry(options: WorkloadContainerEntryOptions) -> Dict[str, Any]:
    return {
        "id": options.container_id,
        "product_id": options.product_id,
        "project_id": options.project_id,
        "system_id": options.system_id,
        "name": f"{architecture_id_part(options.system_name)}_{architecture_id_part(options.raw_container_name)}",
        "title": container_title(options),
        "kind": options.container.get("kind") or "container",
        "technology": "",
        "tags": ["K8sWorkload", options.system_category],
        "discovery": {
            "clusters": [],
            "namespaces": [],
            "workloads": [],
        },
        "runtime": {},
        "name_source": {
            "kind": "rule",
            "rule": "system_plus_container_name",
            "raw_container_name": options.raw_container_name,
        },
    }


def record_container_discovery(
    container_entry: Dict[str, Any],
    svc: Dict[str, Any],
    namespace: str,
    cluster_name: str,
) -> None:
    for key, value in (
        ("clusters", cluster_name),
        ("namespaces", namespace),
        ("workloads", clean_metadata_string(svc.get("service_name"))),
    ):
        if value and value not in container_entry["discovery"][key]:
            container_entry["discovery"][key].append(value)


def append_workload_instance(namespace_entry: Dict[str, Any], options: WorkloadInstanceOptions) -> str:
    instance_id = architecture_id(
        "inst",
        options.env,
        options.project_name,
        options.system_name,
        options.raw_container_name,
        short_hash(options.svc.get("service_id") or options.raw_container_name, 8),
    )
    namespace_entry["instances"].append(
        workload_instance_entry(
            instance_id=instance_id,
            container_id=options.container_id,
            svc=options.svc,
            raw_container_name=options.raw_container_name,
        )
    )
    return instance_id


def workload_instance_entry(
    *,
    instance_id: str,
    container_id: str,
    svc: Dict[str, Any],
    raw_container_name: str,
) -> Dict[str, Any]:
    return {
        "id": instance_id,
        "container_id": container_id,
        "node_kind": "k8s_pod",
        "name": svc.get("service_name") or raw_container_name,
        "runtime": workload_instance_runtime_metadata(svc),
        "tags": ["Generated"],
    }


__all__ = [
    "WorkloadContainerEntryOptions",
    "WorkloadInstanceOptions",
    "append_workload_instance",
    "container_entry",
    "container_title",
    "record_container_discovery",
    "resolved_container_title",
    "set_primary_workload_id",
    "workload_instance_entry",
]
