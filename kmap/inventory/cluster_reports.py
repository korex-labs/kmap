"""Aggregate and render cluster-scoped inventory fragments."""

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from ..config import slug_name
from ..io import dump_json, write_text_atomic
from .buckets import BucketUsageRow, render_buckets_html, storage_type_rules_from_config
from .cluster_inventory import (
    ClusterInventory,
    cluster_dirs,
    cluster_inventory_payload,
    load_cluster_inventories,
    load_cluster_inventory,
)
from .html import render_code_cell, render_inventory_page
from .namespaces import InventoryRow, render_inventory_html


def render_cluster_reports(
    *,
    output_dir: Path,
    generated_at: datetime,
    cluster: str = "",
    tool_config: dict[str, Any] | None = None,
) -> list[Path]:
    written: list[Path] = []
    for cluster_dir in cluster_dirs(output_dir, cluster=cluster):
        written.extend(
            write_cluster_report_files(cluster_dir, generated_at=generated_at, tool_config=tool_config or {})
        )
    clusters_file = write_clusters_index_file(output_dir, generated_at=generated_at)
    written.append(clusters_file)
    return written


def write_cluster_report_files(
    cluster_dir: Path,
    *,
    generated_at: datetime,
    tool_config: dict[str, Any],
) -> list[Path]:
    inventory = load_cluster_inventory(cluster_dir)
    inventory_file = cluster_dir / "inventory.json"
    namespaces_file = cluster_dir / "namespaces.html"
    buckets_file = cluster_dir / "buckets.html"
    dump_json(inventory_file, cluster_inventory_payload(inventory, generated_at=generated_at))
    write_text_atomic(namespaces_file, render_cluster_namespaces_html(inventory, generated_at))
    write_text_atomic(buckets_file, render_cluster_buckets_html(inventory, generated_at, tool_config=tool_config))
    remove_stale_repositories_page(cluster_dir)
    return [inventory_file, namespaces_file, buckets_file]


def write_clusters_index_file(output_dir: Path, *, generated_at: datetime) -> Path:
    clusters_file = output_dir / "clusters.html"
    write_text_atomic(clusters_file, render_clusters_index_html(load_cluster_inventories(output_dir), generated_at))
    return clusters_file


def remove_stale_repositories_page(cluster_dir: Path) -> None:
    stale_file = cluster_dir / "repositories.html"
    if stale_file.exists():
        stale_file.unlink()


def render_cluster_namespaces_html(inventory: ClusterInventory, generated_at: datetime) -> str:
    return render_inventory_html(
        cluster_namespace_rows(inventory),
        generated_at=generated_at,
        page_title=f"{inventory.cluster} Product Namespaces",
        nav_links=cluster_report_nav_links(),
        show_state=True,
    )


def render_cluster_buckets_html(
    inventory: ClusterInventory,
    generated_at: datetime,
    *,
    tool_config: dict[str, Any] | None = None,
) -> str:
    return render_buckets_html(
        cluster_bucket_rows(inventory),
        generated_at=generated_at,
        page_title=f"{inventory.cluster} Storage Buckets",
        nav_links=cluster_report_nav_links(),
        storage_type_rules=storage_type_rules_from_config(tool_config or {}),
        show_state=True,
    )


def cluster_namespace_rows(inventory: ClusterInventory) -> list[InventoryRow]:
    return [
        InventoryRow(
            cluster=row.get("cluster", "") or inventory.cluster,
            product=row.get("product", ""),
            namespace=row.get("namespace", ""),
            repository=row.get("repository", ""),
            owner_team=row.get("owner_team", ""),
            product_title=row.get("product_title", ""),
            stage=row.get("stage", ""),
            last_seen_at=row.get("last_seen_at", ""),
            repository_id=row.get("repository_id", ""),
            repository_name=row.get("repository_name", ""),
            repository_path=row.get("repository_path", ""),
            repository_group=row.get("repository_group", ""),
            repository_archived=row.get("repository_archived", ""),
            labels=row.get("labels", {}) if isinstance(row.get("labels"), dict) else {},
        )
        for row in inventory.namespaces
    ]


