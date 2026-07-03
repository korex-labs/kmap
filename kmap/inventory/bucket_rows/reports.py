"""Bucket usage rows extracted from namespace reports."""

from typing import Any

from ...inspection import bucket_candidate_from_pair
from ..namespaces import InventoryRow, collect_inventory_rows
from .model import BucketUsageRow
from .signals import is_bucket_usage_signal, key_for_bucket_candidate


def bucket_inventory_index(config_dir) -> dict[tuple[str, str], InventoryRow]:
    if not config_dir.exists():
        return {}
    return bucket_inventory_index_from_rows(collect_inventory_rows(config_dir))


def bucket_inventory_index_from_rows(rows: list[InventoryRow]) -> dict[tuple[str, str], InventoryRow]:
    index: dict[tuple[str, str], InventoryRow] = {}
    for row in rows:
        index[row.cluster, row.namespace] = row
        index.setdefault(("", row.namespace), row)
    return index


def bucket_rows_for_report(
    report: dict[str, Any],
    inventory: dict[tuple[str, str], InventoryRow],
    *,
    report_key: str = "",
) -> list[BucketUsageRow]:
    rows = []
    report_cluster = str(report.get("cluster") or "")
    report_namespace = str(report.get("namespace") or "")
    for workload in report.get("workloads") or []:
        cluster = str(workload.get("cluster") or report_cluster)
        namespace = str(workload.get("namespace") or report_namespace)
        inventory_row = bucket_inventory_row(inventory, cluster, namespace)
        rows.extend(
            bucket_usage_row_from_report_candidate(
                candidate,
                workload=workload,
                cluster=cluster,
                namespace=namespace,
                inventory_row=inventory_row,
                report_key=report_key,
            )
            for candidate in workload_bucket_rows(workload)
            if is_bucket_usage_signal(candidate)
        )
    return rows


def bucket_inventory_row(
    inventory: dict[tuple[str, str], InventoryRow],
    cluster: str,
    namespace: str,
) -> InventoryRow | None:
    return inventory.get((cluster, namespace)) or inventory.get(("", namespace))


def bucket_usage_row_from_report_candidate(
    candidate: dict[str, Any],
    *,
    workload: dict[str, Any],
    cluster: str,
    namespace: str,
    inventory_row: InventoryRow | None,
    report_key: str = "",
) -> BucketUsageRow:
    return BucketUsageRow(
        bucket=str(candidate.get("bucket") or ""),
        endpoint=str(candidate.get("endpoint") or ""),
        confidence=str(candidate.get("confidence") or ""),
        cluster=cluster,
        product=inventory_row.product if inventory_row else "",
        namespace=namespace,
        project=str(workload.get("project") or ""),
        workload=str(workload.get("service_name") or ""),
        source=str(candidate.get("source") or ""),
        source_var=str(candidate.get("var") or ""),
        repository=inventory_row.repository if inventory_row else "",
        owner_team=inventory_row.owner_team if inventory_row else "",
        report_key=report_key,
        product_title=inventory_row.product_title if inventory_row else "",
        repository_archived=inventory_row.repository_archived if inventory_row else "",
    )


def workload_bucket_rows(workload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = list(workload.get("bucket_candidates") or [])
    if candidates:
        return dedupe_bucket_rows(candidates)
    return dedupe_bucket_rows(bucket_rows_from_dependency_candidates(workload))


def bucket_rows_from_dependency_candidates(workload: dict[str, Any]) -> list[dict[str, Any]]:
    fallback = []
    for dep in workload.get("dependency_candidates") or []:
        candidate = bucket_candidate_from_pair(
            str(dep.get("var") or ""),
            str(dep.get("key") or ""),
            str(dep.get("source") or dep.get("source_origin") or ""),
            str(dep.get("source_name") or ""),
        )
        if candidate:
            fallback.append(candidate)
    return fallback


def dedupe_bucket_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for candidate in candidates:
        key = (
            str(candidate.get("bucket") or ""),
            str(candidate.get("endpoint") or ""),
            str(candidate.get("source") or ""),
            str(candidate.get("var") or ""),
        )
        deduped.setdefault(key, candidate)
    return sorted(deduped.values(), key=key_for_bucket_candidate)


__all__ = [
    "bucket_inventory_index",
    "bucket_inventory_index_from_rows",
    "bucket_inventory_row",
    "bucket_rows_for_report",
    "bucket_rows_from_dependency_candidates",
    "bucket_usage_row_from_report_candidate",
    "dedupe_bucket_rows",
    "workload_bucket_rows",
]
