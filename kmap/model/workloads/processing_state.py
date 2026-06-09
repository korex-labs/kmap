"""State objects for workload processing."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class WorkloadInputs:
    svc: Dict[str, Any]
    naming: Any
    product_name: str
    product_id: str
    product_metadata: Dict[str, Any]
    project_metadata: Dict[str, Dict[str, Any]]
    config_namespace_projects: Dict[str, str]
    system_naming_config: Dict[str, Any]
    env: str
    deployment: Dict[str, Any]

    @classmethod
    def from_kwargs(cls, kwargs: Dict[str, Any]) -> "WorkloadInputs":
        return cls(
            svc=kwargs["svc"],
            naming=kwargs["naming"],
            product_name=kwargs["product_name"],
            product_id=kwargs["product_id"],
            product_metadata=kwargs["product_metadata"],
            project_metadata=kwargs["project_metadata"],
            config_namespace_projects=kwargs["config_namespace_projects"],
            system_naming_config=kwargs["system_naming_config"],
            env=kwargs["env"],
            deployment=kwargs["deployment"],
        )


@dataclass
class ModelIndexes:
    projects_by_id: Dict[str, Dict[str, Any]]
    systems_by_id: Dict[str, Dict[str, Any]]
    containers_by_id: Dict[str, Dict[str, Any]]
    workload_project_ids: Dict[str, str]
    workload_primary_container_ids: Dict[str, str]
    workload_primary_instance_ids: Dict[str, str]
    workloads_by_service_id: Dict[str, Dict[str, Any]]

    @classmethod
    def from_kwargs(cls, kwargs: Dict[str, Any]) -> "ModelIndexes":
        return cls(
            projects_by_id=kwargs["projects_by_id"],
            systems_by_id=kwargs["systems_by_id"],
            containers_by_id=kwargs["containers_by_id"],
            workload_project_ids=kwargs["workload_project_ids"],
            workload_primary_container_ids=kwargs["workload_primary_container_ids"],
            workload_primary_instance_ids=kwargs["workload_primary_instance_ids"],
            workloads_by_service_id=kwargs["workloads_by_service_id"],
        )


@dataclass
class WorkloadContext:
    service_id: str
    namespace: str
    project_name: str
    project_id: str
    project: Dict[str, Any]
    project_meta: Dict[str, Any]
    system_name: str
    system_name_source: Dict[str, Any]
    system_id: str
    system_title: str
    system_category: str
    system_element_type: str


@dataclass
class ContainerProcessContext:
    container: Dict[str, Any]
    cluster_name: str
    namespace_entry: Dict[str, Any]


__all__ = ["ContainerProcessContext", "ModelIndexes", "WorkloadContext", "WorkloadInputs"]
