"""Dependency hotspot LikeC4 view sections."""

from typing import Any, Dict, List

from ...config import clean_bool, clean_int
from .common import likec4_alias
from .views_shared import include_system_line, quote, view_footer_lines, view_title


def dependency_hotspot_lines(
    product_name: str,
    hotspot_config: Dict[str, Any],
    relationship_stats_by_system: Dict[str, Dict[str, Any]],
    systems_by_id: Dict[str, Dict[str, Any]],
) -> List[str]:
    if not clean_bool(hotspot_config.get("enabled"), True):
        return []
    metric = hotspot_config.get("metric") or "incoming_distinct_source_container_count"
    min_count = clean_int(hotspot_config.get("min_count"), 3, minimum=1)
    hotspot_stats = dependency_hotspot_stats(
        relationship_stats_by_system,
        metric=metric,
        min_count=min_count,
        max_hotspots=clean_int(hotspot_config.get("max_hotspots"), 15, minimum=1),
    )
    if not hotspot_stats:
        return []
    include_ids = dependency_hotspot_include_ids(hotspot_stats)
    lines = [
        f"  view {likec4_alias(product_name + '_dependency_hotspots')} {{",
        f'    title "{quote(view_title("Overview", product_name, "Dependency hotspots"))}"',
        f"    // Most referenced systems by {quote(metric)} >= {min_count}; includes direct source systems.",
    ]
    lines.extend(include_system_line(system_id) for system_id in sorted(include_ids) if system_id in systems_by_id)
    lines.extend(view_footer_lines("LeftRight"))
    return lines


def dependency_hotspot_stats(
    relationship_stats_by_system: Dict[str, Dict[str, Any]],
    *,
    metric: str,
    min_count: int,
    max_hotspots: int,
) -> List[Dict[str, Any]]:
    hotspot_stats = [
        stats
        for stats in relationship_stats_by_system.values()
        if clean_int(stats.get(metric), 0, minimum=0) >= min_count
    ]
    hotspot_stats.sort(
        key=lambda stats: (
            clean_int(stats.get(metric), 0, minimum=0),
            clean_int(stats.get("incoming_relationship_count"), 0, minimum=0),
            stats.get("title") or "",
        ),
        reverse=True,
    )
    return hotspot_stats[:max_hotspots]


def dependency_hotspot_include_ids(hotspot_stats: List[Dict[str, Any]]) -> set:
    include_ids = set()
    for stats in hotspot_stats:
        system_id = stats.get("system_id") or ""
        if system_id:
            include_ids.add(system_id)
        include_ids.update(stats.get("incoming_source_system_ids") or [])
    return include_ids


__all__ = ["dependency_hotspot_include_ids", "dependency_hotspot_lines", "dependency_hotspot_stats"]
