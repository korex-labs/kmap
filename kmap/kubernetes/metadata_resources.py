"""Kubernetes container resource metadata."""

from typing import Any, Dict

from ..config import clean_metadata_string


def container_resource_inventory(container: Dict[str, Any]) -> Dict[str, str]:
    resources = (container or {}).get("resources") or {}
    requests = resources.get("requests") or {}
    limits = resources.get("limits") or {}
    out: Dict[str, str] = {}
    for source, prefix in ((requests, "request"), (limits, "limit")):
        for resource in ("cpu", "memory"):
            value = clean_metadata_string(source.get(resource))
            if value:
                out[f"{prefix}_{resource}"] = value
    return out


__all__ = ["container_resource_inventory"]
