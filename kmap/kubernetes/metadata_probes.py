"""Kubernetes container probe metadata."""

from typing import Any, Dict

from ..config import clean_metadata_string


def container_probe_inventory(container: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for probe_key, prefix in (
        ("readinessProbe", "readiness_probe"),
        ("livenessProbe", "liveness_probe"),
        ("startupProbe", "startup_probe"),
    ):
        summary = probe_summary((container or {}).get(probe_key) or {})
        if summary:
            out[prefix] = summary
    return out


def probe_summary(probe: Dict[str, Any]) -> str:
    if not probe:
        return ""
    http_get = probe.get("httpGet") or {}
    if http_get:
        return http_probe_summary(http_get)
    tcp_socket = probe.get("tcpSocket") or {}
    if tcp_socket:
        return port_probe_summary("tcp", tcp_socket)
    grpc = probe.get("grpc") or {}
    if grpc:
        return grpc_probe_summary(grpc)
    if probe.get("exec"):
        return "exec"
    return ""


def http_probe_summary(http_get: Dict[str, Any]) -> str:
    path = clean_metadata_string(http_get.get("path")) or "/"
    port = clean_metadata_string(http_get.get("port"))
    scheme = clean_metadata_string(http_get.get("scheme")) or "HTTP"
    return f"http {scheme.lower()} {path}:{port}" if port else f"http {scheme.lower()} {path}"


def port_probe_summary(kind: str, config: Dict[str, Any]) -> str:
    port = clean_metadata_string(config.get("port"))
    return f"{kind} {port}" if port else kind


def grpc_probe_summary(grpc: Dict[str, Any]) -> str:
    port = clean_metadata_string(grpc.get("port"))
    service = clean_metadata_string(grpc.get("service"))
    if port and service:
        return f"grpc {service}:{port}"
    return f"grpc {port}" if port else "grpc"


__all__ = [
    "container_probe_inventory",
    "grpc_probe_summary",
    "http_probe_summary",
    "port_probe_summary",
    "probe_summary",
]
