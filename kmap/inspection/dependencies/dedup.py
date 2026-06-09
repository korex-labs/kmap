"""Dependency candidate dedupe policy."""

from typing import Any, Dict, List, Tuple

DEPENDENCY_SOURCE_RANK = {"VaultEnv": 4, "Env": 3, "Secret": 2, "ConfigMap": 1}


def dedupe_dependency_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for candidate in candidates:
        dedupe_key = dependency_candidate_dedupe_key(candidate)
        existing = best.get(dedupe_key)
        if existing is None:
            best[dedupe_key] = candidate
            continue
        if dependency_candidate_source_rank(candidate) > dependency_candidate_source_rank(existing):
            best[dedupe_key] = candidate
    return sorted(best.values(), key=dependency_candidate_sort_key)


def dependency_candidate_dedupe_key(candidate: Dict[str, Any]) -> Tuple[str, str]:
    return (candidate.get("var") or "", candidate.get("key") or "")


def dependency_candidate_source_rank(candidate: Dict[str, Any]) -> int:
    return DEPENDENCY_SOURCE_RANK.get(candidate.get("source"), 0)


def dependency_candidate_sort_key(candidate: Dict[str, Any]) -> Tuple[str, str]:
    return (candidate.get("var") or "", candidate.get("key") or "")


__all__ = [
    "DEPENDENCY_SOURCE_RANK",
    "dedupe_dependency_candidates",
    "dependency_candidate_dedupe_key",
    "dependency_candidate_sort_key",
    "dependency_candidate_source_rank",
]
