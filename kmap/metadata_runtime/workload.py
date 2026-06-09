"""Workload runtime metadata helpers."""

from typing import Any, Dict, Iterable, List, Tuple

from ..config import clean_metadata_string
from .common import (
    AUTOSCALING_METADATA_KEYS,
    OBSERVABILITY_METADATA_KEYS,
    WORKLOAD_BASE_METADATA_ITEMS,
    WORKLOAD_INSTANCE_RUNTIME_KEYS,
    WORKLOAD_SCHEDULING_METADATA_KEYS,
    WORKLOAD_SECURITY_METADATA_KEYS,
    WORKLOAD_STATUS_RUNTIME_KEYS,
    append_runtime_scalars,
    append_unique,
    joined_metadata_pairs,
    short_join_metadata,
)
from .container import workload_container_metadata_pairs


def workload_instance_runtime_metadata(svc: Dict[str, Any]) -> Dict[str, List[Any]]:
    runtime: Dict[str, List[Any]] = empty_runtime_metadata()

    append_unique(runtime["workload_kinds"], svc.get("kind"))
    for port in service_ports(svc):
        append_unique(runtime["service_ports"], port)
    for service in svc.get("services") or []:
        append_unique(runtime["services"], service)
    for ingress in svc.get("ingresses") or []:
        append_unique(runtime["ingresses"], ingress)

    append_runtime_scalars(runtime, svc.get("runtime") or {}, WORKLOAD_STATUS_RUNTIME_KEYS)
    append_runtime_scalars(runtime, svc.get("autoscaling") or {}, AUTOSCALING_METADATA_KEYS)
    apply_storage_runtime_metadata(runtime, svc.get("storage") or {})
    apply_observability_runtime_metadata(runtime, svc.get("observability") or {})
    apply_workload_security_runtime_metadata(runtime, svc.get("security") or {})
    apply_workload_scheduling_runtime_metadata(runtime, svc.get("scheduling") or {})
    return runtime


def apply_storage_runtime_metadata(runtime: Dict[str, List[Any]], storage: Dict[str, Any]) -> None:
    if not storage:
        return
    for key in ("storage_types", "persistent_volume_claims", "storage_classes", "storage_providers"):
        runtime.setdefault(key, [])
    for key, runtime_key in (
        ("volume_types", "storage_types"),
        ("storage_classes", "storage_classes"),
        ("storage_providers", "storage_providers"),
    ):
        for value in storage.get(key) or []:
            append_unique(runtime[runtime_key], value)
    for pvc in storage.get("persistent_volume_claims") or []:
        if isinstance(pvc, dict):
            append_unique(runtime["persistent_volume_claims"], pvc.get("name"))


def apply_observability_runtime_metadata(runtime: Dict[str, List[Any]], observability: Dict[str, Any]) -> None:
    if not observability:
        return
    for key in OBSERVABILITY_METADATA_KEYS:
        runtime.setdefault(key, [])
        for value in observability.get(key) or []:
            append_unique(runtime[key], value)


def apply_workload_security_runtime_metadata(runtime: Dict[str, List[Any]], security: Dict[str, Any]) -> None:
    if security:
        append_runtime_scalars(runtime, security, WORKLOAD_SECURITY_METADATA_KEYS)


def apply_workload_scheduling_runtime_metadata(runtime: Dict[str, List[Any]], scheduling: Dict[str, Any]) -> None:
    if scheduling:
        append_runtime_scalars(runtime, scheduling, WORKLOAD_SCHEDULING_METADATA_KEYS)


def workload_runtime_metadata_items(svc: Dict[str, Any]) -> List[Tuple[str, str]]:
    containers = svc.get("containers") or []
    runtime = svc.get("runtime") or {}
    items: List[Tuple[str, str]] = [
        (property_key, svc.get(source_key) or "") for property_key, source_key in WORKLOAD_BASE_METADATA_ITEMS
    ]
    if svc.get("release"):
        items.append(("helm_release", svc.get("release") or ""))

    items.extend(workload_container_metadata_pairs(containers))
    items.extend(workload_service_metadata_pairs(svc))
    items.extend(workload_storage_metadata_pairs(svc.get("storage") or {}))
    items.extend(workload_section_metadata_pairs(svc.get("observability") or {}, OBSERVABILITY_METADATA_KEYS))
    items.extend(workload_section_metadata_pairs(svc.get("security") or {}, WORKLOAD_SECURITY_METADATA_KEYS))
    items.extend(workload_section_metadata_pairs(svc.get("scheduling") or {}, WORKLOAD_SCHEDULING_METADATA_KEYS))
    items.extend(workload_status_metadata_pairs(runtime))

    return [(key, clean_metadata_string(value)) for key, value in items if clean_metadata_string(value)]


def empty_runtime_metadata() -> Dict[str, List[Any]]:
    return {key: [] for key in WORKLOAD_INSTANCE_RUNTIME_KEYS}


def service_ports(svc: Dict[str, Any]) -> List[str]:
    ports = []
    for entrypoint in svc.get("entrypoints") or []:
        port = entrypoint.get("port")
        protocol = clean_metadata_string(entrypoint.get("protocol")) or ""
        if port:
            ports.append(f"{port}/{protocol}" if protocol else str(port))
    return ports


def workload_service_metadata_pairs(svc: Dict[str, Any]) -> List[Tuple[str, str]]:
    return joined_metadata_pairs(
        {
            "service_ports": service_ports(svc),
            "services": svc.get("services") or [],
            "ingresses": svc.get("ingresses") or [],
        },
        (
            ("service_ports", "service_ports"),
            ("services", "services"),
            ("ingresses", "ingresses"),
        ),
    )


def workload_storage_metadata_pairs(storage: Dict[str, Any]) -> List[Tuple[str, str]]:
    pvc_names = [pvc.get("name") for pvc in storage.get("persistent_volume_claims") or [] if isinstance(pvc, dict)]
    return joined_metadata_pairs(
        {
            "storage_types": storage.get("volume_types") or [],
            "persistent_volume_claims": pvc_names,
            "storage_classes": storage.get("storage_classes") or [],
            "storage_providers": storage.get("storage_providers") or [],
        },
        (
            ("storage_types", "storage_types"),
            ("persistent_volume_claims", "persistent_volume_claims"),
            ("storage_classes", "storage_classes"),
            ("storage_providers", "storage_providers"),
        ),
    )


def workload_section_metadata_pairs(section: Dict[str, Any], keys: Iterable[str]) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []
    for key in keys:
        value = section.get(key)
        if isinstance(value, list):
            value = short_join_metadata(value, limit=8)
        items.append((key, value))
    return items


def workload_status_metadata_pairs(runtime: Dict[str, Any]) -> List[Tuple[str, str]]:
    return [(key, str(runtime[key])) for key in WORKLOAD_STATUS_RUNTIME_KEYS if runtime.get(key) is not None]


__all__ = [
    "apply_observability_runtime_metadata",
    "apply_storage_runtime_metadata",
    "apply_workload_scheduling_runtime_metadata",
    "apply_workload_security_runtime_metadata",
    "empty_runtime_metadata",
    "service_ports",
    "workload_instance_runtime_metadata",
    "workload_runtime_metadata_items",
    "workload_section_metadata_pairs",
    "workload_service_metadata_pairs",
    "workload_status_metadata_pairs",
    "workload_storage_metadata_pairs",
]
