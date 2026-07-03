"""Shared helpers for serialized inventory row payloads."""

from typing import Any, TypeAlias

SerializedRow: TypeAlias = dict[str, Any]
NamespaceRowPayload: TypeAlias = SerializedRow
BucketRowPayload: TypeAlias = dict[str, str]
RepositoryRowPayload: TypeAlias = SerializedRow


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


def row_quality(row: SerializedRow) -> tuple[int, int]:
    valued_fields = sum(1 for key in ("repository", "owner_team", "product", "product_title", "stage") if row.get(key))
    return (valued_fields, len(row.get("repository", "")))


__all__ = [
    "BucketRowPayload",
    "NamespaceRowPayload",
    "RepositoryRowPayload",
    "SerializedRow",
    "namespace_row_with_labels",
    "normalize_row_value",
    "normalize_string_dict",
    "row_quality",
]
