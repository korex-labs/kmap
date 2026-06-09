"""Previous-report fallback helpers for runtime dependency candidates."""

import argparse
from pathlib import Path
from typing import Any, Dict, List

from ...io import load_json_file

RUNTIME_CANDIDATE_SOURCES = {"Env", "VaultEnv"}
RUNTIME_CANDIDATE_SOURCE_NAME = "runtime"


def previous_runtime_candidates_by_workload(
    args: argparse.Namespace, out_dir: Path
) -> Dict[tuple[str, str, str, str], List[Dict[str, Any]]]:
    previous_report = load_json_file(namespace_report_path(args, out_dir), {})
    if not isinstance(previous_report, dict):
        return {}

    out: Dict[tuple[str, str, str, str], List[Dict[str, Any]]] = {}
    for workload in previous_report.get("workloads") or []:
        if not isinstance(workload, dict):
            continue
        key = workload_cache_key(workload)
        candidates = runtime_candidates(workload.get("dependency_candidates") or [])
        if key and candidates:
            out[key] = candidates
    return out


def namespace_report_path(args: argparse.Namespace, out_dir: Path) -> Path:
    report_stem = getattr(args, "report_stem", "") or args.namespace
    return out_dir / f"{report_stem}.report.json"


def workload_cache_key(workload: Dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(workload.get("cluster") or ""),
        str(workload.get("namespace") or ""),
        str(workload.get("kind") or ""),
        str(workload.get("service_name") or ""),
    )


def is_runtime_candidate(candidate: Dict[str, Any]) -> bool:
    return (
        isinstance(candidate, dict)
        and candidate.get("source") in RUNTIME_CANDIDATE_SOURCES
        and candidate.get("source_name") == RUNTIME_CANDIDATE_SOURCE_NAME
    )


def runtime_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [candidate for candidate in candidates or [] if is_runtime_candidate(candidate)]


def cached_runtime_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    cached_candidate = dict(candidate)
    cached_candidate["cache"] = True
    cached_candidate["cache_source"] = "previous_report"
    return cached_candidate


def with_cached_runtime_candidates(
    candidates: List[Dict[str, Any]],
    previous_candidates: Dict[tuple[str, str, str, str], List[Dict[str, Any]]],
    workload_key: tuple[str, str, str, str],
) -> List[Dict[str, Any]]:
    if any(is_runtime_candidate(candidate) for candidate in candidates):
        return candidates

    cached = previous_candidates.get(workload_key) or []
    if not cached:
        return candidates

    out = list(candidates)
    out.extend(cached_runtime_candidate(candidate) for candidate in cached)
    return out


__all__ = [
    "cached_runtime_candidate",
    "is_runtime_candidate",
    "namespace_report_path",
    "previous_runtime_candidates_by_workload",
    "runtime_candidates",
    "with_cached_runtime_candidates",
    "workload_cache_key",
]
