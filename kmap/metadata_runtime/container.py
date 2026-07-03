"""Container runtime metadata helpers."""

from typing import Any, Dict, List, Tuple

from .common import (
    CONTAINER_PROBE_METADATA_ITEMS,
    CONTAINER_RESOURCE_METADATA_ITEMS,
    CONTAINER_SECURITY_METADATA_ITEMS,
    append_unique,
    joined_metadata_pairs,
    short_join_metadata,
)


def runtime_metadata_items(container: Dict[str, Any]) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []

    database = ((container.get("metadata") or {}).get("database")) or {}
    if database.get("engine"):
        items.append(("database_engine", database.get("engine")))
    db_names = short_join_metadata(database.get("names") or [], limit=8)
    if db_names:
        items.append(("databases", db_names))

    return items


def container_runtime_metadata_pairs(container: Dict[str, Any]) -> List[Tuple[str, str]]:
    runtime = container.get("runtime") or {}
    items: List[Tuple[str, str]] = []
    for source_key, property_key in container_runtime_property_items():
        value = short_join_metadata(runtime.get(source_key) or [], limit=8)
        if value:
            items.append((property_key, value))

    name_source = container.get("name_source") or {}
    if name_source.get("raw_container_name"):
        items.append(("container_source", name_source.get("raw_container_name")))
    return items


def update_container_runtime_metadata(
    container_entry: Dict[str, Any], svc: Dict[str, Any], container: Dict[str, Any]
) -> None:
    _ = svc
    runtime = container_entry.setdefault("runtime", {})
    for key in (
        "container_kinds",
        "images",
        "container_ports",
    ):
        runtime.setdefault(key, [])

    append_unique(runtime["container_kinds"], container.get("kind"))
    append_unique(runtime["images"], container.get("image"))
    for port in container.get("ports") or []:
        append_unique(runtime["container_ports"], port)
    for runtime_key, container_key in container_inventory_metadata_items():
        if container.get(container_key):
            append_unique(runtime.setdefault(runtime_key, []), container.get(container_key))


def container_inventory_metadata_items() -> Tuple[Tuple[str, str], ...]:
    return CONTAINER_RESOURCE_METADATA_ITEMS + CONTAINER_PROBE_METADATA_ITEMS + CONTAINER_SECURITY_METADATA_ITEMS


def container_runtime_property_items() -> Tuple[Tuple[str, str], ...]:
    return (
        ("images", "container_images"),
        ("container_ports", "container_ports"),
        *((runtime_key, runtime_key) for runtime_key, _ in container_inventory_metadata_items()),
    )


def workload_container_metadata_pairs(containers: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
    metadata: Dict[str, List[Any]] = {
        "images": [container.get("image") for container in containers if container.get("image")],
        "container_ports": [port for container in containers for port in (container.get("ports") or []) if port],
    }
    for runtime_key, container_key in container_inventory_metadata_items():
        metadata[runtime_key] = [
            container.get(container_key) for container in containers if container.get(container_key)
        ]
    return joined_metadata_pairs(metadata, container_runtime_property_items())


__all__ = [
    "container_inventory_metadata_items",
    "container_runtime_metadata_pairs",
    "container_runtime_property_items",
    "runtime_metadata_items",
    "update_container_runtime_metadata",
    "workload_container_metadata_pairs",
]
