"""Row normalization and aggregation helpers for cluster inventory."""

from collections import defaultdict

from .row_payloads import (
    BucketRowPayload,
    NamespaceRowPayload,
    RepositoryRowPayload,
    SerializedRow,
    namespace_row_with_labels,
    normalize_string_dict,
    row_quality,
)


def sorted_namespace_rows(namespace_rows: dict[str, NamespaceRowPayload]) -> list[NamespaceRowPayload]:
    return sorted(namespace_rows.values(), key=lambda row: (row.get("product", ""), row.get("namespace", "")))


def sorted_bucket_rows(
    bucket_rows: dict[tuple[str, str, str, str, str], BucketRowPayload],
) -> list[BucketRowPayload]:
    return sorted(
        bucket_rows.values(),
        key=lambda row: (
            row.get("bucket", ""),
            row.get("endpoint", ""),
            row.get("namespace", ""),
            row.get("repository", ""),
        ),
    )


def rows_with_last_seen(rows: list[SerializedRow], last_seen_at: str) -> list[SerializedRow]:
    if not last_seen_at:
        return rows
    return [{**row, "last_seen_at": row.get("last_seen_at") or last_seen_at} for row in rows]


def merge_namespace_rows(target: dict[str, NamespaceRowPayload], rows: list[SerializedRow]) -> None:
    for row in rows:
        namespace = str(row.get("namespace") or "")
        if not namespace:
            continue
        normalized = normalize_string_dict(row)
        existing = target.get(namespace)
        if existing is None or row_quality(normalized) > row_quality(existing):
            target[namespace] = namespace_row_with_labels(normalized, existing)
        elif normalized.get("labels") and not existing.get("labels"):
            existing["labels"] = normalized["labels"]


def merge_bucket_rows(
    target: dict[tuple[str, str, str, str, str], BucketRowPayload],
    rows: list[SerializedRow],
) -> None:
    for row in rows:
        normalized = normalize_string_dict(row)
        target.setdefault(bucket_key(normalized), normalized)


def bucket_key(row: SerializedRow) -> tuple[str, str, str, str, str]:
    return (
        row.get("namespace", "").lower(),
        row.get("repository", "").lower(),
        row.get("bucket", "").lower(),
        row.get("endpoint", "").lower(),
        row.get("source_var", "").lower(),
    )


def repositories_for_cluster_namespaces(namespaces: list[NamespaceRowPayload]) -> list[RepositoryRowPayload]:
    by_repo: dict[str, list[NamespaceRowPayload]] = defaultdict(list)
    for row in namespaces:
        repository = row.get("repository", "")
        if repository:
            by_repo[repository].append(row)
    repositories = []
    for repository, rows in by_repo.items():
        best = max(rows, key=row_quality)
        repositories.append(
            {
                "repository": repository,
                "namespaces": sorted({row.get("namespace", "") for row in rows if row.get("namespace")}),
                "products": sorted({row.get("product", "") for row in rows if row.get("product")}),
                "owner_team": best.get("owner_team", ""),
                "repository_id": best.get("repository_id", ""),
                "repository_name": best.get("repository_name", ""),
                "repository_path": best.get("repository_path", ""),
                "repository_group": best.get("repository_group", ""),
                "repository_archived": best.get("repository_archived", ""),
            }
        )
    return sorted(repositories, key=lambda row: row["repository"].lower())


__all__ = [
    "bucket_key",
    "merge_bucket_rows",
    "merge_namespace_rows",
    "normalize_string_dict",
    "repositories_for_cluster_namespaces",
    "row_quality",
    "rows_with_last_seen",
    "sorted_bucket_rows",
    "sorted_namespace_rows",
]
