"""Bucket candidate merge and dedupe policy."""

import re
from typing import Any, Dict, List

from .bucket_detection import bucket_confidence

BUCKET_SOURCE_RANK = {"VaultEnv": 4, "Env": 3, "Secret": 2, "ConfigMap": 1}


def dedupe_bucket_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best: Dict[tuple[str, str, str], Dict[str, Any]] = {}
    for candidate in merge_related_bucket_candidates(candidates):
        key = bucket_candidate_dedupe_key(candidate)
        existing = best.get(key)
        if existing is None or bucket_candidate_source_rank(candidate) > bucket_candidate_source_rank(existing):
            best[key] = candidate
    return sorted(best.values(), key=bucket_candidate_sort_key)


def bucket_candidate_dedupe_key(candidate: Dict[str, Any]) -> tuple[str, str, str]:
    return (candidate.get("var") or "", candidate.get("bucket") or "", candidate.get("endpoint") or "")


def bucket_candidate_source_rank(candidate: Dict[str, Any]) -> int:
    return BUCKET_SOURCE_RANK.get(candidate.get("source"), 0)


def bucket_candidate_sort_key(candidate: Dict[str, Any]) -> tuple[str, str, str]:
    return (candidate.get("bucket") or "", candidate.get("endpoint") or "", candidate.get("var") or "")


def merge_related_bucket_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped, passthrough = grouped_bucket_candidates(candidates)
    merged = list(passthrough)
    for group in grouped.values():
        merged.extend(merge_bucket_candidate_group(group))
    return merged


def grouped_bucket_candidates(
    candidates: List[Dict[str, Any]],
) -> tuple[Dict[tuple[str, str, str], List[Dict[str, Any]]], List[Dict[str, Any]]]:
    grouped: Dict[tuple[str, str, str], List[Dict[str, Any]]] = {}
    passthrough: List[Dict[str, Any]] = []
    for candidate in candidates:
        key = bucket_candidate_group_key(candidate)
        if key:
            grouped.setdefault(key, []).append(candidate)
        else:
            passthrough.append(candidate)
    return grouped, passthrough


def bucket_candidate_group_key(candidate: Dict[str, Any]) -> tuple[str, str, str]:
    family = bucket_candidate_family(str(candidate.get("var") or ""))
    return (str(candidate.get("source") or ""), str(candidate.get("source_name") or ""), family) if family else ()


def merge_bucket_candidate_group(group: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    bucket_candidates = [candidate for candidate in group if candidate.get("bucket")]
    endpoint_candidates = [candidate for candidate in group if candidate.get("endpoint")]
    if not bucket_candidates or not endpoint_candidates:
        return group
    best_bucket = max(bucket_candidates, key=bucket_candidate_quality)
    best_endpoint = max(endpoint_candidates, key=bucket_candidate_quality)
    if best_bucket is best_endpoint:
        return [best_bucket, *remaining_bucket_candidates(group, {id(best_bucket)})]
    consumed = {id(best_bucket), id(best_endpoint)}
    return [merged_bucket_candidate(best_bucket, best_endpoint), *remaining_bucket_candidates(group, consumed)]


def merged_bucket_candidate(best_bucket: Dict[str, Any], best_endpoint: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **best_bucket,
        "endpoint": best_endpoint.get("endpoint") or best_bucket.get("endpoint") or "",
        "confidence": bucket_confidence(
            str(best_bucket.get("var") or ""),
            str(best_bucket.get("bucket") or ""),
            str(best_endpoint.get("endpoint") or ""),
        ),
        "var": ", ".join(sorted({str(best_bucket.get("var") or ""), str(best_endpoint.get("var") or "")})),
    }


def remaining_bucket_candidates(group: List[Dict[str, Any]], consumed_ids: set[int]) -> List[Dict[str, Any]]:
    return [candidate for candidate in group if id(candidate) not in consumed_ids]


def bucket_candidate_quality(candidate: Dict[str, Any]) -> tuple[int, int]:
    return (1 if candidate.get("bucket") else 0, 1 if candidate.get("endpoint") else 0)


def bucket_candidate_family(var: str) -> str:
    tokens = [token for token in re.split(r"_+", var.upper()) if token]
    family_tokens = []
    for token in tokens:
        if token in {"AUTH", "BASE", "BUCKET", "ENDPOINT", "HOST", "NAME", "URL", "URI"}:
            break
        family_tokens.append(token)
    return "_".join(family_tokens)


__all__ = [
    "bucket_candidate_dedupe_key",
    "bucket_candidate_family",
    "bucket_candidate_group_key",
    "bucket_candidate_quality",
    "bucket_candidate_sort_key",
    "bucket_candidate_source_rank",
    "dedupe_bucket_candidates",
    "grouped_bucket_candidates",
    "merge_bucket_candidate_group",
    "merge_related_bucket_candidates",
    "merged_bucket_candidate",
    "remaining_bucket_candidates",
]
