"""Shared deployment grouping helpers."""

from typing import Any

from ..lists import append_clean_unique_string as append_unique


def pod_group_key(instance: dict[str, Any]) -> str:
    return str(instance.get("name") or instance.get("id") or "instance")


def pod_groups(instances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    groups_by_key: dict[str, dict[str, Any]] = {}
    for instance in instances:
        key = pod_group_key(instance)
        group = groups_by_key.get(key)
        if not group:
            group = {
                "id": instance.get("id") or instance.get("name") or "instance",
                "title": instance.get("name") or instance.get("id") or "instance",
                "instances": [],
                "node_kinds": [],
            }
            groups_by_key[key] = group
            groups.append(group)
        group["instances"].append(instance)
        append_unique(group["node_kinds"], instance.get("node_kind") or "")
    return groups


def pod_system_titles(
    pod_group: dict[str, Any],
    containers_by_id: dict[str, dict[str, Any]],
    systems_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    systems: list[str] = []
    for instance in pod_group["instances"]:
        container = containers_by_id.get(instance.get("container_id") or "") or {}
        system = systems_by_id.get(container.get("system_id") or "") or {}
        append_unique(systems, system.get("title") or system.get("name") or "")
    return systems


def pod_display_titles(
    grouped_pods: list[dict[str, Any]],
    containers_by_id: dict[str, dict[str, Any]],
    systems_by_id: dict[str, dict[str, Any]],
) -> dict[str, str]:
    candidates: dict[str, str] = {}
    counts: dict[str, int] = {}
    for pod_group in grouped_pods:
        systems = pod_system_titles(pod_group, containers_by_id, systems_by_id)
        candidate = systems[0] if len(systems) == 1 else pod_group["title"]
        candidates[pod_group["id"]] = candidate
        counts[candidate] = counts.get(candidate, 0) + 1

    display_titles: dict[str, str] = {}
    for pod_group in grouped_pods:
        candidate = candidates.get(pod_group["id"], pod_group["title"])
        display_titles[pod_group["id"]] = candidate if counts.get(candidate, 0) == 1 else pod_group["title"]
    return display_titles


def merged_instance_runtime(instances: list[dict[str, Any]]) -> dict[str, list[Any]]:
    runtime: dict[str, list[Any]] = {}
    for instance in instances:
        for key, values in (instance.get("runtime") or {}).items():
            target = runtime.setdefault(key, [])
            for value in values if isinstance(values, list) else [values]:
                append_unique(target, value)
    return runtime


__all__ = ["append_unique", "merged_instance_runtime", "pod_display_titles", "pod_groups", "pod_system_titles"]
