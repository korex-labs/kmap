"""Service catalog helpers for namespace inspection."""

from typing import Any, Dict, List

from ...kubernetes import obj_name, service_entrypoints


def build_service_catalog(services: List[Dict[str, Any]], namespace: str) -> List[Dict[str, Any]]:
    catalog = []
    for service in services:
        item = service_catalog_item(service, namespace)
        if not item:
            continue
        catalog.append(item)
    return catalog


def service_catalog_item(service: Dict[str, Any], namespace: str) -> Dict[str, Any]:
    service_name = obj_name(service)
    if not service_name:
        return {}
    spec = service.get("spec") or {}
    return {
        "name": service_name,
        "namespace": namespace,
        "cluster_ip": spec.get("clusterIP"),
        "entrypoints": service_entrypoints(service, namespace),
    }


def build_internal_alias_to_service(service_catalog: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    aliases: Dict[str, List[str]] = {}
    for service in service_catalog:
        service_name = service.get("name")
        if not service_name:
            continue
        for entrypoint in service.get("entrypoints") or []:
            for alias in entrypoint_aliases(entrypoint):
                if alias:
                    aliases.setdefault(str(alias).lower(), []).append(service_name)
    return aliases


def entrypoint_aliases(entrypoint: Dict[str, Any]) -> List[Any]:
    return [entrypoint.get("host"), entrypoint.get("endpoint")]


__all__ = [
    "build_internal_alias_to_service",
    "build_service_catalog",
    "entrypoint_aliases",
    "service_catalog_item",
]
