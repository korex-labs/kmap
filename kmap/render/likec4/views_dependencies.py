"""External dependency LikeC4 view sections."""

from typing import Any, Dict, List

from .common import likec4_alias
from .views_shared import include_system_line, quote, view_footer_lines, view_title, view_token


def major_external_lines(
    product_name: str,
    major_external_refs: set,
    relationship_stats_by_system: Dict[str, Dict[str, Any]],
    systems_by_id: Dict[str, Dict[str, Any]],
) -> List[str]:
    if not major_external_refs:
        return []
    lines = [
        f"  view {likec4_alias(product_name + '_external_dependencies')} {{",
        f'    title "{quote(view_title("Overview", product_name, "Major external dependencies"))}"',
        "    // High fan-in external dependencies and the systems that use them.",
    ]
    major_source_systems = major_external_source_systems(major_external_refs, relationship_stats_by_system)
    lines.extend(
        include_system_line(system_id) for system_id in sorted(major_source_systems) if system_id in systems_by_id
    )
    lines.extend(include_system_line(system_id) for system_id in sorted(major_external_refs))
    lines.extend(view_footer_lines("LeftRight"))
    return lines


def major_external_source_systems(
    major_external_refs: set,
    relationship_stats_by_system: Dict[str, Dict[str, Any]],
) -> set:
    source_systems = set()
    for external_id in major_external_refs:
        stats = relationship_stats_by_system.get(external_id) or {}
        source_systems.update(stats.get("incoming_source_system_ids") or [])
    return source_systems


def external_category_lines(
    product_name: str,
    external_refs_by_category: Dict[str, set],
    external_source_systems_by_category: Dict[str, set],
    systems_by_id: Dict[str, Dict[str, Any]],
) -> List[str]:
    lines: List[str] = []
    for category, category_external_refs in sorted(external_refs_by_category.items(), key=lambda item: item[0]):
        view_suffix = view_token(f"{category}_external_dependencies")
        lines.extend(
            [
                f"  view {likec4_alias(product_name + '_' + view_suffix)} {{",
                f'    title "{quote(view_title("External dependencies", category))}"',
                f"    // External dependencies in category: {quote(category)}.",
            ]
        )
        lines.extend(
            include_system_line(system_id)
            for system_id in sorted(external_source_systems_by_category.get(category) or [])
            if system_id in systems_by_id
        )
        lines.extend(include_system_line(system_id) for system_id in sorted(category_external_refs))
        lines.extend(view_footer_lines("LeftRight"))
    return lines


__all__ = ["external_category_lines", "major_external_lines", "major_external_source_systems"]
