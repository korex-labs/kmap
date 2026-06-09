"""Entrypoint index helpers for dependency relation matching."""

from collections import defaultdict
from typing import Any, Dict, List

from ...naming import service_reference_variants, short_service_name_variants


def dependency_entry_hits(
    dependency: Dict[str, Any],
    service: Dict[str, Any],
    entry_index: Dict[str, List[Dict[str, Any]]],
    system_naming_config: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    search_keys = []
    for key in [str(dependency.get("key") or "").lower(), str(dependency.get("host") or "").lower()]:
        search_keys.extend(service_reference_variants(key, service.get("project") or "", system_naming_config))
    search_keys = [key for key in dict.fromkeys(search_keys) if key]

    hits: List[Dict[str, Any]] = []
    for key in search_keys:
        hits.extend(entry_index.get(key, []))
    return hits


def build_entry_index(
    services: List[Dict[str, Any]],
    system_naming_config: Dict[str, Any] | None = None,
) -> Dict[str, List[Dict[str, Any]]]:
    entry_index: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for service in services:
        index_service_entrypoints(entry_index, service, system_naming_config)
        index_implicit_workload_entrypoints(entry_index, service, system_naming_config)
    return entry_index


def index_service_entrypoints(
    entry_index: Dict[str, List[Dict[str, Any]]],
    service: Dict[str, Any],
    system_naming_config: Dict[str, Any] | None = None,
) -> None:
    service_project = service.get("project") or ""
    for entrypoint in service.get("entrypoints", []):
        candidates = set()
        candidates.update(
            service_reference_variants(
                str(entrypoint.get("endpoint", "")).lower(),
                service_project,
                system_naming_config,
            )
        )
        candidates.update(
            service_reference_variants(
                str(entrypoint.get("host", "")).lower(),
                service_project,
                system_naming_config,
            )
        )
        for candidate in candidates:
            if candidate:
                entry_index[candidate].append(
                    {
                        "service_id": service["service_id"],
                        "namespace": service["namespace"],
                        "cluster": service["cluster"],
                        "entrypoint_type": entrypoint.get("type") or "Service",
                    }
                )


def index_implicit_workload_entrypoints(
    entry_index: Dict[str, List[Dict[str, Any]]],
    service: Dict[str, Any],
    system_naming_config: Dict[str, Any] | None = None,
) -> None:
    service_project = service.get("project") or ""
    implicit_candidates = set()
    for candidate in {
        service.get("service_name", "").lower(),
        f"{service.get('service_name', '')}.{service.get('namespace', '')}".lower(),
        f"{service.get('service_name', '')}.{service.get('namespace', '')}.svc".lower(),
        f"{service.get('service_name', '')}.{service.get('namespace', '')}.svc.cluster.local".lower(),
    }:
        implicit_candidates.update(service_reference_variants(candidate, service_project, system_naming_config))
    implicit_candidates.update(short_service_name_variants(service.get("service_name", "")))
    for candidate in implicit_candidates:
        if candidate:
            entry_index[candidate].append(
                {
                    "service_id": service["service_id"],
                    "namespace": service["namespace"],
                    "cluster": service["cluster"],
                    "entrypoint_type": "implicit_workload",
                }
            )


__all__ = [
    "build_entry_index",
    "dependency_entry_hits",
    "index_implicit_workload_entrypoints",
    "index_service_entrypoints",
]
