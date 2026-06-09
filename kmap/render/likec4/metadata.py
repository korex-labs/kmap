"""LikeC4 metadata presentation helpers."""

from collections.abc import Iterable
from typing import Tuple

from .metadata_summaries import (
    database_summary,
    network_summary,
    observability_summary,
    probes_summary,
    resources_summary,
    runtime_summary,
    scaling_summary,
    scheduling_summary,
    security_summary,
    storage_summary,
)
from .metadata_values import (
    MetadataItems,
    append_summary,
    first,
    metadata_map,
    preserved_items,
)

LIKEC4_METADATA_RESERVED_KEYS = {
    "as",
    "autoLayout",
    "component",
    "container",
    "deployment",
    "deploymentNode",
    "dynamic",
    "element",
    "extend",
    "global",
    "group",
    "include",
    "model",
    "person",
    "relationship",
    "source",
    "specification",
    "storage",
    "style",
    "system",
    "target",
    "view",
    "views",
}


def grouped_container_metadata_items(items: Iterable[Tuple[str, str]]) -> MetadataItems:
    """Collapse verbose runtime keys into compact LikeC4 property rows."""
    return grouped_runtime_metadata_items(items)


def grouped_runtime_metadata_items(
    items: Iterable[Tuple[str, str]], preserve_keys: Iterable[str] = ()
) -> MetadataItems:
    """Collapse verbose runtime keys while preserving selected structural rows."""
    metadata = metadata_map(items)
    grouped = preserved_items(metadata, preserve_keys)

    append_summary(grouped, "ops_database", database_summary(metadata))
    append_summary(grouped, "container_image", first(metadata, "container_images"))
    append_summary(grouped, "ops_network", network_summary(metadata))
    append_summary(grouped, "ops_observability", observability_summary(metadata))
    append_summary(grouped, "ops_probes", probes_summary(metadata))
    append_summary(grouped, "ops_resources", resources_summary(metadata))
    append_summary(grouped, "ops_runtime", runtime_summary(metadata))
    append_summary(grouped, "ops_scaling", scaling_summary(metadata))
    append_summary(grouped, "ops_scheduling", scheduling_summary(metadata))
    append_summary(grouped, "ops_security", security_summary(metadata))
    append_summary(grouped, "container_source", first(metadata, "container_source"))
    append_summary(grouped, "ops_storage", storage_summary(metadata))

    return grouped


__all__ = [
    "LIKEC4_METADATA_RESERVED_KEYS",
    "grouped_container_metadata_items",
    "grouped_runtime_metadata_items",
]
