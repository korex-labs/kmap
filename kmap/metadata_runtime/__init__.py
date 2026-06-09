"""Runtime metadata aggregation helpers."""

from .common import (
    CONTAINER_PROBE_METADATA_ITEMS,
    CONTAINER_RESOURCE_METADATA_ITEMS,
    CONTAINER_SECURITY_METADATA_ITEMS,
    OBSERVABILITY_METADATA_KEYS,
    RUNTIME_METADATA_ITEMS,
    WORKLOAD_SCHEDULING_METADATA_KEYS,
    WORKLOAD_SECURITY_METADATA_KEYS,
    runtime_metadata_pairs,
    short_join_metadata,
)
from .common import (
    append_unique as _append_unique,
)
from .container import (
    container_runtime_metadata_pairs,
    runtime_metadata_items,
    update_container_runtime_metadata,
)
from .deployment import deployment_runtime_metadata_by_container_id
from .workload import (
    apply_observability_runtime_metadata,
    apply_storage_runtime_metadata,
    apply_workload_scheduling_runtime_metadata,
    apply_workload_security_runtime_metadata,
    workload_instance_runtime_metadata,
    workload_runtime_metadata_items,
)

__all__ = [
    "CONTAINER_PROBE_METADATA_ITEMS",
    "CONTAINER_RESOURCE_METADATA_ITEMS",
    "CONTAINER_SECURITY_METADATA_ITEMS",
    "OBSERVABILITY_METADATA_KEYS",
    "RUNTIME_METADATA_ITEMS",
    "WORKLOAD_SCHEDULING_METADATA_KEYS",
    "WORKLOAD_SECURITY_METADATA_KEYS",
    "_append_unique",
    "apply_observability_runtime_metadata",
    "apply_storage_runtime_metadata",
    "apply_workload_scheduling_runtime_metadata",
    "apply_workload_security_runtime_metadata",
    "container_runtime_metadata_pairs",
    "deployment_runtime_metadata_by_container_id",
    "runtime_metadata_items",
    "runtime_metadata_pairs",
    "short_join_metadata",
    "update_container_runtime_metadata",
    "workload_instance_runtime_metadata",
    "workload_runtime_metadata_items",
]
