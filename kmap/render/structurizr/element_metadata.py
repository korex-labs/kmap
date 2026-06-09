"""Structurizr element metadata and description helpers."""

from typing import Any, Dict, List

from ...rendering_resources import short_join_unique

MAX_LISTED_DESCRIPTION_ITEMS = 3


def diagram_text(value: str) -> str:
    return str(value or "").replace("\\n", "\n")


def element_description(element: Dict[str, Any], fallback: str = "") -> str:
    return diagram_text(element.get("description") or fallback)


def element_metadata_items(element: Dict[str, Any]) -> List[tuple[str, str]]:
    items: List[tuple[str, str]] = []
    metadata = element.get("metadata") or {}
    if not isinstance(metadata, dict):
        return items
    for key, value in sorted(metadata.items()):
        if isinstance(value, list):
            cleaned = [str(item).strip() for item in value if str(item).strip()]
            if cleaned:
                items.append((key, ", ".join(dict.fromkeys(cleaned))))
        elif str(value or "").strip():
            items.append((key, str(value).strip()))
    return items


def element_tags(element: Dict[str, Any]) -> str:
    tags = [str(tag).strip() for tag in (element.get("tags") or []) if str(tag).strip()]
    return ",".join(tags)


def runtime_values(container: Dict[str, Any], key: str) -> List[str]:
    return [
        str(value or "").strip()
        for value in ((container.get("runtime") or {}).get(key) or [])
        if str(value or "").strip()
    ]


def container_technology(container: Dict[str, Any]) -> str:
    workload_kinds = runtime_values(container, "workload_kinds")
    if workload_kinds and not container.get("technology"):
        return short_join_unique(workload_kinds)
    return container.get("technology") or container.get("kind") or "Container"


def summary_values(values: List[str], singular: str, plural: str) -> str:
    unique: List[str] = []
    seen = set()
    for value in values:
        cleaned = str(value or "").strip()
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        unique.append(cleaned)
    if not unique:
        return ""
    if len(unique) == 1:
        return f"{singular}: {unique[0]}"
    if len(unique) <= MAX_LISTED_DESCRIPTION_ITEMS:
        return f"{plural}: {', '.join(unique)}"
    return f"{plural}: {len(unique)} observed"


def container_description(container: Dict[str, Any], inbound_count: int = 0) -> str:
    if container.get("description"):
        return diagram_text(container.get("description") or "")
    discovery = container.get("discovery") or {}
    namespaces = [str(value).strip() for value in (discovery.get("namespaces") or []) if str(value).strip()]
    workloads = [str(value).strip() for value in (discovery.get("workloads") or []) if str(value).strip()]
    parts: List[str] = []
    namespace_summary = summary_values(namespaces, "Namespace", "Namespaces")
    workload_summary = summary_values(workloads, "Workload", "Workloads")
    if namespace_summary:
        parts.append(namespace_summary)
    if workload_summary:
        parts.append(workload_summary)
    if inbound_count:
        parts.append(f"Used by: {inbound_count}")
    return "\n".join(parts)


__all__ = [
    "MAX_LISTED_DESCRIPTION_ITEMS",
    "container_description",
    "container_technology",
    "diagram_text",
    "element_description",
    "element_metadata_items",
    "element_tags",
    "runtime_values",
    "summary_values",
]
