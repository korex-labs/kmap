"""Deployment runtime metadata aggregation."""

from typing import Any, Dict, Iterable, List, Tuple

from ..config import clean_metadata_string
from .common import RUNTIME_METADATA_ITEMS, append_clean_unique, short_join_metadata


def deployment_runtime_metadata_by_container_id(architecture: Dict[str, Any]) -> Dict[str, List[Tuple[str, str]]]:
    by_container: Dict[str, Dict[str, List[str]]] = {}
    for instance in deployment_instances(architecture):
        container_id = clean_metadata_string(instance.get("container_id"))
        runtime = instance.get("runtime") or {}
        if not container_id or not runtime:
            continue
        append_runtime_metadata_items(by_container.setdefault(container_id, {}), runtime)
    return runtime_metadata_result(by_container)


def deployment_instances(architecture: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for deployment in architecture.get("deployments") or []:
        for cluster in deployment.get("clusters") or []:
            for namespace in cluster.get("namespaces") or []:
                yield from namespace.get("instances") or []


def append_runtime_metadata_items(target: Dict[str, List[str]], runtime: Dict[str, Any]) -> None:
    for source_key, property_key in RUNTIME_METADATA_ITEMS:
        for value in runtime.get(source_key) or []:
            append_clean_unique(target.setdefault(property_key, []), value)


def runtime_metadata_result(
    metadata_by_container: Dict[str, Dict[str, List[str]]],
) -> Dict[str, List[Tuple[str, str]]]:
    result: Dict[str, List[Tuple[str, str]]] = {}
    for container_id, metadata in metadata_by_container.items():
        items: List[Tuple[str, str]] = []
        for key, values in metadata.items():
            value = short_join_metadata(values, limit=8)
            if value:
                items.append((key, value))
        result[container_id] = items
    return result


__all__ = [
    "append_runtime_metadata_items",
    "deployment_instances",
    "deployment_runtime_metadata_by_container_id",
    "runtime_metadata_result",
]
