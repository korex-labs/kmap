"""Kubernetes service and pod matching helpers."""

from typing import Any, Dict, List, Optional

from .objects import (
    dict_contains,
    labels_of,
    obj_name,
    pod_labels_from_template,
    selector_of_workload,
    service_selector,
)


def workload_pods(pods_data: Dict[str, Any], workload: Dict[str, Any]) -> List[Dict[str, Any]]:
    selector = selector_of_workload(workload) or pod_labels_from_template(workload)
    if not selector:
        return []
    out = []
    for pod in pods_data.get("items") or []:
        phase = ((pod.get("status") or {}).get("phase")) or ""
        if phase == "Running" and dict_contains(labels_of(pod), selector):
            out.append(pod)
    return out


def service_matches_workload(service: Dict[str, Any], workload: Dict[str, Any]) -> bool:
    selector = service_selector(service)
    if not selector:
        return False
    labels = pod_labels_from_template(workload) or selector_of_workload(workload)
    return dict_contains(labels, selector)


def service_entrypoints(service: Dict[str, Any], namespace: str) -> List[Dict[str, Any]]:
    spec = service.get("spec") or {}
    name = obj_name(service)
    cluster_ip = spec.get("clusterIP")
    aliases = alias_variants(name, namespace, cluster_ip if isinstance(cluster_ip, str) else None)
    return service_entrypoints_for_aliases(name, spec.get("ports") or [], aliases)


def alias_variants(name: str, namespace: str, cluster_ip: Optional[str] = None) -> List[str]:
    values = {
        name.lower(),
        f"{name}.{namespace}".lower(),
        f"{name}.{namespace}.svc".lower(),
        f"{name}.{namespace}.svc.cluster.local".lower(),
    }
    if cluster_ip:
        values.add(cluster_ip.lower())
    return sorted(value for value in values if value)


def service_entrypoints_for_aliases(
    service_name: str,
    ports: List[Dict[str, Any]],
    aliases: List[str],
) -> List[Dict[str, Any]]:
    if ports:
        return [
            service_entrypoint(
                service_name,
                alias,
                port.get("port"),
                port.get("protocol") or "TCP",
                port.get("targetPort"),
            )
            for port in ports
            for alias in aliases
        ]
    return [service_entrypoint(service_name, alias, None, None, None) for alias in aliases]


def service_entrypoint(
    service_name: str,
    alias: str,
    port: Any,
    protocol: Optional[str],
    target_port: Any,
) -> Dict[str, Any]:
    return {
        "type": "Service",
        "name": service_name,
        "endpoint": f"{alias}:{port}" if port else alias,
        "host": alias,
        "port": port,
        "protocol": protocol,
        "targetPort": target_port,
    }


__all__ = [
    "alias_variants",
    "service_entrypoint",
    "service_entrypoints",
    "service_entrypoints_for_aliases",
    "service_matches_workload",
    "workload_pods",
]
