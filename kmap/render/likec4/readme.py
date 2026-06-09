"""LikeC4 README renderer."""

from typing import Any, Dict

from ...model.metadata import generator_metadata
from .readme_sections import (
    append_dependency_sections,
    append_deployment_sections,
    append_followup_section,
    append_project_sections,
    append_relationship_sections,
    generated_files_lines,
    intro_lines,
    regenerate_lines,
    summary_lines,
)
from .readme_tables import readme_tables


def _readme_context(architecture: Dict[str, Any]) -> Dict[str, Any]:
    workspace = architecture.get("workspace") or {}
    product = architecture.get("product") or {}
    source = workspace.get("source") or {}
    product_name = _readme_product_name(product, workspace)
    return {
        "workspace": workspace,
        "product": product,
        "product_name": product_name,
        **_readme_workspace_context(workspace, source, product, product_name),
        **_readme_architecture_collections(architecture),
    }


def _readme_product_name(product: Dict[str, Any], workspace: Dict[str, Any]) -> str:
    return product.get("name") or workspace.get("product") or "product"


def _readme_workspace_context(
    workspace: Dict[str, Any],
    source: Dict[str, Any],
    product: Dict[str, Any],
    product_name: str,
) -> Dict[str, Any]:
    return {
        "product_title": product.get("title") or product_name,
        "default_env": workspace.get("default_env") or "prod",
        "generator": workspace.get("generator") or generator_metadata(source.get("config_file", ""), "likec4"),
        "config_file": source.get("config_file") or f"config/{product_name}.yaml",
        "generated_at": workspace.get("generated_at") or "",
    }


def _readme_architecture_collections(architecture: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "generation_hints": architecture.get("generation_hints") or {},
        "systems": architecture.get("systems") or [],
        "containers": architecture.get("containers") or [],
        "relationships": architecture.get("relationships") or [],
        "traffic_flows": architecture.get("traffic_flows") or [],
        "projects": architecture.get("projects") or [],
        "deployments": architecture.get("deployments") or [],
        "system_stats": (architecture.get("relationship_statistics") or {}).get("systems") or [],
    }


def render_likec4_readme(architecture: Dict[str, Any]) -> str:
    context = _readme_context(architecture)
    tables = readme_tables(context)
    lines = intro_lines(context["product_title"])
    lines.extend(summary_lines(context, tables.internal_systems, tables.external_systems))
    lines.extend(regenerate_lines(context["config_file"], context["product_name"]))
    append_project_sections(lines, tables)
    append_dependency_sections(lines, tables)
    append_relationship_sections(lines, tables)
    append_deployment_sections(lines, tables)
    append_followup_section(lines, tables)
    lines.extend(generated_files_lines())
    return "\n".join(lines)


__all__ = ["render_likec4_readme"]
