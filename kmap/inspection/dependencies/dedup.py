"""Dependency candidate dedupe policy."""

from typing import Any

from ..source_rank import SOURCE_RANK as DEPENDENCY_SOURCE_RANK
from ..source_rank import source_rank


def dedupe_dependency_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in candidates:
        dedupe_key = dependency_candidate_dedupe_key(candidate)
        existing = best.get(dedupe_key)
        if existing is None:
            best[dedupe_key] = candidate
            continue
        if dependency_candidate_source_rank(candidate) > dependency_candidate_source_rank(existing):
            best[dedupe_key] = candidate
    return sorted(best.values(), key=dependency_candidate_sort_key)


def dependency_candidate_dedupe_key(candidate: dict[str, Any]) -> tuple[str, str]:
    return (candidate.get("var") or "", candidate.get("key") or "")


def dependency_candidate_source_rank(candidate: dict[str, Any]) -> int:
    return source_rank(candidate.get("source"))


def dependency_candidate_sort_key(candidate: dict[str, Any]) -> tuple[str, str]:
    return (candidate.get("var") or "", candidate.get("key") or "")


__all__ = [
    "DEPENDENCY_SOURCE_RANK",
    "dedupe_dependency_candidates",
    "dependency_candidate_dedupe_key",
    "dependency_candidate_sort_key",
    "dependency_candidate_source_rank",
]
