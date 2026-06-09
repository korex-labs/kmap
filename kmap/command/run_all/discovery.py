"""Namespace and discovery helper functions shared by inspect and run-all."""

import hashlib
from typing import Dict, List

from ...config import slug_name


def split_csv_args(values: List[str]) -> List[str]:
    parts: List[str] = []
    for raw in values or []:
        parts.extend(part.strip() for part in (raw or "").split(","))
    return [part for part in parts if part]


def parse_namespace_args(values: List[str]) -> List[str]:
    namespaces: List[str] = []
    seen = set()
    for namespace in split_csv_args(values):
        if namespace in seen:
            continue
        seen.add(namespace)
        namespaces.append(namespace)
    if not namespaces:
        raise SystemExit("At least one namespace must be provided via -n/--namespace")
    return namespaces


def parse_namespace_project_args(values: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for item in split_csv_args(values):
        if "=" not in item:
            raise SystemExit(f"Invalid --namespace-project value '{item}', expected namespace=project")
        ns, project = item.split("=", 1)
        ns = ns.strip()
        project = project.strip()
        if not ns or not project:
            raise SystemExit(f"Invalid --namespace-project value '{item}', expected namespace=project")
        out[ns] = project
    return out


def discovery_target_identity(target: Dict[str, str]) -> str:
    context = str((target or {}).get("context") or "").strip()
    kubeconfig = str((target or {}).get("kubeconfig") or "").strip()
    if context and kubeconfig:
        kubeconfig_hash = hashlib.sha1(kubeconfig.encode("utf-8")).hexdigest()[:8]
        return f"{context}@{kubeconfig_hash}"
    return context or kubeconfig


def report_stem_for_namespace(namespace: str, target: Dict[str, str], use_target_report_stems: bool) -> str:
    identity = discovery_target_identity(target)
    if use_target_report_stems and identity:
        return f"{slug_name(identity)}__{namespace}"
    return namespace


__all__ = [
    "discovery_target_identity",
    "parse_namespace_args",
    "parse_namespace_project_args",
    "report_stem_for_namespace",
    "split_csv_args",
]