def cluster_bucket_rows(inventory: ClusterInventory) -> list[BucketUsageRow]:
    return [
        BucketUsageRow(
            bucket=row.get("bucket", ""),
            endpoint=row.get("endpoint", ""),
            confidence=row.get("confidence", ""),
            cluster=row.get("cluster", "") or inventory.cluster,
            product=row.get("product", ""),
            namespace=row.get("namespace", ""),
            project=row.get("project", ""),
            workload=row.get("workload", ""),
            source=row.get("source", ""),
            source_var=row.get("source_var", ""),
            repository=row.get("repository", ""),
            owner_team=row.get("owner_team", ""),
            report_key=row.get("report_key", ""),
            product_title=row.get("product_title", ""),
            last_seen_at=row.get("last_seen_at", ""),
            repository_archived=row.get("repository_archived", ""),
        )
        for row in inventory.buckets
    ]


def cluster_report_nav_links() -> list[tuple[str, str]]:
    return [
        ("../../clusters.html", "Clusters"),
        ("namespaces.html", "Namespaces"),
        ("buckets.html", "Buckets"),
    ]


def render_clusters_index_html(inventories: list[ClusterInventory], generated_at: datetime | None = None) -> str:
    rows = sorted(inventories, key=lambda inventory: inventory.cluster.lower())
    return render_inventory_page(
        page_title="Cluster Inventory",
        summary=f"{len(rows)} clusters with generated inventory pages.",
        generated_at=generated_at,
        nav_links=[("namespaces.html", "Namespaces"), ("buckets.html", "Buckets"), ("clusters.html", "Clusters")],
        extra_styles=[
            "    main { width: min(1500px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0; }",
            "    .stats { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 12px; margin-bottom: 16px; }",
            "    table { min-width: 980px; }",
            "    th, td { padding: 0.72rem 0.85rem; }",
            "    th { font-size: 0.78rem; }",
            "    td code { font-size: 0.88rem; }",
            "    .actions { display: flex; gap: 10px; flex-wrap: wrap; }",
            "    @media (max-width: 900px) { main { width: min(100% - 20px, 1500px); padding: 20px 0; } header { display: block; } .generated { text-align: left; margin-top: 8px; white-space: normal; } .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); } }",
        ],
        stats=[
            (len(rows), "Clusters"),
            (sum(len(item.namespaces) for item in rows), "Namespaces"),
            (sum(len(item.repositories) for item in rows), "Repositories"),
            (sum(len(item.buckets) for item in rows), "Bucket signals"),
        ],
        stats_label="Cluster inventory summary",
        filter_id="cluster-filter",
        filter_placeholder="Filter clusters",
        table_id="cluster-table",
        empty_id="cluster-empty",
        empty_text="No matching clusters.",
        table_header="<tr><th>K8s cluster</th><th>Namespaces</th><th>Repositories</th><th>Bucket signals</th><th>Last seen</th><th>Reports</th></tr>",
        table_rows=[render_cluster_index_row(item) for item in rows],
    )


def render_cluster_index_row(inventory: ClusterInventory) -> str:
    cluster_slug = slug_name(inventory.cluster or "default").lower()
    return (
        "          <tr>"
        f"<td>{render_code_cell(inventory.cluster)}</td>"
        f"<td>{len(inventory.namespaces)}</td>"
        f"<td>{len(inventory.repositories)}</td>"
        f"<td>{len(inventory.buckets)}</td>"
        f"<td>{render_optional_text(inventory.last_seen_at)}</td>"
        f'<td><div class="actions"><a href="clusters/{cluster_slug}/namespaces.html">Namespaces</a>'
        f'<a href="clusters/{cluster_slug}/buckets.html">Buckets</a></div></td>'
        "</tr>"
    )


def render_optional_text(value: str) -> str:
    return escape(value) if value else '<span class="missing">missing</span>'


__all__ = [
    "ClusterInventory",
    "cluster_inventory_payload",
    "load_cluster_inventory",
    "render_cluster_buckets_html",
    "render_cluster_namespaces_html",
    "render_cluster_reports",
    "render_clusters_index_html",
]
