"""Relationship statistics rendering helpers."""

from typing import Any, Dict, List


def render_system_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    incoming_source_system_ids = pop_sorted_values(stats, "incoming_source_system_ids")
    incoming_source_container_ids = pop_sorted_values(stats, "incoming_source_container_ids")
    outgoing_target_system_ids = pop_sorted_values(stats, "outgoing_target_system_ids")
    outgoing_target_container_ids = pop_sorted_values(stats, "outgoing_target_container_ids")
    incoming_by_type = pop_sorted_counter(stats, "incoming_by_type")
    outgoing_by_type = pop_sorted_counter(stats, "outgoing_by_type")
    incoming_by_boundary = pop_sorted_counter(stats, "incoming_by_boundary")
    outgoing_by_boundary = pop_sorted_counter(stats, "outgoing_by_boundary")

    stats.update(
        {
            "incoming_distinct_source_system_count": len(incoming_source_system_ids),
            "incoming_distinct_source_container_count": len(incoming_source_container_ids),
            "outgoing_distinct_target_system_count": len(outgoing_target_system_ids),
            "outgoing_distinct_target_container_count": len(outgoing_target_container_ids),
            "incoming_source_system_ids": incoming_source_system_ids,
            "incoming_source_container_ids": incoming_source_container_ids,
            "outgoing_target_system_ids": outgoing_target_system_ids,
            "outgoing_target_container_ids": outgoing_target_container_ids,
            "incoming_by_type": incoming_by_type,
            "outgoing_by_type": outgoing_by_type,
            "incoming_by_boundary": incoming_by_boundary,
            "outgoing_by_boundary": outgoing_by_boundary,
        }
    )
    return stats


def pop_sorted_values(mapping: Dict[str, Any], key: str) -> List[Any]:
    return sorted(mapping.pop(key))


def pop_sorted_counter(mapping: Dict[str, Any], key: str) -> Dict[str, int]:
    return dict(sorted(mapping.pop(key).items()))


def render_relationship_group(aggregate: Dict[str, Any]) -> Dict[str, Any]:
    aggregate["source_container_ids"] = sorted(aggregate["source_container_ids"])
    aggregate["target_container_ids"] = sorted(aggregate["target_container_ids"])
    aggregate["source_container_count"] = len(aggregate["source_container_ids"])
    aggregate["target_container_count"] = len(aggregate["target_container_ids"])
    aggregate["relationship_ids"] = sorted(x for x in aggregate["relationship_ids"] if x)
    return aggregate


__all__ = ["pop_sorted_counter", "pop_sorted_values", "render_relationship_group", "render_system_stats"]
