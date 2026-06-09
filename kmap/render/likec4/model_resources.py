"""LikeC4 model resource links and metadata helpers."""

from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from ...config import clean_metadata_string
from ...hostish import parse_hostish
from ...identifiers import dsl_url, sq
from ...metadata import resource_property_key
from ...naming import humanize_slug
from ...rendering_resources import project_resource_items
from .common import likec4_metadata_lines


def single_quote(value: str) -> str:
    return sq(value)


def is_url(value: str) -> bool:
    text = clean_metadata_string(value)
    if not text:
        return False
    parsed = urlparse(text)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def endpoint_label(dep_key: str) -> str:
    parsed = parse_hostish(dep_key or "")
    if not parsed:
        return dep_key or ""

    host, _, _ = parsed
    host = (host or "").strip().lower()
    internal_suffixes = (".svc", ".svc.cluster.local", ".lan", ".consul", ".local")

    if any(suffix in host for suffix in internal_suffixes):
        return host.split(".", 1)[0]
    return host


def likec4_link_label(key: str) -> str:
    labels = {
        "repo": "Repository",
        "tasks": "Tasks",
        "logs": "Logs",
        "zabbix": "Zabbix",
        "chat": "Chat",
        "url": "URL",
        "domain": "Website",
    }
    return labels.get(resource_property_key(key), humanize_slug(key))


def diagram_description(value: str) -> str:
    return "; ".join(part.strip() for part in str(value or "").replace("\\n", "\n").splitlines() if part.strip())


def element_metadata_items(element: Dict[str, Any]) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []
    metadata = element.get("metadata") or {}
    if not isinstance(metadata, dict):
        return items
    for key, value in sorted(metadata.items()):
        if isinstance(value, list):
            cleaned = [clean_metadata_string(item) for item in value if clean_metadata_string(item)]
            if cleaned:
                items.append((key, ", ".join(dict.fromkeys(cleaned))))
        elif clean_metadata_string(value):
            items.append((key, clean_metadata_string(value)))
    return items


def likec4_system_description(system: Dict[str, Any], project_by_id: Dict[str, Dict[str, Any]]) -> str:
    description = clean_metadata_string(system.get("description"))
    if description:
        return diagram_description(description)
    project = project_by_id.get(system.get("project_id") or "")
    return diagram_description(clean_metadata_string((project or {}).get("description")))


def likec4_system_resource_lines(system: Dict[str, Any], project_by_id: Dict[str, Dict[str, Any]]) -> List[str]:
    project = project_by_id.get(system.get("project_id") or "")
    if not project:
        return []
    metadata_resources: List[Tuple[str, str]] = [
        ("project", project.get("name") or ""),
        ("project_title", project.get("title") or ""),
        ("devops", project.get("owner_team") or ""),
        ("domain_team", project.get("domain_team") or ""),
    ]

    lines = likec4_metadata_lines(metadata_resources, indent="    ")
    lines.extend(likec4_resource_link_lines(project_resource_items(project), indent="    "))
    return lines


def likec4_container_resource_lines(
    container: Dict[str, Any],
    project_by_id: Dict[str, Dict[str, Any]],
    fallback_project: Dict[str, Any] | None = None,
) -> List[str]:
    project = project_by_id.get(container.get("project_id") or "") or fallback_project or {}
    if not project:
        return []
    return likec4_resource_link_lines(project_resource_items(project), indent="      ")


def likec4_resource_link_lines(resources: List[Tuple[str, str]], indent: str) -> List[str]:
    lines = []
    for key, value in resources:
        url = dsl_url(value)
        if url:
            lines.append(f"{indent}link {url} '{single_quote(likec4_link_label(key))}'")
    return lines


def likec4_external_resource_lines(system: Dict[str, Any]) -> List[str]:
    kind = system.get("element_type") or "system"
    title = clean_metadata_string(system.get("title") or system.get("name"))
    if kind != "Website" or not title:
        return []

    domain = endpoint_label(title) or title
    if not domain or domain.lower() in {"website", "websites"}:
        return []
    url = title if is_url(title) else f"https://{domain}"
    url = dsl_url(url)
    if not url:
        return []
    resources = [
        ("domain", domain.lower()),
        ("url", url),
    ]
    lines = likec4_metadata_lines(resources, indent="    ")
    lines.append(f"    link {url} 'Website'")
    return lines


__all__ = [
    "diagram_description",
    "element_metadata_items",
    "endpoint_label",
    "is_url",
    "likec4_container_resource_lines",
    "likec4_external_resource_lines",
    "likec4_link_label",
    "likec4_resource_link_lines",
    "likec4_system_description",
    "likec4_system_resource_lines",
    "single_quote",
]
