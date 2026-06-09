"""Bucket inventory row model and merge helpers."""

import re
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class BucketUsageRow:
    bucket: str
    endpoint: str
    confidence: str
    cluster: str
    product: str
    namespace: str
    project: str
    workload: str
    source: str
    source_var: str
    repository: str
    owner_team: str
    report_key: str = ""
    product_title: str = ""
    last_seen_at: str = ""
    repository_archived: str = ""


def sort_bucket_usage_rows(rows: list[BucketUsageRow]) -> list[BucketUsageRow]:
    return sorted(
        rows,
        key=lambda row: (
            row.bucket.lower(),
            row.endpoint.lower(),
            row.product.lower(),
            row.namespace.lower(),
            row.workload.lower(),
            row.source_var.lower(),
        ),
    )


def merge_bucket_usage_rows(rows: list[BucketUsageRow]) -> list[BucketUsageRow]:
    merged: dict[tuple[str, str, str, str], BucketUsageRow] = {}
    for row in rows:
        key = bucket_usage_merge_key(row)
        existing = merged.get(key)
        if existing is None:
            merged[key] = row
        else:
            merged[key] = merge_bucket_usage_row(existing, row)
    return list(merged.values())


def bucket_usage_merge_key(row: BucketUsageRow) -> tuple[str, str, str, str]:
    owner = row.repository or f"{row.product}:{row.namespace}"
    signal = row.bucket or row.endpoint
    family = "" if row.bucket else ",".join(sorted(bucket_source_families(row.source_var)))
    return (owner.lower(), signal.lower(), row.namespace.lower(), family)


def merge_bucket_usage_row(left: BucketUsageRow, right: BucketUsageRow) -> BucketUsageRow:
    preferred = max((left, right), key=bucket_usage_row_quality)
    source_vars = sorted({part for row in (left, right) for part in row.source_var.split(", ") if part})
    return replace(
        preferred,
        source_var=", ".join(source_vars),
        endpoint=preferred.endpoint or left.endpoint or right.endpoint,
        bucket=preferred.bucket or left.bucket or right.bucket,
        confidence=best_confidence(left.confidence, right.confidence),
    )


def bucket_usage_row_quality(row: BucketUsageRow) -> tuple[int, int, int]:
    return (
        confidence_rank(row.confidence),
        1 if row.endpoint else 0,
        1 if row.bucket else 0,
    )


def confidence_rank(confidence: str) -> int:
    return {"low": 1, "medium": 2, "high": 3}.get(confidence.lower(), 0)


def best_confidence(left: str, right: str) -> str:
    return max((left, right), key=confidence_rank)


def suppress_redundant_location_only_rows(rows: list[BucketUsageRow]) -> list[BucketUsageRow]:
    named_families = {
        bucket_context_key(row, family)
        for row in rows
        if row.bucket
        for family in bucket_source_families(row.source_var)
    }
    return [
        row
        for row in rows
        if row.bucket
        or not any(
            bucket_context_key(row, family) in named_families for family in bucket_source_families(row.source_var)
        )
    ]


def bucket_context_key(row: BucketUsageRow, source_family: str) -> tuple[str, str, str, str]:
    owner = row.repository or f"{row.product}:{row.namespace}"
    return (owner.lower(), row.namespace.lower(), row.source.lower(), source_family)


def bucket_source_families(source_var: str) -> set[str]:
    return {bucket_source_family(part) for part in source_var.split(", ") if bucket_source_family(part)}


def bucket_source_family(source_var: str) -> str:
    tokens = [token for token in re.split(r"_+", source_var.upper()) if token]
    cut_tokens = []
    for token in tokens:
        if token in {"BASE", "BUCKET", "ENDPOINT", "HOST", "NAME", "URL", "URI"}:
            break
        cut_tokens.append(token)
    return "_".join(cut_tokens)


def bucket_row_dict(row: BucketUsageRow) -> dict[str, str]:
    payload = {
        "bucket": row.bucket,
        "endpoint": row.endpoint,
        "confidence": row.confidence,
        "cluster": row.cluster,
        "product": row.product,
        "namespace": row.namespace,
        "project": row.project,
        "workload": row.workload,
        "source": row.source,
        "source_var": row.source_var,
        "repository": row.repository,
        "owner_team": row.owner_team,
        "report_key": row.report_key,
        "product_title": row.product_title,
    }
    if row.last_seen_at:
        payload["last_seen_at"] = row.last_seen_at
    if row.repository_archived:
        payload["repository_archived"] = row.repository_archived
    return payload


__all__ = [
    "BucketUsageRow",
    "best_confidence",
    "bucket_context_key",
    "bucket_row_dict",
    "bucket_source_families",
    "bucket_source_family",
    "bucket_usage_merge_key",
    "bucket_usage_row_quality",
    "confidence_rank",
    "merge_bucket_usage_row",
    "merge_bucket_usage_rows",
    "sort_bucket_usage_rows",
    "suppress_redundant_location_only_rows",
]
