"""LikeC4 deployment rendering context helpers."""

from dataclasses import dataclass
from typing import Any, Dict, List

from .common import likec4_reference_map


@dataclass
class DeploymentRenderContext:
    projects_by_id: Dict[str, Dict[str, Any]]
    containers_by_id: Dict[str, Dict[str, Any]]
    systems_by_id: Dict[str, Dict[str, Any]]
    refs: Dict[str, str]
    traffic_flows: List[Dict[str, Any]]


def deployment_render_context(architecture: Dict[str, Any]) -> DeploymentRenderContext:
    return DeploymentRenderContext(
        projects_by_id={project.get("id"): project for project in architecture.get("projects") or []},
        containers_by_id={container.get("id"): container for container in architecture.get("containers") or []},
        systems_by_id={system.get("id"): system for system in architecture.get("systems") or []},
        refs=likec4_reference_map(architecture),
        traffic_flows=architecture.get("traffic_flows") or [],
    )


def has_scaling(runtime: Dict[str, Any]) -> bool:
    scaling_enabled = [str(value).lower() for value in runtime.get("scaling_enabled") or []]
    return "true" in scaling_enabled or any(
        runtime.get(key) for key in ("scaling_type", "min_replicas", "max_replicas", "scale_formula")
    )


__all__ = ["DeploymentRenderContext", "deployment_render_context", "has_scaling"]
