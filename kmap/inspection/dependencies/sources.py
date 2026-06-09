"""Dependency source collection from inspected Kubernetes data."""

from typing import Any, Dict, List, Tuple

from ...kubernetes import configmap_data, decode_secret_data
from ..workloads import extract_literal_env_from_container


def workload_dependency_sources(
    *,
    containers: List[Dict[str, Any]],
    referenced_configmaps: set,
    referenced_secrets: set,
    configmaps: Dict[str, Dict[str, Any]],
    secrets: Dict[str, Dict[str, Any]],
    runtime_env: Dict[str, str],
    vault_env: Dict[str, str],
) -> List[Tuple[Dict[str, str], str, str]]:
    return [
        (
            referenced_configmap_values(referenced_configmaps, configmaps),
            "ConfigMap",
            referenced_source_name(referenced_configmaps),
        ),
        (
            referenced_secret_values(referenced_secrets, secrets),
            "Secret",
            referenced_source_name(referenced_secrets),
        ),
        (container_literal_env(containers), "Env", "spec"),
        (runtime_env, "Env", "runtime"),
        (vault_env, "VaultEnv", "runtime"),
    ]


def referenced_source_name(referenced_names: set) -> str:
    return ",".join(sorted(referenced_names)) or "referenced"


def referenced_configmap_values(
    referenced_configmaps: set,
    configmaps: Dict[str, Dict[str, Any]],
) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for cm_name in sorted(referenced_configmaps):
        values.update(configmap_data(configmaps.get(cm_name, {})))
    return values


def referenced_secret_values(
    referenced_secrets: set,
    secrets: Dict[str, Dict[str, Any]],
) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for sec_name in sorted(referenced_secrets):
        values.update(decode_secret_data(secrets.get(sec_name, {})))
    return values


def container_literal_env(containers: List[Dict[str, Any]]) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for container in containers:
        values.update(extract_literal_env_from_container(container))
    return values


__all__ = [
    "container_literal_env",
    "referenced_configmap_values",
    "referenced_secret_values",
    "referenced_source_name",
    "workload_dependency_sources",
]
