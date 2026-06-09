"""Landscape and project LikeC4 view sections."""

from typing import Any, Dict, List

from .common import likec4_alias
from .views_shared import include_line, include_system_line, quote, system_ref_from_item, view_footer_lines, view_title


def overview_lines(product_name: str, internal_systems: List[Dict[str, Any]], major_external_refs: set) -> List[str]:
    lines = [
        f"  view {likec4_alias(product_name + '_landscape')} {{",
        f'    title "{quote(view_title("Overview", product_name, "Product landscape"))}"',
        "    // Product-level slice: internal systems plus high fan-in external dependencies.",
    ]
    lines.extend(include_line(system_ref_from_item(system)) for system in internal_systems)
    lines.extend(include_system_line(system_id) for system_id in sorted(major_external_refs))
    lines.extend(view_footer_lines("TopBottom"))
    return lines


def application_landscape_lines(
    product_name: str,
    app_systems: List[Dict[str, Any]],
    major_external_refs: set,
) -> List[str]:
    if not app_systems:
        return []
    lines = [
        f"  view {likec4_alias(product_name + '_application_landscape')} {{",
        f'    title "{quote(view_title("Overview", product_name, "Applications"))}"',
        "    // Business/application systems only. Platform and observability noise is hidden.",
    ]
    lines.extend(
        include_line(system_ref_from_item(system))
        for system in sorted(app_systems, key=lambda item: item.get("title", ""))
    )
    lines.extend(include_system_line(system_id) for system_id in sorted(major_external_refs))
    lines.extend(view_footer_lines("LeftRight"))
    return lines


def platform_support_lines(product_name: str, platform_systems: List[Dict[str, Any]]) -> List[str]:
    if not platform_systems:
        return []
    lines = [
        f"  view {likec4_alias(product_name + '_platform_support')} {{",
        f'    title "{quote(view_title("Overview", product_name, "Platform and support"))}"',
        "    // Messaging, data, monitoring and support systems.",
    ]
    lines.extend(
        include_line(system_ref_from_item(system))
        for system in sorted(platform_systems, key=lambda item: (item.get("category", ""), item.get("title", "")))
    )
    lines.extend(view_footer_lines("LeftRight"))
    return lines


def project_view_lines(
    product_name: str,
    project_systems: Dict[str, List[Dict[str, Any]]],
    project_by_id: Dict[str, Dict[str, Any]],
) -> List[str]:
    lines: List[str] = []
    for project_id, project_system_list in sorted(project_systems.items(), key=lambda item: item[0]):
        project = project_by_id.get(project_id) or {}
        project_name = project.get("name") or project_id or "project"
        project_title = project.get("title") or project_name
        view_name = likec4_alias(f"{product_name}_{project_name}_project")
        lines.extend(
            [
                f"  view {view_name} {{",
                f'    title "{quote(view_title("Projects", project_title))}"',
                "    // Project ownership slice: systems only; containers stay in scoped drilldowns.",
            ]
        )
        lines.extend(
            include_line(system_ref_from_item(system))
            for system in sorted(project_system_list, key=lambda item: item.get("name", ""))
        )
        lines.extend(view_footer_lines("LeftRight"))
    return lines


__all__ = [
    "application_landscape_lines",
    "overview_lines",
    "platform_support_lines",
    "project_view_lines",
]
