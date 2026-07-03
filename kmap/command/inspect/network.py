"""Network context extraction for namespace inspection."""

from typing import Any

from ...config import clean_metadata_string
from ...kubernetes import (
    ingress_entrypoints,
    ingress_routes,
    ingress_services,
    obj_name,
    service_entrypoints,
    service_matches_workload,
)


def workload_traffic_routes(
    workload: dict[str, Any],
    matched_services: list[str],
    matched_ingresses: list[str],
    services: list[dict[str, Any]],
    ingresses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    workload_name = obj_name(workload)
    containers = workload_container_names(workload)
    routes = []

    for service in named_objects(services, matched_services):
        routes.extend(service_traffic_routes(service, workload_name, containers))

    for ingress in named_objects(ingresses, matched_ingresses):
        routes.extend(ingress_traffic_routes(ingress, matched_services, workload_name, containers))

    return routes


def workload_container_names(workload: dict[str, Any]) -> list[str]:
    pod_spec = ((workload.get("spec") or {}).get("template") or {}).get("spec") or {}
    return [
        clean_metadata_string(container.get("name"))
        for container in pod_spec.get("containers") or []
        if clean_metadata_string(container.get("name"))
    ]


def service_traffic_routes(
    service: dict[str, Any],
    workload_name: str,
    containers: list[str],
) -> list[dict[str, Any]]:
    service_name = obj_name(service)
    return [
        service_traffic_route(service_name, entrypoint, workload_name, containers)
        for entrypoint in service_entrypoints(service, "")
        if not (entrypoint.get("host") and "." in str(entrypoint.get("host")))
    ]


def service_traffic_route(
    service_name: str,
    entrypoint: dict[str, Any],
    workload_name: str,
    containers: list[str],
) -> dict[str, Any]:
    return {
        "direction": "inbound",
        "source": {"type": "ServiceClient", "name": service_name},
        "hops": [
            {
                "type": "Service",
                "name": service_name,
                "port": entrypoint.get("port"),
                "protocol": entrypoint.get("protocol"),
                "target_port": entrypoint.get("targetPort"),
            },
            {
                "type": "Workload",
                "name": workload_name,
            },
        ],
        "target": {"type": "Container", "names": containers},
    }


def ingress_traffic_routes(
    ingress: dict[str, Any],
    matched_services: list[str],
    workload_name: str,
    containers: list[str],
) -> list[dict[str, Any]]:
    ingress_name = obj_name(ingress)
    return [
        ingress_traffic_route(ingress_name, route, workload_name, containers)
        for route in ingress_routes(ingress)
        if route.get("service") in matched_services
    ]


def ingress_traffic_route(
    ingress_name: str,
    route: dict[str, Any],
    workload_name: str,
    containers: list[str],
) -> dict[str, Any]:
    host = route.get("host") or "*"
    path = route.get("path") or "/"
    return {
        "direction": "inbound",
        "source": {"type": "External", "name": host, "path": path},
        "hops": [
            {
                "type": "Ingress",
                "name": ingress_name,
                "host": host,
                "path": path,
            },
            {
                "type": "Service",
                "name": route.get("service"),
                "port": route.get("service_port"),
            },
            {
                "type": "Workload",
                "name": workload_name,
            },
        ],
        "target": {"type": "Container", "names": containers},
    }


def workload_network_context(
    workload: dict[str, Any],
    namespace: str,
    services: list[dict[str, Any]],
    ingresses: list[dict[str, Any]],
) -> dict[str, Any]:
    matched_services = matched_service_names(workload, services)
    matched_ingresses = matched_ingress_names(matched_services, ingresses)
    entrypoints = workload_entrypoints(namespace, services, ingresses, matched_services, matched_ingresses)

    return {
        "services": matched_services,
        "ingresses": matched_ingresses,
        "entrypoints": entrypoints,
        "traffic_routes": workload_traffic_routes(
            workload,
            matched_services,
            matched_ingresses,
            services,
            ingresses,
        ),
    }


def matched_service_names(workload: dict[str, Any], services: list[dict[str, Any]]) -> list[str]:
    return [obj_name(service) for service in services if service_matches_workload(service, workload)]


def matched_ingress_names(matched_services: list[str], ingresses: list[dict[str, Any]]) -> list[str]:
    service_names = set(matched_services)
    return [
        obj_name(ingress) for ingress in ingresses if any(name in service_names for name in ingress_services(ingress))
    ]


def named_objects(objects: list[dict[str, Any]], names: list[str]) -> list[dict[str, Any]]:
    name_set = set(names)
    return [obj for obj in objects if obj_name(obj) in name_set]


def workload_entrypoints(
    namespace: str,
    services: list[dict[str, Any]],
    ingresses: list[dict[str, Any]],
    matched_services: list[str],
    matched_ingresses: list[str],
) -> list[dict[str, Any]]:
    entrypoints = []
    for service in named_objects(services, matched_services):
        entrypoints.extend(service_entrypoints(service, namespace))
    for ingress in named_objects(ingresses, matched_ingresses):
        entrypoints.extend(ingress_entrypoints(ingress))
    return entrypoints


__all__ = [
    "matched_ingress_names",
    "matched_service_names",
    "named_objects",
    "workload_network_context",
    "workload_traffic_routes",
]
