"""Shared workload selection and container context helpers."""

import re
from typing import Any, Dict, List, Tuple

from ..kubernetes import container_inventory, find_related_workloads, obj_name


def extract_refs_from_container(container: Dict[str, Any]) -> Tuple[set, set]:
    cms, secs = set(), set()
    for env_from in container.get("envFrom") or []:
        if env_from.get("configMapRef", {}).get("name"):
            cms.add(env_from["configMapRef"]["name"])
        if env_from.get("secretRef", {}).get("name"):
            secs.add(env_from["secretRef"]["name"])
    for env in container.get("env") or []:
        value_from = env.get("valueFrom") or {}
        if value_from.get("configMapKeyRef", {}).get("name"):
            cms.add(value_from["configMapKeyRef"]["name"])
        if value_from.get("secretKeyRef", {}).get("name"):
            secs.add(value_from["secretKeyRef"]["name"])
    return cms, secs


def extract_literal_env_from_container(container: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for env in container.get("env") or []:
        key = str(env.get("name") or "").strip()
        if not key or "value" not in env or env.get("value") is None:
            continue
        out[key] = str(env.get("value")).strip()
    return out


def workload_container_context(workload: Dict[str, Any]) -> Dict[str, Any]:
    template_spec = (((workload.get("spec") or {}).get("template") or {}).get("spec")) or {}
    workload_containers = template_spec.get("containers") or []
    workload_init_containers = template_spec.get("initContainers") or []
    containers = workload_containers + workload_init_containers
    inventory = container_inventory(workload_containers, "container") + container_inventory(
        workload_init_containers, "initContainer"
    )

    referenced_configmaps = set()
    referenced_secrets = set()
    for container in containers:
        cms, secs = extract_refs_from_container(container)
        referenced_configmaps.update(cms)
        referenced_secrets.update(secs)

    return {
        "containers": containers,
        "inventory": inventory,
        "referenced_configmaps": referenced_configmaps,
        "referenced_secrets": referenced_secrets,
    }


def select_workloads(
    *,
    deployments: Dict[str, Any],
    statefulsets: Dict[str, Any],
    daemonsets: Dict[str, Any],
    match_re: re.Pattern,
    match_regex: str,
    namespace: str,
) -> Tuple[List[Tuple[str, Dict[str, Any]]], str]:
    workload_sources = workload_source_items(deployments, statefulsets, daemonsets)
    selected = matching_workload_items(workload_sources, match_re)
    if selected:
        return selected, ""

    selected = all_workload_items(workload_sources)
    if selected:
        return (
            selected,
            f"[kmap] info: --match-regex {match_regex!r} matched no workloads in namespace "
            f"{namespace!r}; inspecting all {len(selected)} workloads instead",
        )

    return (
        selected,
        f"[kmap] info: --match-regex {match_regex!r} matched no workloads in namespace "
        f"{namespace!r}; namespace has no Deployment/StatefulSet/DaemonSet workloads",
    )


def workload_source_items(
    deployments: Dict[str, Any],
    statefulsets: Dict[str, Any],
    daemonsets: Dict[str, Any],
) -> List[Tuple[str, Dict[str, Any]]]:
    return [("Deployment", deployments), ("StatefulSet", statefulsets), ("DaemonSet", daemonsets)]


def matching_workload_items(
    workload_sources: List[Tuple[str, Dict[str, Any]]],
    match_re: re.Pattern,
) -> List[Tuple[str, Dict[str, Any]]]:
    return [(kind, item) for kind, data in workload_sources for item in find_related_workloads(data, match_re)]


def all_workload_items(workload_sources: List[Tuple[str, Dict[str, Any]]]) -> List[Tuple[str, Dict[str, Any]]]:
    return [(kind, item) for kind, data in workload_sources for item in data.get("items") or []]


def related_replicasets_by_deployment(replicasets: Dict[str, Any]) -> Dict[str, List[str]]:
    by_deployment: Dict[str, List[str]] = {}
    for item in replicasets.get("items") or []:
        item_name = obj_name(item)
        if not item_name:
            continue
        for ref in ((item.get("metadata") or {}).get("ownerReferences")) or []:
            if ref.get("kind") == "Deployment" and ref.get("name"):
                by_deployment.setdefault(ref["name"], []).append(item_name)
    return {name: sorted(values) for name, values in by_deployment.items()}


def matching_helm_release_names(helm_releases: List[Dict[str, Any]], match_re: re.Pattern) -> List[str]:
    return [item.get("name") for item in helm_releases if item.get("name") and match_re.search(item.get("name", ""))]


__all__ = [
    "all_workload_items",
    "extract_literal_env_from_container",
    "extract_refs_from_container",
    "matching_helm_release_names",
    "matching_workload_items",
    "related_replicasets_by_deployment",
    "select_workloads",
    "workload_container_context",
    "workload_source_items",
]
