"""Namespace-scoped cluster inventory state."""

from datetime import datetime
from pathlib import Path

from ..config import slug_name
from ..io import dump_json, ensure_dir, load_required_json_file
from .buckets import BucketUsageRow, bucket_row_dict
from .cluster_fragments import CLUSTER_INVENTORY_SCHEMA_VERSION, namespace_row_dict
from .namespaces import InventoryRow
from .row_payloads import (
    BucketRowPayload,
    SerializedRow,
    bucket_key,
    bucket_sort_key,
    normalize_string_dict,
    row_quality,
)
from .schema import require_schema_version


def write_namespace_state_files(
    *,
    output_dir: Path,
    cluster: str,
    generated_at: datetime,
    namespace_rows: list[InventoryRow],
    bucket_rows: list[BucketUsageRow],
) -> list[Path]:
    state_dir = cluster_namespace_state_dir(output_dir, cluster)
    ensure_dir(state_dir)
    buckets_by_namespace = bucket_rows_by_namespace(bucket_rows)

    return [
        write_namespace_state_file(
            output_dir=output_dir,
            cluster=cluster,
            generated_at=generated_at,
            namespace_row=row,
            bucket_rows=buckets_by_namespace.get(row.namespace, []),
        )
        for row in namespace_rows
    ]


def write_namespace_state_file(
    *,
    output_dir: Path,
    cluster: str,
    generated_at: datetime,
    namespace_row: InventoryRow,
    bucket_rows: list[BucketUsageRow],
) -> Path:
    output_file = namespace_state_path(output_dir, cluster, namespace_row.namespace)
    payload = namespace_state_payload(
        cluster=cluster,
        generated_at=generated_at,
        namespace_row=namespace_row,
        bucket_rows=bucket_rows,
        existing=load_namespace_state(output_file) if output_file.exists() else {},
    )
    dump_json(output_file, payload)
    return output_file


def bucket_rows_by_namespace(bucket_rows: list[BucketUsageRow]) -> dict[str, list[BucketUsageRow]]:
    grouped: dict[str, list[BucketUsageRow]] = {}
    for row in bucket_rows:
        grouped.setdefault(row.namespace, []).append(row)
    return grouped


def namespace_state_payload(
    *,
    cluster: str,
    generated_at: datetime,
    namespace_row: InventoryRow,
    bucket_rows: list[BucketUsageRow],
    existing: SerializedRow | None = None,
) -> SerializedRow:
    existing = existing or {}
    generated = generated_at.isoformat(timespec="seconds")
    current_namespace = namespace_row_dict(namespace_row)
    existing_namespace = normalize_string_dict(existing.get("namespace") or {})
    best_namespace = (
        current_namespace_with_existing_labels(current_namespace, existing_namespace)
        if row_quality(current_namespace) >= row_quality(existing_namespace)
        else {
            **existing_namespace,
            "cluster": cluster,
            "namespace": namespace_row.namespace,
            "labels": current_namespace.get("labels") or existing_namespace.get("labels", {}),
        }
    )
    return {
        "schema_version": CLUSTER_INVENTORY_SCHEMA_VERSION,
        "cluster": cluster,
        "namespace_name": namespace_row.namespace,
        "last_seen_at": generated,
        "namespace": best_namespace,
        "buckets": merge_bucket_dicts(
            existing_bucket_dicts(existing) + [bucket_dict_with_last_seen(row, generated) for row in bucket_rows]
        ),
    }


def current_namespace_with_existing_labels(current: SerializedRow, existing: SerializedRow) -> SerializedRow:
    if current.get("labels") or not existing.get("labels"):
        return current
    return {**current, "labels": existing["labels"]}


def load_namespace_state(path: Path) -> SerializedRow:
    payload = load_required_json_file(path)
    require_schema_version(
        payload,
        expected=CLUSTER_INVENTORY_SCHEMA_VERSION,
        source=path,
        kind="cluster namespace state",
    )
    return payload


def bucket_dict_with_last_seen(row: BucketUsageRow, last_seen_at: str) -> BucketRowPayload:
    payload = bucket_row_dict(row)
    payload["last_seen_at"] = last_seen_at
    return payload


def existing_bucket_dicts(existing: SerializedRow) -> list[SerializedRow]:
    last_seen_at = str(existing.get("last_seen_at") or "")
    return [
        {**normalize_string_dict(row), "last_seen_at": str(row.get("last_seen_at") or last_seen_at)}
        for row in existing.get("buckets") or []
    ]


def cluster_namespace_state_dir(output_dir: Path, cluster: str) -> Path:
    return output_dir / "clusters" / slug_name(cluster or "default").lower() / "state" / "namespaces"


def namespace_state_path(output_dir: Path, cluster: str, namespace: str) -> Path:
    return cluster_namespace_state_dir(output_dir, cluster) / f"{slug_name(namespace)}.json"


def merge_bucket_dicts(rows: list[SerializedRow]) -> list[SerializedRow]:
    merged: dict[tuple[str, str, str, str, str], SerializedRow] = {}
    for row in rows:
        merged[bucket_key(row)] = row
    return sorted(
        merged.values(),
        key=bucket_sort_key,
    )


__all__ = [
    "cluster_namespace_state_dir",
    "load_namespace_state",
    "namespace_state_path",
    "write_namespace_state_files",
]
