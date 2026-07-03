"""Shared helpers for serialized inventory row payloads."""

from typing import Any, NotRequired, TypeAlias, TypedDict

SerializedRow: TypeAlias = dict[str, Any]


class NamespaceRowPayload(TypedDict, total=False):
    cluster: str
    namespace: str
    stage: str
    labels: dict[str, str]
    product: str
    product_title: str
    repository: str
    repository_id: str
    repository_name: str
    repository_path: str
    repository_group: str
    repository_archived: str
    owner_team: str
    last_seen_at: NotRequired[str]


class BucketRowPayload(TypedDict, total=False):
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
    report_key: str
    product_title: str
    repository_archived: str
    last_seen_at: NotRequired[str]


class RepositoryRowPayload(TypedDict, total=False):
    repository: str
    namespaces: list[str]
    products: list[str]
    owner_team: str
    repository_id: str
    repository_name: str
    repository_path: str
    repository_group: str
    repository_archived: str


class FragmentRepositoryRowPayload(TypedDict, total=False):
    repository: str
    namespaces: list[str]
    product: str
    product_title: str
    owner_team: str
    repository_id: str
    repository_name: str
    repository_path: str
    repository_group: str
    repository_archived: str


def normalize_string_dict(row: SerializedRow) -> SerializedRow:
    return {str(key): normalize_row_value(key, value) for key, value in row.items()}


def normalize_row_value(key: Any, value: Any) -> Any:
    if key == "labels" and isinstance(value, dict):
        return {str(label_key): str(label_value or "") for label_key, label_value in value.items() if str(label_key)}
    return str(value or "")


def namespace_row_with_labels(row: NamespaceRowPayload, existing: NamespaceRowPayload | None) -> NamespaceRowPayload:
    if row.get("labels") or not existing or not existing.get("labels"):
        return row
    return {**row, "labels": existing["labels"]}


def bucket_key(row: SerializedRow) -> tuple[str, str, str, str, str]:
    return (
        row.get("namespace", "").lower(),
        row.get("repository", "").lower(),
        row.get("bucket", "").lower(),
        row.get("endpoint", "").lower(),
        row.get("source_var", "").lower(),
    )


def bucket_sort_key(row: SerializedRow) -> tuple[str, str, str, str]:
    return (
        row.get("bucket", ""),
        row.get("endpoint", ""),
        row.get("namespace", ""),
        row.get("repository", ""),
    )


def row_quality(row: SerializedRow) -> tuple[int, int]:
    valued_fields = sum(1 for key in ("repository", "owner_team", "product", "product_title", "stage") if row.get(key))
    return (valued_fields, len(row.get("repository", "")))


__all__ = [
    "BucketRowPayload",
    "FragmentRepositoryRowPayload",
    "NamespaceRowPayload",
    "RepositoryRowPayload",
    "SerializedRow",
    "bucket_key",
    "bucket_sort_key",
    "namespace_row_with_labels",
    "normalize_row_value",
    "normalize_string_dict",
    "row_quality",
]
