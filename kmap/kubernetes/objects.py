"""Kubernetes object extraction helpers."""

import re
from typing import Any, Dict, List

from ..config import clean_metadata_string
from .data import configmap_data, decode_secret_data
from .metadata import (
    affinity_summary,
    container_probe_inventory,
    container_resource_inventory,
    container_security_inventory,
    probe_summary,
    scheduling_map_summary,
    toleration_summaries,
    topology_spread_summary,
    workload_scheduling_context,
    workload_security_context,
)

APP_SERVICE_ANNOTATION = "app_service"


def obj_name(obj: Dict[str, Any]) -> str:
    return (((obj or {}).get("metadata") or {}).get("name")) or ""


def labels_of(obj: Dict[str, Any]) -> Dict[str, str]:
    return (((obj or {}).get("metadata") or {}).get("labels")) or {}


def annotations_of(obj: Dict[str, Any]) -> Dict[str, str]:
    return (((obj or {}).get("metadata") or {}).get("annotations")) or {}


def pod_template_annotations_of(obj: Dict[str, Any]) -> Dict[str, str]:
    tpl = (((obj or {}).get("spec") or {}).get("template") or {}).get("metadata") or {}
    return tpl.get("annotations") or {}


def workload_app_service(workload: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    metadata_annotations = annotations_of(workload)
    value = clean_metadata_string(metadata_annotations.get(APP_SERVICE_ANNOTATION))
    if value:
        return value, app_service_source(f"metadata.annotations.{APP_SERVICE_ANNOTATION}")

    template_annotations = pod_template_annotations_of(workload)
    value = clean_metadata_string(template_annotations.get(APP_SERVICE_ANNOTATION))
    if value:
        return value, app_service_source(f"spec.template.metadata.annotations.{APP_SERVICE_ANNOTATION}")

    return "", app_service_source("", fallback_used=True)


def app_service_source(path: str, *, fallback_used: bool = False) -> Dict[str, Any]:
    return {
        "kind": "fallback" if fallback_used else "annotation",
        "key": APP_SERVICE_ANNOTATION,
        "path": path,
        "fallback_used": fallback_used,
    }


def container_inventory(containers: List[Dict[str, Any]], kind: str) -> List[Dict[str, Any]]:
    out = []
    for container in containers or []:
        name = clean_metadata_string(container.get("name"))
        if not name:
            continue
        out.append(
            {
                "name": name,
                "kind": kind,
                "image": clean_metadata_string(container.get("image")),
                "ports": container_port_labels(container),
                **container_resource_inventory(container),
                **container_probe_inventory(container),
                **container_security_inventory(container),
            }
        )
    return out


def container_port_labels(container: Dict[str, Any]) -> List[str]:
    ports = []
    for port in container.get("ports") or []:
        container_port = port.get("containerPort")
        if not container_port:
            continue
        protocol = clean_metadata_string(port.get("protocol")) or "TCP"
        port_name = clean_metadata_string(port.get("name"))
        label = f"{container_port}/{protocol}"
        if port_name:
            label = f"{port_name}:{label}"
        ports.append(label)
    return ports


def selector_of_workload(obj: Dict[str, Any]) -> Dict[str, str]:
    spec = (obj or {}).get("spec") or {}
    sel = (spec.get("selector") or {}).get("matchLabels") or {}
    return {str(k): str(v) for k, v in sel.items() if k and v}


def pod_labels_from_template(obj: Dict[str, Any]) -> Dict[str, str]:
    tpl = (((obj or {}).get("spec") or {}).get("template") or {}).get("metadata") or {}
    return tpl.get("labels") or {}


def service_selector(obj: Dict[str, Any]) -> Dict[str, str]:
    return (((obj or {}).get("spec") or {}).get("selector")) or {}


def dict_contains(big: Dict[str, str], small: Dict[str, str]) -> bool:
    if not small:
        return False
    return all(big.get(k) == v for k, v in small.items())


def item_map(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {obj_name(x): x for x in (data.get("items") or []) if obj_name(x)}


def workload_runtime_status(workload: Dict[str, Any], pods: List[Dict[str, Any]]) -> Dict[str, Any]:
    spec = workload.get("spec") or {}
    status = workload.get("status") or {}
    out: Dict[str, Any] = {
        "running_pods": len(pods or []),
    }

    desired = first_present_value(spec, status, "replicas", "desiredNumberScheduled")
    if desired is not None:
        out["replicas_desired"] = desired

    ready = first_present_value(status, status, "readyReplicas", "numberReady")
    if ready is not None:
        out["replicas_ready"] = ready

    available = first_present_value(status, status, "availableReplicas", "numberAvailable")
    if available is not None:
        out["replicas_available"] = available

    return out


def first_present_value(primary: Dict[str, Any], fallback: Dict[str, Any], primary_key: str, fallback_key: str) -> Any:
    value = primary.get(primary_key)
    return fallback.get(fallback_key) if value is None else value


def find_related_workloads(kind_data: Dict[str, Any], match_re: re.Pattern) -> List[Dict[str, Any]]:
    return [item for item in kind_data.get("items") or [] if obj_name(item) and match_re.search(obj_name(item))]


def workload_service_id(cluster: str, namespace: str, kind: str, name: str) -> str:
    raw = f"{cluster}:{namespace}:{kind}:{name}"
    return re.sub(r"[^A-Za-z0-9_.:-]+", "_", raw)


__all__ = [
    "affinity_summary",
    "annotations_of",
    "app_service_source",
    "configmap_data",
    "container_inventory",
    "container_port_labels",
    "container_probe_inventory",
    "container_resource_inventory",
    "container_security_inventory",
    "decode_secret_data",
    "dict_contains",
    "find_related_workloads",
    "first_present_value",
    "item_map",
    "labels_of",
    "obj_name",
    "pod_labels_from_template",
    "pod_template_annotations_of",
    "probe_summary",
    "scheduling_map_summary",
    "selector_of_workload",
    "service_selector",
    "toleration_summaries",
    "topology_spread_summary",
    "workload_app_service",
    "workload_runtime_status",
    "workload_scheduling_context",
    "workload_security_context",
    "workload_service_id",
]
