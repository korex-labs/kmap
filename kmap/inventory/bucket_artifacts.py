"""Bucket inventory artifact loading and writing."""

from datetime import datetime
from pathlib import Path

from ..config import slug_name
from ..io import dump_json, ensure_dir, load_required_json_file
from ..paths import SCHEMAS_ROOT
from .bucket_rows import (
    BUCKET_REPORT_SCHEMA_VERSION,
    BucketUsageRow,
    bucket_inventory_index,
    bucket_inventory_index_from_rows,
    bucket_row_dict,
    bucket_rows_for_report,
    bucket_rows_from_artifact,
    merge_bucket_usage_rows,
    sort_bucket_usage_rows,
    suppress_redundant_location_only_rows,
)
from .namespaces import InventoryRow

DEFAULT_BUCKET_REPORTS_DIR = SCHEMAS_ROOT / "artifacts" / "buckets"


def write_bucket_report(
    *,
    reports_dir: Path,
    config_dir: Path,
    config_path: str,
    product: str,
    output_dir: Path = DEFAULT_BUCKET_REPORTS_DIR,
) -> Path:
    report_key = bucket_report_key(config_path, product)
    rows = collect_bucket_usage_rows_from_reports(reports_dir, config_dir, report_key=report_key)
    payload = {
        "schema_version": BUCKET_REPORT_SCHEMA_VERSION,
        "report_key": report_key,
        "product": product,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "rows": [bucket_row_dict(row) for row in rows],
    }
    ensure_dir(output_dir)
    output_file = output_dir / f"{report_key}.json"
    dump_json(output_file, payload)
    return output_file


def bucket_report_key(config_path: str, product: str) -> str:
    if config_path:
        return Path(config_path).stem
    return slug_name(product or "product")


def collect_bucket_usage_rows(
    bucket_reports_dir: Path,
    config_dir: Path,
    *,
    inventory_rows: list[InventoryRow] | None = None,
) -> list[BucketUsageRow]:
    if not bucket_reports_dir.exists():
        return []
    if not bucket_reports_dir.is_dir():
        raise SystemExit(f"bucket artifacts path is not a directory: {bucket_reports_dir}")
    bucket_report_files = sorted(bucket_reports_dir.glob("*.json"))
    validate_bucket_report_freshness(bucket_report_files, config_dir)

    inventory = (
        bucket_inventory_index_from_rows(inventory_rows)
        if inventory_rows is not None
        else bucket_inventory_index(config_dir)
    )
    rows: list[BucketUsageRow] = []
    for report_file in bucket_report_files:
        payload = load_required_json_file(report_file)
        rows.extend(bucket_rows_from_artifact(payload, inventory, fallback_report_key=report_file.stem))
    return finalize_bucket_usage_rows(rows)


def collect_bucket_usage_rows_from_reports(
    reports_dir: Path,
    config_dir: Path,
    *,
    report_key: str = "",
    inventory_rows: list[InventoryRow] | None = None,
) -> list[BucketUsageRow]:
    if not reports_dir.exists():
        raise SystemExit(f"reports directory not found: {reports_dir}")
    report_files = sorted(reports_dir.glob("*.report.json"))
    if not report_files:
        raise SystemExit(f"No *.report.json found in {reports_dir}")

    inventory = (
        bucket_inventory_index_from_rows(inventory_rows)
        if inventory_rows is not None
        else bucket_inventory_index(config_dir)
    )
    rows: list[BucketUsageRow] = []
    for report_file in report_files:
        report = load_required_json_file(report_file)
        rows.extend(bucket_rows_for_report(report, inventory, report_key=report_key))
    return finalize_bucket_usage_rows(rows)


def finalize_bucket_usage_rows(rows: list[BucketUsageRow]) -> list[BucketUsageRow]:
    return sort_bucket_usage_rows(suppress_redundant_location_only_rows(merge_bucket_usage_rows(rows)))


def validate_bucket_report_freshness(bucket_report_files: list[Path], config_dir: Path) -> None:
    if not config_dir.exists():
        return
    config_keys = {path.stem for path in config_dir.glob("*.yaml") if not path.name.startswith("example.")}
    config_keys.discard("kmap")
    stale = sorted(path.name for path in bucket_report_files if path.stem not in config_keys)
    if stale:
        joined = "\n".join(f"- {name}" for name in stale)
        raise SystemExit(f"Stale bucket artifacts found; remove, rename, or regenerate them:\n{joined}")
