"""Runtime metadata summary helpers for LikeC4 output."""

from .metadata_values import MetadataMap, field, first, summary


def database_summary(metadata: MetadataMap) -> str:
    engine = first(metadata, "database_engine")
    databases = first(metadata, "databases")
    if engine and databases:
        return f"{engine}: {databases}"
    return engine or databases


def network_summary(metadata: MetadataMap) -> str:
    return summary(
        (
            field(metadata, "services", "services"),
            field(metadata, "ingresses", "ingresses"),
            field(metadata, "service_ports", "service ports"),
            field(metadata, "container_ports", "container ports"),
        )
    )


def observability_summary(metadata: MetadataMap) -> str:
    prometheus = summary(
        (
            field(metadata, "prometheus_scrapes", "prometheus"),
            field(metadata, "prometheus_paths", "paths"),
            field(metadata, "prometheus_ports", "ports"),
            field(metadata, "prometheus_schemes", "schemes"),
            field(metadata, "prometheus_sources", "sources"),
        )
    )
    otel = summary(
        (
            field(metadata, "otel_service_names", "otel services"),
            field(metadata, "otel_exporter_otlp_endpoints", "otel endpoints"),
            field(metadata, "otel_env_vars", "otel env"),
        )
    )
    return summary((prometheus, otel))


def resources_summary(metadata: MetadataMap) -> str:
    cpu = request_limit_summary(metadata, "container_cpu_requests", "container_cpu_limits")
    memory = request_limit_summary(metadata, "container_memory_requests", "container_memory_limits")
    return summary((f"cpu {cpu}" if cpu else "", f"memory {memory}" if memory else ""))


def probes_summary(metadata: MetadataMap) -> str:
    return summary(
        (
            field(metadata, "container_readiness_probes", "readiness"),
            field(metadata, "container_liveness_probes", "liveness"),
            field(metadata, "container_startup_probes", "startup"),
        )
    )


def request_limit_summary(metadata: MetadataMap, request_key: str, limit_key: str) -> str:
    request = first(metadata, request_key)
    limit = first(metadata, limit_key)
    if request and limit:
        return f"{request}/{limit}"
    return request or limit


def runtime_summary(metadata: MetadataMap) -> str:
    replicas = summary(
        (
            field(metadata, "replicas_desired", "desired"),
            field(metadata, "replicas_ready", "ready"),
            field(metadata, "replicas_available", "available"),
            field(metadata, "running_pods", "running"),
        )
    )
    return summary((field(metadata, "workload_kinds", "workloads"), f"replicas {replicas}" if replicas else ""))


def scaling_summary(metadata: MetadataMap) -> str:
    return summary(
        (
            field(metadata, "scaling_enabled", "enabled"),
            field(metadata, "scaling_type", "type"),
            field(metadata, "min_replicas", "min"),
            field(metadata, "max_replicas", "max"),
            field(metadata, "scale_formula", "formula"),
        )
    )


def scheduling_summary(metadata: MetadataMap) -> str:
    return summary(
        (
            field(metadata, "priority_class", "priority"),
            field(metadata, "scheduler_name", "scheduler"),
            field(metadata, "runtime_class", "runtime class"),
            field(metadata, "node_selector", "node selector"),
            field(metadata, "tolerations", "tolerations"),
            field(metadata, "affinity", "affinity"),
            field(metadata, "topology_spread", "topology spread"),
        )
    )


def security_summary(metadata: MetadataMap) -> str:
    return summary(
        (
            field(metadata, "service_account", "service account"),
            field(metadata, "automount_service_account_token", "automount token"),
            field(metadata, "host_network", "host network"),
            field(metadata, "host_pid", "host pid"),
            field(metadata, "host_ipc", "host ipc"),
            field(metadata, "pod_run_as_non_root", "pod non-root"),
            field(metadata, "pod_run_as_user", "pod user"),
            field(metadata, "pod_fs_group", "pod fs group"),
            field(metadata, "pod_seccomp_profile", "pod seccomp"),
            field(metadata, "container_privileged", "privileged"),
            field(metadata, "container_allow_privilege_escalation", "allow privilege escalation"),
            field(metadata, "container_read_only_root_filesystem", "read-only root fs"),
            field(metadata, "container_run_as_non_root", "container non-root"),
            field(metadata, "container_run_as_user", "container user"),
            field(metadata, "container_capabilities_add", "cap add"),
            field(metadata, "container_capabilities_drop", "cap drop"),
        )
    )


def storage_summary(metadata: MetadataMap) -> str:
    return summary(
        (
            field(metadata, "storage_types", "types"),
            field(metadata, "persistent_volume_claims", "pvcs"),
            field(metadata, "storage_classes", "classes"),
            field(metadata, "storage_providers", "providers"),
        )
    )


__all__ = [
    "database_summary",
    "network_summary",
    "observability_summary",
    "probes_summary",
    "resources_summary",
    "runtime_summary",
    "scaling_summary",
    "scheduling_summary",
    "security_summary",
    "storage_summary",
]
