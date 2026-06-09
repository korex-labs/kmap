"""Project model helpers."""

from typing import Any, Dict

from ..config import clean_metadata_string
from ..naming import humanize_slug


def project_entry(
    *,
    project_id: str,
    product_id: str,
    project_name: str,
    product_metadata: Dict[str, Any],
    project_meta: Dict[str, Any],
) -> Dict[str, Any]:
    project_owner_team = product_metadata.get("owner_team") or project_meta.get("owner_team", "")
    return {
        "id": project_id,
        "product_id": product_id,
        "name": project_name,
        "title": project_meta.get("title") or humanize_slug(project_name),
        "repo": project_meta.get("repo", ""),
        "owner_team": project_owner_team,
        "domain_team": project_meta.get("domain_team", ""),
        "description": project_meta.get("description", ""),
        "resources": dict(project_meta.get("resources", {})),
        "tags": merged_project_tags(product_metadata, project_meta),
        "discovery": {
            "namespaces": [],
            "mapping_source": "report",
        },
    }


def merged_project_tags(product_metadata: Dict[str, Any], project_meta: Dict[str, Any]) -> list[Any]:
    tags = list(product_metadata.get("tags") or [])
    for tag in project_meta.get("tags", []) or []:
        if tag not in tags:
            tags.append(tag)
    return tags


def record_project_namespace_discovery(
    project: Dict[str, Any],
    *,
    namespace: str,
    cluster: str,
    project_meta: Dict[str, Any],
    report_discovery: Dict[str, Any],
) -> None:
    if not namespace:
        return

    discovery = project.setdefault("discovery", {})
    namespaces = discovery.setdefault("namespaces", [])
    if namespace not in namespaces:
        namespaces.append(namespace)

    namespaces_meta = discovery.setdefault("namespace_metadata", {})
    if namespace not in namespaces_meta:
        namespaces_meta[namespace] = namespace_metadata_from_project_meta(project_meta)
    namespaces_meta[namespace]["cluster"] = clean_metadata_string(cluster)
    if report_discovery.get("context"):
        namespaces_meta[namespace]["context"] = clean_metadata_string(report_discovery.get("context"))


def namespace_metadata_from_project_meta(project_meta: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in project_meta.items()
        if key in {"title", "domain_team", "description", "tags", "resources"}
    }


__all__ = [
    "merged_project_tags",
    "namespace_metadata_from_project_meta",
    "project_entry",
    "record_project_namespace_discovery",
]
