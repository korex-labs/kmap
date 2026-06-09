"""LikeC4 views renderer."""

from typing import Any, Dict, List

from .deployment_views import deployment_view_lines
from .system_views import system_drilldown_lines
from .views_context import (
    LikeC4ViewContext,
    application_likec4_systems,
    internal_likec4_systems,
    internal_system_title_counts,
    likec4_view_context,
    major_external_system_refs,
    platform_likec4_systems,
    relationship_stats_by_system_id,
)
from .views_dependencies import external_category_lines, major_external_lines
from .views_hotspots import dependency_hotspot_lines
from .views_landscape import (
    application_landscape_lines,
    overview_lines,
    platform_support_lines,
    project_view_lines,
)


def render_likec4_views(architecture: Dict[str, Any]) -> str:
    context = likec4_view_context(architecture)
    lines = ["views {", ""]
    lines.extend(likec4_view_sections(context))
    lines.append("}")
    return "\n".join(lines) + "\n"


def likec4_view_sections(context: LikeC4ViewContext) -> List[str]:
    lines: List[str] = []
    lines.extend(overview_lines(context.product_name, context.internal_systems, context.major_external_refs))
    lines.extend(application_landscape_lines(context.product_name, context.app_systems, context.major_external_refs))
    lines.extend(platform_support_lines(context.product_name, context.platform_systems))
    lines.extend(project_view_lines(context.product_name, context.project_systems, context.project_by_id))
    lines.extend(major_external_view_lines(context))
    lines.extend(external_category_view_lines(context))
    lines.extend(dependency_hotspot_view_lines(context))
    lines.extend(system_drilldown_view_lines(context))
    lines.extend(deployment_view_lines(context.product_name, context.deployments))
    return lines


def major_external_view_lines(context: LikeC4ViewContext) -> List[str]:
    return major_external_lines(
        context.product_name,
        context.major_external_refs,
        context.relationship_stats_by_system,
        context.systems_by_id,
    )


def external_category_view_lines(context: LikeC4ViewContext) -> List[str]:
    return external_category_lines(
        context.product_name,
        context.relationship_context.external_refs_by_category,
        context.relationship_context.external_source_systems_by_category,
        context.systems_by_id,
    )


def dependency_hotspot_view_lines(context: LikeC4ViewContext) -> List[str]:
    return dependency_hotspot_lines(
        context.product_name,
        context.hotspot_config,
        context.relationship_stats_by_system,
        context.systems_by_id,
    )


def system_drilldown_view_lines(context: LikeC4ViewContext) -> List[str]:
    return system_drilldown_lines(
        context.internal_systems,
        context.relationship_context.direct_dependency_systems,
        context.internal_title_counts,
        context.project_by_id,
    )


__all__ = [
    "application_likec4_systems",
    "internal_likec4_systems",
    "internal_system_title_counts",
    "major_external_system_refs",
    "platform_likec4_systems",
    "relationship_stats_by_system_id",
    "render_likec4_views",
]
