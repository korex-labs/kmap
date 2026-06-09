"""Dependency candidate extraction and sanitization helpers."""

from typing import Any, Dict, List, Tuple

from ..dependency_sanitization import (
    SENSITIVE_VAR_RE,
    mock_database_metadata,
    mock_dependency_candidate_fields,
    mock_dns_label,
    mock_host,
    mock_hostish_value,
    mock_identity_label,
    mock_label,
    sanitize_dependency_candidate,
    sanitize_dependency_source_name,
)
from .candidates import (
    IGNORE_KEY_RE,
    SUSPECT_KEY_RE,
    BaseDependencyCandidateInput,
    DependencyCandidateInput,
    attach_dependency_database_metadata,
    base_dependency_candidate,
    dedupe_dependency_candidates,
    dependency_candidate,
    dependency_candidate_dedupe_key,
    dependency_candidate_from_input,
    dependency_candidate_from_raw_part,
    dependency_candidate_key,
    dependency_candidate_sort_key,
    dependency_candidate_source_rank,
    dependency_candidates_from_map,
    dependency_candidates_from_pair,
    dependency_value_parts,
    parse_dependency_hostish,
    parse_env_block,
    should_consider_dependency_pair,
)
from .internal import dependency_alias_key, mark_internal_dependency_candidates
from .sources import (
    container_literal_env,
    referenced_configmap_values,
    referenced_secret_values,
    referenced_source_name,
    workload_dependency_sources,
)


def workload_dependency_candidates(
    *,
    containers: List[Dict[str, Any]],
    referenced_configmaps: set,
    referenced_secrets: set,
    configmaps: Dict[str, Dict[str, Any]],
    secrets: Dict[str, Dict[str, Any]],
    runtime_env: Dict[str, str],
    vault_env: Dict[str, str],
    internal_alias_to_service: Dict[str, List[str]],
) -> List[Dict[str, Any]]:
    sources = workload_dependency_sources(
        containers=containers,
        referenced_configmaps=referenced_configmaps,
        referenced_secrets=referenced_secrets,
        configmaps=configmaps,
        secrets=secrets,
        runtime_env=runtime_env,
        vault_env=vault_env,
    )
    candidates = dependency_candidates_from_sources(sources)
    candidates = dedupe_dependency_candidates(candidates)
    return mark_internal_dependency_candidates(candidates, internal_alias_to_service)


def dependency_candidates_from_sources(
    sources: List[Tuple[Dict[str, str], str, str]],
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for data, source, source_name in sources:
        candidates.extend(dependency_candidates_from_map(data, source, source_name))
    return candidates


__all__ = [
    "IGNORE_KEY_RE",
    "SENSITIVE_VAR_RE",
    "SUSPECT_KEY_RE",
    "BaseDependencyCandidateInput",
    "DependencyCandidateInput",
    "attach_dependency_database_metadata",
    "base_dependency_candidate",
    "container_literal_env",
    "dedupe_dependency_candidates",
    "dependency_alias_key",
    "dependency_candidate",
    "dependency_candidate_dedupe_key",
    "dependency_candidate_from_input",
    "dependency_candidate_from_raw_part",
    "dependency_candidate_key",
    "dependency_candidate_sort_key",
    "dependency_candidate_source_rank",
    "dependency_candidates_from_map",
    "dependency_candidates_from_pair",
    "dependency_candidates_from_sources",
    "dependency_value_parts",
    "mark_internal_dependency_candidates",
    "mock_database_metadata",
    "mock_dependency_candidate_fields",
    "mock_dns_label",
    "mock_host",
    "mock_hostish_value",
    "mock_identity_label",
    "mock_label",
    "parse_dependency_hostish",
    "parse_env_block",
    "referenced_configmap_values",
    "referenced_secret_values",
    "referenced_source_name",
    "sanitize_dependency_candidate",
    "sanitize_dependency_source_name",
    "should_consider_dependency_pair",
    "workload_dependency_candidates",
    "workload_dependency_sources",
]
