"""Shared project resource and discovery metadata helpers for renderers."""

from typing import Any, Dict, List, Tuple

from .config import clean_metadata_string
from .metadata import resource_property_key


def short_join_unique(values: List[str], limit: int = 8) -> str:
    unique: List[str] = []
    seen = set()
    for value in values:
        cleaned = str(value or "").strip()
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        unique.append(cleaned)
    if len(unique) <= limit:
        return ", ".join(unique)
    return ", ".join(unique[:limit]) + f", +{len(unique) - limit} more"


def project_discovery_items(
    project: Dict[str, Any],
    containers: List[Dict[str, Any]] | None = None,
) -> List[Tuple[str, str]]:
    discovery = project.get("discovery") or {}
    clusters: List[str] = list(discovery.get("clusters") or [])
    namespaces: List[str] = list(discovery.get("namespaces") or [])
    workloads: List[str] = list(discovery.get("workloads") or [])

    for container in containers or []:
        container_discovery = container.get("discovery") or {}
        clusters.extend(container_discovery.get("clusters") or [])
        namespaces.extend(container_discovery.get("namespaces") or [])
        workloads.extend(container_discovery.get("workloads") or [])

    return [
        ("clusters", short_join_unique(clusters)),
        ("namespaces", short_join_unique(namespaces)),
        ("workloads", short_join_unique(workloads)),
    ]


def project_resource_items(
    project: Dict[str, Any],
    containers: List[Dict[str, Any]] | None = None,
) -> List[Tuple[str, str]]:
    del containers
    resources = dict(project.get("resources") or {})
    if project.get("repo") and not resources.get("repo"):
        resources["repo"] = project.get("repo")

    items: List[Tuple[str, str]] = []
    seen = set()
    for key, value in sorted(resources.items()):
        clean_key = resource_property_key(key)
        clean_value = clean_metadata_string(value)
        if not clean_key or not clean_value:
            continue
        if (clean_key, clean_value) in seen:
            continue
        seen.add((clean_key, clean_value))
        items.append((clean_key, clean_value))
    return items


__all__ = ["project_discovery_items", "project_resource_items", "short_join_unique"]
