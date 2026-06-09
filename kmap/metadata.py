"""Shared architecture metadata facade."""

from typing import Any, Dict

from .config import clean_metadata_string, slug_name
from .metadata_runtime import (
    RUNTIME_METADATA_ITEMS,
    _append_unique,
    apply_observability_runtime_metadata,
    apply_storage_runtime_metadata,
    apply_workload_scheduling_runtime_metadata,
    apply_workload_security_runtime_metadata,
    container_runtime_metadata_pairs,
    deployment_runtime_metadata_by_container_id,
    runtime_metadata_items,
    runtime_metadata_pairs,
    short_join_metadata,
    update_container_runtime_metadata,
    workload_instance_runtime_metadata,
    workload_runtime_metadata_items,
)


def merge_database_metadata(target: Dict[str, Any], database: Dict[str, Any]) -> None:
    if not database:
        return
    metadata = target.setdefault("metadata", {})
    db_meta = metadata.setdefault("database", {})
    if database.get("engine") and not db_meta.get("engine"):
        db_meta["engine"] = database.get("engine")
    for key in ("names", "source_vars", "sources"):
        merge_database_metadata_values(db_meta, key, database.get(key) or [])


def merge_database_metadata_values(db_meta: Dict[str, Any], key: str, source_values: list[Any]) -> None:
    values = db_meta.setdefault(key, [])
    for value in source_values:
        _append_unique(values, value)
    if not values:
        db_meta.pop(key, None)


def resource_property_key(key: str) -> str:
    normalized = slug_name(clean_metadata_string(key)).replace("-", "_")
    if not normalized:
        return "resource"
    if normalized[0].isdigit():
        normalized = f"resource_{normalized}"
    return normalized


__all__ = [
    "RUNTIME_METADATA_ITEMS",
    "apply_observability_runtime_metadata",
    "apply_storage_runtime_metadata",
    "apply_workload_scheduling_runtime_metadata",
    "apply_workload_security_runtime_metadata",
    "container_runtime_metadata_pairs",
    "deployment_runtime_metadata_by_container_id",
    "merge_database_metadata",
    "merge_database_metadata_values",
    "resource_property_key",
    "runtime_metadata_items",
    "runtime_metadata_pairs",
    "short_join_metadata",
    "update_container_runtime_metadata",
    "workload_instance_runtime_metadata",
    "workload_runtime_metadata_items",
]
