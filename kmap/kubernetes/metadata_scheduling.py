"""Kubernetes pod scheduling metadata."""

from typing import Any, Dict, List

from ..config import clean_metadata_string
from .metadata_values import metadata_scalar_fields, pod_spec

SCHEDULING_SCALAR_FIELDS = (
    ("priorityClassName", "priority_class"),
    ("schedulerName", "scheduler_name"),
    ("runtimeClassName", "runtime_class"),
)


def workload_scheduling_context(workload: Dict[str, Any]) -> Dict[str, str]:
    spec = pod_spec(workload)
    out: Dict[str, str] = metadata_scalar_fields(spec, SCHEDULING_SCALAR_FIELDS)
    node_selector = scheduling_map_summary(spec.get("nodeSelector") or {})
    if node_selector:
        out["node_selector"] = node_selector

    tolerations = toleration_summaries(spec.get("tolerations") or [])
    if tolerations:
        out["tolerations"] = ", ".join(tolerations)

    affinity = affinity_summary(spec.get("affinity") or {})
    if affinity:
        out["affinity"] = affinity

    topology_spread = topology_spread_summary(spec.get("topologySpreadConstraints") or [])
    if topology_spread:
        out["topology_spread"] = topology_spread
    return out


def scheduling_map_summary(values: Dict[str, Any]) -> str:
    parts = []
    for key, value in sorted((values or {}).items()):
        key = clean_metadata_string(key)
        value = clean_metadata_string(value)
        if key and value:
            parts.append(f"{key}={value}")
    return ", ".join(parts)


def toleration_summaries(tolerations: List[Dict[str, Any]]) -> List[str]:
    out = []
    for toleration in tolerations or []:
        key = clean_metadata_string(toleration.get("key")) or "*"
        operator = clean_metadata_string(toleration.get("operator")) or "Equal"
        value = clean_metadata_string(toleration.get("value"))
        effect = clean_metadata_string(toleration.get("effect"))
        summary = f"{key} {operator}"
        if value:
            summary = f"{summary} {value}"
        if effect:
            summary = f"{summary} ({effect})"
        out.append(summary)
    return sorted(set(out))


def affinity_summary(affinity: Dict[str, Any]) -> str:
    parts = []
    for key, label in (
        ("nodeAffinity", "node"),
        ("podAffinity", "pod"),
        ("podAntiAffinity", "podAnti"),
    ):
        if (affinity or {}).get(key):
            parts.append(label)
    return ", ".join(parts)


def topology_spread_summary(constraints: List[Dict[str, Any]]) -> str:
    out = []
    for constraint in constraints or []:
        topology_key = clean_metadata_string(constraint.get("topologyKey"))
        action = clean_metadata_string(constraint.get("whenUnsatisfiable"))
        if topology_key and action:
            out.append(f"{topology_key} ({action})")
        elif topology_key:
            out.append(topology_key)
    return ", ".join(sorted(set(out)))


__all__ = [
    "SCHEDULING_SCALAR_FIELDS",
    "affinity_summary",
    "scheduling_map_summary",
    "toleration_summaries",
    "topology_spread_summary",
    "workload_scheduling_context",
]
