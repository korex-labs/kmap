"""Context objects used while rendering LikeC4 model files."""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from ...metadata import (
    container_runtime_metadata_pairs,
    deployment_runtime_metadata_by_container_id,
    runtime_metadata_items,
)
from .metadata import grouped_container_metadata_items


@dataclass
class LikeC4ModelContext:
    project_by_id: Dict[str, Dict[str, Any]]
    deployment_metadata_by_container_id: Dict[str, List[Tuple[str, str]]]
    containers_by_system: Dict[str, List[Dict[str, Any]]]


def likec4_model_context(architecture: Dict[str, Any]) -> LikeC4ModelContext:
    containers_by_system: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for container in architecture.get("containers") or []:
        containers_by_system[container.get("system_id") or ""].append(container)
    return LikeC4ModelContext(
        project_by_id={project.get("id"): project for project in architecture.get("projects") or []},
        deployment_metadata_by_container_id=deployment_runtime_metadata_by_container_id(architecture),
        containers_by_system=containers_by_system,
    )


def container_metadata_items(
    container: Dict[str, Any],
    context: LikeC4ModelContext,
) -> List[Tuple[str, str]]:
    metadata_items = runtime_metadata_items(container)
    metadata_items.extend(container_runtime_metadata_pairs(container))
    metadata_items.extend(context.deployment_metadata_by_container_id.get(container.get("id") or "") or [])
    return grouped_container_metadata_items(metadata_items)


__all__ = [
    "LikeC4ModelContext",
    "container_metadata_items",
    "likec4_model_context",
]
