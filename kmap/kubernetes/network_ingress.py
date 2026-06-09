"""Kubernetes ingress extraction helpers."""

from typing import Any, Dict, List, Tuple

from ..config import clean_metadata_string
from .objects import obj_name


def ingress_services(ingress: Dict[str, Any]) -> List[str]:
    out = []
    spec = ingress.get("spec") or {}
    default_backend = spec.get("defaultBackend") or {}
    service = backend_service_name(default_backend)
    if service:
        out.append(service)
    for _host, path in ingress_http_paths(spec):
        service = backend_service_name(path.get("backend") or {})
        if service:
            out.append(service)
    return out


def ingress_routes(ingress: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    spec = ingress.get("spec") or {}
    ingress_name = obj_name(ingress)
    default_backend = spec.get("defaultBackend") or {}
    if default_backend:
        append_ingress_route(out, ingress_name, "", "/", default_backend)
    for host, path in ingress_http_paths(spec):
        append_ingress_route(out, ingress_name, host, path.get("path") or "/", path.get("backend") or {})
    return out


def append_ingress_route(
    routes: List[Dict[str, Any]],
    ingress_name: str,
    host: str,
    path: str,
    backend: Dict[str, Any],
) -> None:
    route = ingress_route(ingress_name, host, path, backend)
    if route:
        routes.append(route)


def ingress_http_paths(spec: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    out = []
    for rule in spec.get("rules") or []:
        host = rule.get("host") or ""
        http = rule.get("http") or {}
        out.extend((host, path) for path in http.get("paths") or [])
    return out


def ingress_route(ingress_name: str, host: str, path: str, backend: Dict[str, Any]) -> Dict[str, Any]:
    service_name = backend_service_name(backend)
    if not service_name:
        return {}
    return {
        "ingress": ingress_name,
        "host": clean_metadata_string(host).lower(),
        "path": clean_metadata_string(path) or "/",
        "service": service_name,
        "service_port": backend_service_port(backend),
    }


def backend_service(backend: Dict[str, Any]) -> Dict[str, Any]:
    return ((backend or {}).get("service")) or {}


def backend_service_name(backend: Dict[str, Any]) -> str:
    return backend_service(backend).get("name") or ""


def backend_service_port(backend: Dict[str, Any]) -> Any:
    port = backend_service(backend).get("port") or {}
    return port.get("number") or port.get("name")


def ingress_entrypoints(ingress: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for rule in (ingress.get("spec") or {}).get("rules") or []:
        host = (rule.get("host") or "").strip().lower()
        if not host:
            continue
        out.append(
            {
                "type": "Ingress",
                "name": obj_name(ingress),
                "endpoint": host,
                "host": host,
                "port": 443,
                "protocol": "HTTPS",
                "targetPort": None,
            }
        )
    return out


__all__ = [
    "backend_service_name",
    "backend_service_port",
    "ingress_entrypoints",
    "ingress_http_paths",
    "ingress_routes",
    "ingress_services",
]
