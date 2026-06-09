"""LikeC4 system drilldown view rendering helpers."""

from collections import Counter
from typing import Any, Dict, List

from .common import likec4_alias
from .views_shared import include_system_line, quote, system_ref, view_footer_lines, view_title


def system_drilldown_lines(
    internal_systems: List[Dict[str, Any]],
    direct_dependency_systems: Dict[str, set],
    internal_title_counts: Counter,
    project_by_id: Dict[str, Dict[str, Any]],
) -> List[str]:
    lines: List[str] = []
    for system in sorted(internal_systems, key=lambda item: item.get("name", "")):
        ref = system_ref(system.get("id") or "")
        system_title = system.get("title") or system.get("name") or ref
        lines.extend(
            [
                f"  view of {ref} {{",
                f'    title "{quote(view_title("Systems", system_title))}"',
                "    // System drilldown: containers and direct relationships.",
                "    include *",
                "    autoLayout LeftRight",
                "  }",
                "",
            ]
        )

        neighbor_ids = sorted(direct_dependency_systems.get(system.get("id") or "", set()))
        if neighbor_ids:
            dep_view_name = likec4_alias(f"{system.get('id') or system.get('name')}_dependencies")
            dep_view_title = system_dependency_view_title(system, ref, internal_title_counts, project_by_id)
            lines.extend(
                [
                    f"  view {dep_view_name} {{",
                    f'    title "{quote(view_title("Systems", dep_view_title, "Dependencies"))}"',
                    "    // Direct incoming/outgoing system dependencies; containers stay hidden.",
                    f"    include {ref}",
                ]
            )
            lines.extend(include_system_line(neighbor_id) for neighbor_id in neighbor_ids)
            lines.extend(view_footer_lines("LeftRight"))
    return lines


def system_dependency_view_title(
    system: Dict[str, Any],
    fallback_ref: str,
    internal_title_counts: Counter,
    project_by_id: Dict[str, Dict[str, Any]],
) -> str:
    title = system.get("title") or system.get("name") or fallback_ref
    if internal_title_counts.get(title, 0) <= 1:
        return title
    project = project_by_id.get(system.get("project_id") or {}) or {}
    project_name = project.get("name") or system.get("project_id") or ""
    return f"{title} ({project_name})" if project_name else title


__all__ = ["system_dependency_view_title", "system_drilldown_lines"]
