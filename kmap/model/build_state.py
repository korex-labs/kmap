"""State objects used while building the normalized architecture model."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ConfigInputs:
    project_metadata: Dict[str, Any]
    config_namespace_projects: Dict[str, Any]
    system_naming_config: Dict[str, Any]
    dependency_hotspots_config: Dict[str, Any]
    discovery_config: Dict[str, Any]


@dataclass
class DependencyInputs:
    external_mappings: List[Dict[str, Any]]
    external_mapping_summaries: List[Dict[str, Any]]
    dependency_relations: List[Dict[str, Any]]


@dataclass
class ProductContext:
    naming: Any
    product_name: str
    product_id: str
    product_metadata: Dict[str, Any]
    generated_at: str
    generator: Dict[str, Any]
    env: str


@dataclass
class ModelBuildState:
    projects_by_id: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    systems_by_id: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    containers_by_id: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    deployments_by_env: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    workload_project_ids: Dict[str, str] = field(default_factory=dict)
    workload_primary_container_ids: Dict[str, str] = field(default_factory=dict)
    workload_primary_instance_ids: Dict[str, str] = field(default_factory=dict)
    workloads_by_service_id: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def deployment_for(self, env: str) -> Dict[str, Any]:
        return self.deployments_by_env.setdefault(env, {"env": env, "clusters": {}})


__all__ = ["ConfigInputs", "DependencyInputs", "ModelBuildState", "ProductContext"]
