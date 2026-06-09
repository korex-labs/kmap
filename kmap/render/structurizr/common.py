"""Shared Structurizr DSL rendering helpers."""

from typing import Any, Dict, List, Optional, Tuple

from ...identifiers import dsl_url
from ...metadata import resource_property_key
from ...naming import q
from ...rendering_resources import project_resource_items as _project_resource_items


def _quote(value: str) -> str:
    return q(value)


def structurizr_resource_lines(
    project: Dict[str, Any],
    indent: str = "  ",
    extra_items: Optional[List[Tuple[str, str]]] = None,
) -> List[str]:
    resources = _project_resource_items(project)
    resources.extend(extra_items or [])
    if not resources:
        return []

    lines: List[str] = []
    repo = next((value for key, value in resources if key == "repo"), "")
    repo_url = dsl_url(repo)
    if repo_url:
        lines.append(f"{indent}url {repo_url}")

    lines.append(f"{indent}properties {{")
    for key, value in resources:
        lines.append(f'{indent}  "resource.{_quote(key)}" "{_quote(value)}"')
    lines.append(f"{indent}}}")
    return lines


def _clean_value(value: Any) -> str:
    return str(value or "").strip()


def structurizr_properties_lines(items: List[Tuple[str, str]], indent: str = "  ") -> List[str]:
    cleaned = [
        (resource_property_key(key), _clean_value(value))
        for key, value in items
        if resource_property_key(key) and _clean_value(value)
    ]
    if not cleaned:
        return []
    lines = [f"{indent}properties {{"]
    for key, value in cleaned:
        lines.append(f'{indent}  "{_quote(key)}" "{_quote(value)}"')
    lines.append(f"{indent}}}")
    return lines


__all__ = [
    "structurizr_properties_lines",
    "structurizr_resource_lines",
]
