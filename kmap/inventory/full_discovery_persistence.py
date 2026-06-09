"""Persistence helpers for full inventory discovery."""

from datetime import datetime
from pathlib import Path

from ..config import slug_name
from .buckets import bucket_rows_for_report
from .cluster_state import write_namespace_state_files
from .namespaces import InventoryRow


def write_namespace_report_state(
    *,
    output_dir: Path,
    cluster: str,
    generated_at: datetime,
    namespace_row: InventoryRow,
    report: dict[str, object],
) -> list[Path]:
    bucket_rows = bucket_rows_for_report(
        report,
        {(namespace_row.cluster, namespace_row.namespace): namespace_row, ("", namespace_row.namespace): namespace_row},
        report_key=slug_name(cluster),
    )
    return write_namespace_state_files(
        output_dir=output_dir,
        cluster=cluster,
        generated_at=generated_at,
        namespace_rows=[namespace_row],
        bucket_rows=bucket_rows,
    )


def remove_stale_full_discovery_reports(reports_dir: Path) -> None:
    for report_file in reports_dir.glob("*.report.json"):
        report_file.unlink()


def remove_legacy_live_discovery_fragment(output_dir: Path, cluster: str) -> None:
    legacy_file = (
        output_dir
        / "clusters"
        / slug_name(cluster or "default").lower()
        / "fragments"
        / f"{slug_name('live-discovery')}.json"
    )
    if legacy_file.exists():
        legacy_file.unlink()


__all__ = [
    "remove_legacy_live_discovery_fragment",
    "remove_stale_full_discovery_reports",
    "write_namespace_report_state",
]
