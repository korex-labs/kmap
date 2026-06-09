"""Bucket usage rows extracted from persisted bucket artifacts."""

from typing import Any

from ...inspection import bucket_candidate_from_pair
from ..namespaces import InventoryRow
from .model import BucketUsageRow
from .reports import bucket_inventory_row
from .signals import is_bucket_usage_signal

BUCKET_REPORT_SCHEMA_VERSION = 1


def bucket_rows_from_artifact(
    payload: dict[str, Any],
    inventory: dict[tuple[str, str], InventoryRow],
    *,
    fallback_report_key: str,
) -> list[BucketUsageRow]:
    if int(payload.get("schema_version") or 0) != BUCKET_REPORT_SCHEMA_VERSION:
        raise SystemExit(f"Unsupported bucket report schema version in {fallback_report_key}")
    report_key = str(payload.get("report_key") or fallback_report_key)
    rows = []
    for item in payload.get("rows") or []:
        enriched_item = enrich_bucket_artifact_item(item)
        cluster = str(item.get("cluster") or "")
        namespace = str(item.get("namespace") or "")
        inventory_row = bucket_inventory_row(inventory, cluster, namespace)
        if not is_bucket_usage_signal(enriched_item):
            continue
        rows.append(bucket_usage_row_from_artifact_item(enriched_item, payload, inventory_row, report_key))
    return rows


def bucket_usage_row_from_artifact_item(
    item: dict[str, Any],
    payload: dict[str, Any],
    inventory_row: InventoryRow | None,
    report_key: str,
) -> BucketUsageRow:
    return BucketUsageRow(
        bucket=str(item.get("bucket") or ""),
        endpoint=str(item.get("endpoint") or ""),
        confidence=str(item.get("confidence") or ""),
        cluster=str(item.get("cluster") or ""),
        product=artifact_product(item, payload, inventory_row),
        namespace=str(item.get("namespace") or ""),
        project=str(item.get("project") or ""),
        workload=str(item.get("workload") or ""),
        source=str(item.get("source") or ""),
        source_var=str(item.get("source_var") or ""),
        repository=artifact_repository(item, inventory_row),
        owner_team=artifact_owner_team(item, inventory_row),
        report_key=report_key,
        product_title=artifact_product_title(item, inventory_row),
        repository_archived=artifact_repository_archived(item, inventory_row),
    )


def artifact_product(
    item: dict[str, Any],
    payload: dict[str, Any],
    inventory_row: InventoryRow | None,
) -> str:
    if inventory_row:
        return inventory_row.product
    return str(item.get("product") or payload.get("product") or "")


def artifact_repository(item: dict[str, Any], inventory_row: InventoryRow | None) -> str:
    return inventory_row.repository if inventory_row else str(item.get("repository") or "")


def artifact_owner_team(item: dict[str, Any], inventory_row: InventoryRow | None) -> str:
    return inventory_row.owner_team if inventory_row else str(item.get("owner_team") or "")


def artifact_product_title(item: dict[str, Any], inventory_row: InventoryRow | None) -> str:
    return inventory_row.product_title if inventory_row else str(item.get("product_title") or "")


def artifact_repository_archived(item: dict[str, Any], inventory_row: InventoryRow | None) -> str:
    return inventory_row.repository_archived if inventory_row else str(item.get("repository_archived") or "")


def enrich_bucket_artifact_item(item: dict[str, Any]) -> dict[str, Any]:
    if item.get("bucket") or not item.get("endpoint"):
        return item
    candidate = bucket_candidate_from_pair(
        str(item.get("source_var") or ""),
        str(item.get("endpoint") or ""),
        str(item.get("source") or ""),
        "",
    )
    if not candidate.get("bucket"):
        return item
    enriched = dict(item)
    enriched["bucket"] = candidate["bucket"]
    enriched["confidence"] = candidate.get("confidence") or item.get("confidence") or ""
    return enriched


__all__ = [
    "BUCKET_REPORT_SCHEMA_VERSION",
    "artifact_owner_team",
    "artifact_product",
    "artifact_product_title",
    "artifact_repository",
    "artifact_repository_archived",
    "bucket_rows_from_artifact",
    "bucket_usage_row_from_artifact_item",
    "enrich_bucket_artifact_item",
]
