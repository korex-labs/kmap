"""Naming context and workload naming/filtering helpers."""

import argparse
import os
from dataclasses import dataclass
from typing import Any, Dict

from ..config import slug_name


@dataclass
class NamingContext:
    org: str
    product: str
    project: str
    env: str

    def base(self) -> str:
        return f"{slug_name(self.org)}-{slug_name(self.product)}-{slug_name(self.project)}"

    def software_system_name(self) -> str:
        return self.base()

    def container_name(self, subsystem: str) -> str:
        name = f"{self.base()}-{slug_name(subsystem)}"
        if self.env:
            name = f"{name}-{slug_name(self.env)}"
        return name


def naming_context_from_args(args: argparse.Namespace) -> NamingContext:
    return NamingContext(
        org=getattr(args, "org", "") or os.environ.get("KMAP_ORG", "org"),
        product=getattr(args, "product", "") or os.environ.get("KMAP_PRODUCT", "product"),
        project=getattr(args, "project", "") or os.environ.get("KMAP_PROJECT", ""),
        env=getattr(args, "env", "") or os.environ.get("KMAP_ENV", ""),
    )


def container_subsystem_name(svc: Dict[str, Any]) -> str:
    parts = [svc.get("service_name") or "workload"]
    namespace = svc.get("namespace") or ""
    cluster = svc.get("cluster") or ""
    if namespace:
        parts.append(namespace)
    if cluster:
        parts.append(cluster)
    return "-".join(parts)


def should_model_workload(svc: Dict[str, Any]) -> bool:
    name = (svc.get("service_name") or "").strip().lower()
    selector = {str(k).lower(): str(v).lower() for k, v in (svc.get("selector") or {}).items()}
    entrypoints = svc.get("entrypoints") or []
    deps = svc.get("dependency_candidates") or []

    operator_markers = (
        "operator",
        "controller",
        "controller-manager",
    )
    operatorish_name = any(marker in name for marker in operator_markers)
    operatorish_label = any(any(marker in value for marker in operator_markers) for value in selector.values())

    return not ((operatorish_name or operatorish_label) and not entrypoints and not deps)


__all__ = [
    "NamingContext",
    "container_subsystem_name",
    "naming_context_from_args",
    "should_model_workload",
]
