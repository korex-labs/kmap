"""Container inventory helpers for normalized architecture models."""

from typing import Any, Dict, List

from ..config import clean_metadata_string


def architecture_container_inventory(svc: Dict[str, Any]) -> List[Dict[str, Any]]:
    containers = [c for c in (svc.get("containers") or []) if clean_metadata_string(c.get("name"))]
    if containers:
        return containers
    return [{"name": svc.get("service_name") or "workload", "kind": "workload"}]


__all__ = ["architecture_container_inventory"]
