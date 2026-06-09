"""Shared runtime metadata constants and collection helpers."""

from typing import Any, Dict, Iterable, List, Tuple

from ..config import clean_metadata_string

OBSERVABILITY_METADATA_KEYS = (
    "prometheus_scrapes",
    "prometheus_paths",
    "prometheus_ports",
    "prometheus_schemes",
    "prometheus_sources",
    "otel_service_names",
    "otel_exporter_otlp_endpoints",
    "otel_env_vars",
)

CONTAINER_RESOURCE_METADATA_ITEMS = (
    ("container_cpu_requests", "request_cpu"),
    ("container_memory_requests", "request_memory"),
    ("container_cpu_limits", "limit_cpu"),
    ("container_memory_limits", "limit_memory"),
)

CONTAINER_PROBE_METADATA_ITEMS = (
    ("container_readiness_probes", "readiness_probe"),
    ("container_liveness_probes", "liveness_probe"),
    ("container_startup_probes", "startup_probe"),
)

CONTAINER_SECURITY_METADATA_ITEMS = (
    ("container_privileged", "security_privileged"),
    ("container_allow_privilege_escalation", "security_allow_privilege_escalation"),
    ("container_read_only_root_filesystem", "security_read_only_root_filesystem"),
    ("container_run_as_non_root", "security_run_as_non_root"),
    ("container_run_as_user", "security_run_as_user"),
    ("container_capabilities_add", "security_capabilities_add"),
    ("container_capabilities_drop", "security_capabilities_drop"),
)

WORKLOAD_SECURITY_METADATA_KEYS = (
    "service_account",
    "automount_service_account_token",
    "host_network",
    "host_pid",
    "host_ipc",
    "pod_run_as_non_root",
    "pod_run_as_user",
    "pod_fs_group",
    "pod_seccomp_profile",
)

WORKLOAD_SCHEDULING_METADATA_KEYS = (
    "priority_class",
    "scheduler_name",
    "runtime_class",
    "node_selector",
    "tolerations",
    "affinity",
    "topology_spread",
)

RUNTIME_METADATA_ITEMS = (
    ("workload_kinds", "workload_kinds"),
    ("service_ports", "service_ports"),
    ("services", "services"),
    ("ingresses", "ingresses"),
    ("replicas_desired", "replicas_desired"),
    ("replicas_ready", "replicas_ready"),
    ("replicas_available", "replicas_available"),
    ("running_pods", "running_pods"),
    ("scaling_enabled", "scaling_enabled"),
    ("scaling_type", "scaling_type"),
    ("min_replicas", "min_replicas"),
    ("max_replicas", "max_replicas"),
    ("scale_formula", "scale_formula"),
    ("storage_types", "storage_types"),
    ("persistent_volume_claims", "persistent_volume_claims"),
    ("storage_classes", "storage_classes"),
    ("storage_providers", "storage_providers"),
    *(
        (key, key)
        for key in OBSERVABILITY_METADATA_KEYS + WORKLOAD_SECURITY_METADATA_KEYS + WORKLOAD_SCHEDULING_METADATA_KEYS
    ),
)

WORKLOAD_INSTANCE_RUNTIME_KEYS = (
    "workload_kinds",
    "service_ports",
    "services",
    "ingresses",
    "replicas_desired",
    "replicas_ready",
    "replicas_available",
    "running_pods",
    "scaling_enabled",
    "scaling_type",
    "min_replicas",
    "max_replicas",
    "scale_formula",
)

WORKLOAD_STATUS_RUNTIME_KEYS = (
    "replicas_desired",
    "replicas_ready",
    "replicas_available",
    "running_pods",
)

AUTOSCALING_METADATA_KEYS = (
    "scaling_enabled",
    "scaling_type",
    "min_replicas",
    "max_replicas",
    "scale_formula",
)

WORKLOAD_BASE_METADATA_ITEMS = (
    ("cluster", "cluster"),
    ("namespace", "namespace"),
    ("workload", "service_name"),
    ("workload_kind", "kind"),
)


def short_join_metadata(values: Iterable[Any], limit: int = 5) -> str:
    cleaned = [clean_metadata_string(value) for value in values if clean_metadata_string(value)]
    unique = []
    seen = set()
    for value in cleaned:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(value)
    if len(unique) <= limit:
        return ", ".join(unique)
    return ", ".join(unique[:limit]) + f", +{len(unique) - limit} more"


def append_unique(items: List[Any], value: Any) -> None:
    if value is None:
        return
    if isinstance(value, str):
        value = clean_metadata_string(value)
        if not value:
            return
    if value not in items:
        items.append(value)


def append_runtime_scalars(runtime: Dict[str, List[Any]], source: Dict[str, Any], keys: Iterable[str]) -> None:
    for key in keys:
        append_unique(runtime.setdefault(key, []), source.get(key))


def append_clean_unique(values: List[str], value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            append_clean_unique(values, item)
        return
    text = clean_metadata_string(value)
    if text and text not in values:
        values.append(text)


def joined_metadata_pairs(
    source: Dict[str, Any],
    metadata_items: Iterable[Tuple[str, str]],
    *,
    limit: int = 8,
) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for source_key, property_key in metadata_items:
        value = short_join_metadata(source.get(source_key) or [], limit=limit)
        if value:
            pairs.append((property_key, value))
    return pairs


def runtime_metadata_pairs(runtime: Dict[str, Any]) -> List[Tuple[str, str]]:
    return joined_metadata_pairs(runtime, RUNTIME_METADATA_ITEMS)


__all__ = [
    "AUTOSCALING_METADATA_KEYS",
    "CONTAINER_PROBE_METADATA_ITEMS",
    "CONTAINER_RESOURCE_METADATA_ITEMS",
    "CONTAINER_SECURITY_METADATA_ITEMS",
    "OBSERVABILITY_METADATA_KEYS",
    "RUNTIME_METADATA_ITEMS",
    "WORKLOAD_BASE_METADATA_ITEMS",
    "WORKLOAD_INSTANCE_RUNTIME_KEYS",
    "WORKLOAD_SCHEDULING_METADATA_KEYS",
    "WORKLOAD_SECURITY_METADATA_KEYS",
    "WORKLOAD_STATUS_RUNTIME_KEYS",
    "append_clean_unique",
    "append_runtime_scalars",
    "append_unique",
    "joined_metadata_pairs",
    "runtime_metadata_pairs",
    "short_join_metadata",
]
