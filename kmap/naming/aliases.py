"""Alias and reference-name variants used when matching Kubernetes data."""

import re
from typing import List, Optional

from ..config import slug_name
from ..hostish import parse_hostish

NAMESPACE_ALIAS_IGNORED_TOKENS = (
    "prod",
    "production",
    "stage",
    "staging",
    "test",
    "qa",
    "dev",
    "uat",
)
MIN_NAMESPACED_HOST_LABELS = 2


def _sorted_non_empty(values: set[str]) -> List[str]:
    return sorted(value for value in values if value)


def _raw_lower(value: str) -> str:
    return (value or "").strip().lower()


def _service_alias_rewrites(system_naming_config: Optional[dict] = None) -> List[dict]:
    config = system_naming_config or {}
    return list(((config.get("service_aliases") or {}).get("rewrites")) or [])


def _rewritten_service_aliases(value: str, system_naming_config: Optional[dict] = None) -> List[str]:
    raw = _raw_lower(value)
    if not raw:
        return []

    vals = set()
    for rewrite in _service_alias_rewrites(system_naming_config):
        match_regex = str(rewrite.get("match_regex") or "")
        replace = str(rewrite.get("replace") or "")
        if not match_regex:
            continue
        try:
            rewritten = re.sub(match_regex, replace, raw)
        except re.error:
            continue
        if rewritten and rewritten != raw:
            vals.add(rewritten)
    return _sorted_non_empty(vals)


def alias_variants(name: str, namespace: str, cluster_ip: Optional[str] = None) -> List[str]:
    vals = {
        name.lower(),
        f"{name}.{namespace}".lower(),
        f"{name}.{namespace}.svc".lower(),
        f"{name}.{namespace}.svc.cluster.local".lower(),
    }
    if cluster_ip:
        vals.add(cluster_ip.lower())
    return _sorted_non_empty(vals)


def service_name_alias_variants(value: str, system_naming_config: Optional[dict] = None) -> List[str]:
    raw = _raw_lower(value)
    if not raw:
        return []

    vals = {raw}

    parsed = parse_hostish(raw)
    if parsed:
        host, port, _ = parsed
        for rewritten_host in _rewritten_service_aliases(host, system_naming_config):
            vals.add(f"{rewritten_host}:{port}" if port else rewritten_host)
    else:
        vals.update(_rewritten_service_aliases(raw, system_naming_config))

    return _sorted_non_empty(vals)


def namespace_alias_variants(namespace: str, project: str = "") -> List[str]:
    raw = _raw_lower(namespace)
    project_slug = slug_name(project).lower() if project else ""
    if not raw:
        return []

    vals = {raw}
    parts = [p for p in raw.split("-") if p]
    if parts:
        stripped_parts = [p for p in parts if p not in NAMESPACE_ALIAS_IGNORED_TOKENS]
        if stripped_parts and stripped_parts != parts:
            vals.add("-".join(stripped_parts))

    expanded_vals = set(vals)
    if project_slug:
        prefix = f"{project_slug}-"
        for value in vals:
            if value.startswith(prefix):
                expanded_vals.add(value[len(prefix) :])
            else:
                expanded_vals.add(prefix + value)
    vals = expanded_vals
    return _sorted_non_empty(vals)


def service_reference_variants(value: str, project: str = "", system_naming_config: Optional[dict] = None) -> List[str]:
    raw = _raw_lower(value)
    if not raw:
        return []

    vals = set(service_name_alias_variants(raw, system_naming_config))
    parsed = parse_hostish(raw)
    if not parsed:
        return _sorted_non_empty(vals)

    host, port, _ = parsed
    host_labels = host.split(".")
    if len(host_labels) < MIN_NAMESPACED_HOST_LABELS:
        return _sorted_non_empty(vals)

    service_label = host_labels[0]
    namespace_label = host_labels[1]
    rest = host_labels[2:]

    service_labels = service_name_alias_variants(service_label, system_naming_config)
    namespace_labels = namespace_alias_variants(namespace_label, project)

    for svc_label in service_labels:
        for ns_label in namespace_labels:
            candidate_host = ".".join([svc_label, ns_label, *rest])
            vals.add(f"{candidate_host}:{port}" if port else candidate_host)

    return _sorted_non_empty(vals)


def short_service_name_variants(service_name: str) -> List[str]:
    raw = _raw_lower(service_name)
    if not raw:
        return []

    vals = {raw}
    for prefix in ("prod-", "stage-", "staging-", "dev-", "test-", "qa-"):
        if raw.startswith(prefix) and len(raw) > len(prefix):
            vals.add(raw[len(prefix) :])
    return _sorted_non_empty(vals)


__all__ = [
    "NAMESPACE_ALIAS_IGNORED_TOKENS",
    "alias_variants",
    "namespace_alias_variants",
    "service_name_alias_variants",
    "service_reference_variants",
    "short_service_name_variants",
]
