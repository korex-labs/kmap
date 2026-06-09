"""Shared object storage bucket candidate collection."""

from typing import Any, Dict, List

from ..kubernetes import configmap_data, decode_secret_data
from .bucket_dedup import dedupe_bucket_candidates
from .bucket_detection import (
    bucket_candidate_from_pair,
    bucket_candidates_from_map,
    bucket_confidence,
    bucket_endpoint_data,
    bucket_from_endpoint_or_value,
    bucket_from_host,
    bucket_from_path,
    bucket_from_plain_value,
    looks_like_bucket_name,
    looks_like_object_storage_endpoint,
    should_consider_bucket_pair,
    should_parse_bucket_endpoint,
)
from .workloads import extract_literal_env_from_container


def workload_bucket_candidates(
    *,
    containers: List[Dict[str, Any]],
    referenced_configmaps: set,
    referenced_secrets: set,
    configmaps: Dict[str, Dict[str, Any]],
    secrets: Dict[str, Dict[str, Any]],
    runtime_env: Dict[str, str],
    vault_env: Dict[str, str],
) -> List[Dict[str, Any]]:
    candidates = bucket_candidates_from_sources(
        [
            (
                referenced_configmap_bucket_values(referenced_configmaps, configmaps),
                "ConfigMap",
                referenced_source_name(referenced_configmaps),
            ),
            (
                referenced_secret_bucket_values(referenced_secrets, secrets),
                "Secret",
                referenced_source_name(referenced_secrets),
            ),
            (container_literal_bucket_env(containers), "Env", "spec"),
            (runtime_env, "Env", "runtime"),
            (vault_env, "VaultEnv", "runtime"),
        ]
    )
    return dedupe_bucket_candidates(candidates)


def referenced_source_name(names: set) -> str:
    return ",".join(sorted(str(name) for name in names if name))


def referenced_configmap_bucket_values(
    referenced_configmaps: set, configmaps: Dict[str, Dict[str, Any]]
) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for cm_name in sorted(referenced_configmaps):
        values.update(configmap_data(configmaps.get(cm_name, {})))
    return values


def referenced_secret_bucket_values(referenced_secrets: set, secrets: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for sec_name in sorted(referenced_secrets):
        values.update(decode_secret_data(secrets.get(sec_name, {})))
    return values


def container_literal_bucket_env(containers: List[Dict[str, Any]]) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for container in containers:
        values.update(extract_literal_env_from_container(container))
    return values


def bucket_candidates_from_sources(sources: List[tuple[Dict[str, str], str, str]]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for data, source, source_name in sources:
        candidates.extend(bucket_candidates_from_map(data, source, source_name))
    return candidates


__all__ = [
    "bucket_candidate_from_pair",
    "bucket_candidates_from_map",
    "bucket_candidates_from_sources",
    "bucket_confidence",
    "bucket_endpoint_data",
    "bucket_from_endpoint_or_value",
    "bucket_from_host",
    "bucket_from_path",
    "bucket_from_plain_value",
    "container_literal_bucket_env",
    "dedupe_bucket_candidates",
    "looks_like_bucket_name",
    "looks_like_object_storage_endpoint",
    "referenced_configmap_bucket_values",
    "referenced_secret_bucket_values",
    "should_consider_bucket_pair",
    "should_parse_bucket_endpoint",
    "workload_bucket_candidates",
]
