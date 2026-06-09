"""Structurizr element rendering helpers."""

from dataclasses import dataclass
from typing import Any, Dict, List

from ...identifiers import dsl_url, q
from ...metadata import runtime_metadata_items
from ...rendering_resources import project_resource_items
from . import structurizr_properties_lines
from .element_metadata import (
    container_description,
    container_technology,
    diagram_text,
    element_description,
    element_metadata_items,
    element_tags,
    runtime_values,
    summary_values,
)
from .references import structurizr_alias, structurizr_system_alias

MIN_DUPLICATE_TITLE_PARTS = 2


@dataclass(frozen=True)
class InternalSystemRenderContext:
    system: Dict[str, Any]
    project: Dict[str, Any]
    containers: List[Dict[str, Any]]
    refs: Dict[str, str]
    architecture: Dict[str, Any]
    inbound_counts: Dict[str, int]


def project_property_lines(project: Dict[str, Any], containers: List[Dict[str, Any]]) -> List[str]:
    resource_items = project_resource_items(project, containers)
    lines: List[str] = []
    repo = next((value for key, value in resource_items if key == "repo"), "")
    repo_url = dsl_url(repo)
    if repo_url:
        lines.append(f"  url {repo_url}")
    lines.append("  properties {")
    lines.append(f'    "project_id" "{q(project.get("id") or "")}"')
    for key, value in resource_items:
        lines.append(f'    "resource.{q(key)}" "{q(value)}"')
    lines.append("  }")
    return lines


def system_project_property_lines(
    system: Dict[str, Any], project: Dict[str, Any], containers: List[Dict[str, Any]]
) -> List[str]:
    lines = project_property_lines(project, containers)
    for index, line in enumerate(lines):
        if line == "  properties {":
            lines.insert(index + 1, f'    "system_id" "{q(system.get("id") or "")}"')
            break
    return lines


def container_lines(
    container: Dict[str, Any],
    refs: Dict[str, str],
    inbound_counts: Dict[str, int],
    indent: str = "  ",
) -> List[str]:
    alias = refs.get(container.get("id") or "") or structurizr_alias(container.get("id") or "")
    title = container.get("title") or container.get("name") or alias
    lines = [
        f'{indent}{alias} = container "{q(title)}" "{q(container_description(container, inbound_counts.get(container.get("id") or "", 0)))}" "{q(container_technology(container))}" {{'
    ]
    tags = element_tags(container)
    if tags:
        lines.append(f'{indent}  tags "{q(tags)}"')
    lines.extend(structurizr_properties_lines(runtime_metadata_items(container), indent=f"{indent}  "))
    lines.append(f"{indent}}}")
    return lines


def system_lines(
    system: Dict[str, Any],
    containers: List[Dict[str, Any]],
    refs: Dict[str, str],
    inbound_counts: Dict[str, int],
) -> List[str]:
    alias = refs.get(system.get("id") or "") or structurizr_alias(system.get("id") or "")
    title = system.get("title") or system.get("name") or alias
    fallback_description = "" if system.get("project_id") else "External dependency"
    lines = [f'{alias} = softwareSystem "{q(title)}" "{q(element_description(system, fallback_description))}" {{']
    tags = element_tags(system)
    if tags:
        lines.append(f'  tags "{q(tags)}"')
    metadata_items = element_metadata_items(system)
    if system.get("project_id") or metadata_items:
        lines.append("  properties {")
        if system.get("project_id"):
            lines.append(f'    "project_id" "{q(system.get("project_id") or "")}"')
        for key, value in metadata_items:
            lines.append(f'    "{q(key)}" "{q(value)}"')
        lines.append("  }")
    for container in containers:
        lines.extend(container_lines(container, refs, inbound_counts))
    lines.append("}")
    return lines


def internal_system_lines(
    system: Dict[str, Any],
    project: Dict[str, Any],
    containers: List[Dict[str, Any]],
    refs: Dict[str, str],
    *render_parts: Any,
    **render_options: Any,
) -> List[str]:
    architecture = render_options.get("architecture", render_parts[0] if render_parts else {})
    inbound_counts = render_options.get("inbound_counts", render_parts[1] if len(render_parts) > 1 else {})
    return internal_system_lines_from_context(
        InternalSystemRenderContext(
            system=system,
            project=project,
            containers=containers,
            refs=refs,
            architecture=architecture,
            inbound_counts=inbound_counts,
        )
    )


def internal_system_lines_from_context(context: InternalSystemRenderContext) -> List[str]:
    alias = context.refs.get(context.system.get("id") or "") or structurizr_system_alias(context.system)
    product = context.architecture.get("product") or {}
    product_name = product.get("name") or (context.architecture.get("workspace") or {}).get("product") or ""
    title = context.system.get("title") or context.system.get("name") or alias
    project_title = context.project.get("title") or context.project.get("name") or ""
    title_parts = [part for part in (product_name, project_title, title) if part]
    if len(title_parts) >= MIN_DUPLICATE_TITLE_PARTS and title_parts[-1].lower() == title_parts[-2].lower():
        title_parts.pop()
    display_title = " / ".join(title_parts) if title_parts else title
    lines = [
        f'{alias} = softwareSystem "{q(display_title)}" "{q(element_description(context.system, "Product scope"))}" {{'
    ]
    tags = element_tags(context.system)
    if tags:
        lines.append(f'  tags "{q(tags)}"')
    lines.extend(system_project_property_lines(context.system, context.project, context.containers))
    for container in context.containers:
        lines.extend(container_lines(container, context.refs, context.inbound_counts))
    lines.append("}")
    return lines


__all__ = [
    "InternalSystemRenderContext",
    "container_description",
    "container_lines",
    "container_technology",
    "diagram_text",
    "element_description",
    "element_metadata_items",
    "element_tags",
    "internal_system_lines",
    "internal_system_lines_from_context",
    "project_property_lines",
    "runtime_values",
    "structurizr_alias",
    "structurizr_system_alias",
    "summary_values",
    "system_lines",
    "system_project_property_lines",
]
