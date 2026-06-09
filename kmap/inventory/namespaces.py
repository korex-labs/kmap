"""Render a product responsibility inventory from kmap configs."""

from datetime import datetime
from pathlib import Path
from typing import Any

from ..io import ensure_dir, write_text_atomic
from ..logging import eprint
from ..paths import SCHEMAS_ROOT
from .namespace_html import (
    render_inventory_html,
    render_product_cell,
    render_repository,
    render_state_cell,
    repository_archived,
)
from .namespace_rows import (
    InventoryNamespaceContext,
    InventoryRow,
    collect_inventory_rows,
    config_files,
    discovery_context,
    infer_stage_from_namespace,
    inventory_row_for_namespace,
    inventory_row_from_context,
    inventory_rows_for_config,
    load_valid_inventory_config,
    namespace_cluster,
    namespace_entries,
    namespace_stage,
    project_repository,
)

DEFAULT_CONFIG_DIR = SCHEMAS_ROOT / "tools" / "kmap" / "config"
DEFAULT_INVENTORY_DIR = SCHEMAS_ROOT / "Inventory"
DEFAULT_NAMESPACES_INVENTORY_FILE = DEFAULT_INVENTORY_DIR / "namespaces.html"


def render_inventory(args) -> int:
    from .full_discovery import discover_full_inventory

    config_dir = Path(args.config_dir)
    output_dir = Path(args.output_dir)
    bucket_artifacts_dir = Path(args.bucket_artifacts_dir)
    generated_at = datetime.now().astimezone()

    if getattr(args, "full", False):
        if not getattr(args, "cluster", ""):
            raise SystemExit("--full requires --cluster so kmap knows which cluster to discover")
        return discover_full_inventory(args, generated_at=generated_at)

    render_static_inventory(
        config_dir=config_dir,
        bucket_artifacts_dir=bucket_artifacts_dir,
        output_dir=output_dir,
        generated_at=generated_at,
        tool_config=getattr(args, "kmap_tool_config", {}),
    )
    return 0


def render_static_inventory(
    *,
    config_dir: Path,
    bucket_artifacts_dir: Path,
    output_dir: Path,
    generated_at: datetime,
    tool_config: dict[str, Any],
) -> tuple[Path, Path]:
    from .buckets import collect_bucket_usage_rows, render_buckets_html, storage_type_rules_from_config

    ensure_dir(output_dir)
    rows = enrich_inventory_rows(collect_inventory_rows(config_dir), tool_config)
    namespaces_file = output_dir / "namespaces.html"
    write_text_atomic(namespaces_file, render_inventory_html(rows, generated_at=generated_at))

    bucket_rows = collect_bucket_usage_rows(bucket_artifacts_dir, config_dir, inventory_rows=rows)
    buckets_file = output_dir / "buckets.html"
    write_text_atomic(
        buckets_file,
        render_buckets_html(
            bucket_rows,
            generated_at=generated_at,
            storage_type_rules=storage_type_rules_from_config(tool_config),
        ),
    )

    eprint(f"[kmap] wrote namespaces inventory: {namespaces_file}")
    eprint(f"[kmap] wrote bucket inventory: {buckets_file}")
    return namespaces_file, buckets_file


def enrich_inventory_rows(rows: list[InventoryRow], tool_config: dict[str, Any]) -> list[InventoryRow]:
    from .repositories import enrich_inventory_rows_from_repositories

    return enrich_inventory_rows_from_repositories(rows, tool_config)


__all__ = [
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_INVENTORY_DIR",
    "DEFAULT_NAMESPACES_INVENTORY_FILE",
    "InventoryNamespaceContext",
    "InventoryRow",
    "collect_inventory_rows",
    "config_files",
    "discovery_context",
    "enrich_inventory_rows",
    "infer_stage_from_namespace",
    "inventory_row_for_namespace",
    "inventory_row_from_context",
    "inventory_rows_for_config",
    "load_valid_inventory_config",
    "namespace_cluster",
    "namespace_entries",
    "namespace_stage",
    "project_repository",
    "render_inventory",
    "render_inventory_html",
    "render_product_cell",
    "render_repository",
    "render_state_cell",
    "render_static_inventory",
    "repository_archived",
]
