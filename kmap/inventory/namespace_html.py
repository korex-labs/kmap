"""Namespace inventory HTML rendering."""

from collections import Counter
from datetime import datetime
from html import escape

from .html import render_cell, render_code_cell, render_inventory_page
from .namespace_repository import render_repository, repository_archived, repository_label
from .namespace_rows import InventoryRow
from .namespace_state import render_state_cell


def render_inventory_html(
    rows: list[InventoryRow],
    generated_at: datetime | None = None,
    *,
    page_title: str = "Product Namespaces",
    nav_links: list[tuple[str, str]] | None = None,
    show_state: bool = False,
) -> str:
    summary = inventory_summary(rows)
    repository_counts = inventory_repository_counts(rows)
    nav_links = nav_links or [("namespaces.html", "Namespaces"), ("buckets.html", "Buckets")]
    table_rows = inventory_table_rows(
        rows,
        repository_counts=repository_counts,
        generated_at=generated_at,
        show_state=show_state,
    )
    return render_inventory_page(
        page_title=page_title,
        summary=f"{len(rows)} namespaces from kmap product configs.",
        generated_at=generated_at,
        nav_links=nav_links,
        extra_styles=inventory_page_styles(),
        stats=inventory_page_stats(summary),
        stats_label="Inventory summary",
        filter_id="inventory-filter",
        filter_placeholder="Filter inventory",
        table_id="inventory-table",
        empty_id="inventory-empty",
        empty_text="No matching inventory rows.",
        table_header=inventory_table_header(show_state=show_state),
        table_rows=table_rows,
        repository_archive_filter=True,
    )


def inventory_page_styles() -> list[str]:
    return [
        "    main { width: min(1500px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0; }",
        "    .stats { display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 12px; margin-bottom: 16px; }",
        "    table { min-width: 980px; }",
        "    th, td { padding: 0.72rem 0.85rem; }",
        "    th { font-size: 0.78rem; }",
        "    td code { font-size: 0.88rem; }",
        "    @media (max-width: 900px) { main { width: min(100% - 20px, 1500px); padding: 20px 0; } header { display: block; } .generated { text-align: left; margin-top: 8px; white-space: normal; } .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); } }",
    ]


def inventory_page_stats(summary: dict[str, int]) -> list[tuple[int, str]]:
    return [
        (summary["namespaces"], "Namespaces"),
        (summary["products"], "Products"),
        (summary["clusters"], "K8s clusters"),
        (summary["missing_repositories"], "Missing repositories"),
        (summary["missing_owner_teams"], "Missing owner teams"),
    ]


def inventory_table_header(*, show_state: bool = False) -> str:
    state = "<th>State</th>" if show_state else ""
    return (
        f"<tr><th>Product</th><th>K8s cluster</th><th>Namespace</th>{state}<th>Repository</th><th>Owner team</th></tr>"
    )


def inventory_table_rows(
    rows: list[InventoryRow],
    repository_counts: dict[str, int],
    *,
    generated_at: datetime | None = None,
    show_state: bool = False,
) -> list[str]:
    return [
        render_inventory_row(
            row,
            repository_counts=repository_counts,
            generated_at=generated_at,
            show_state=show_state,
        )
        for row in rows
    ]


def render_inventory_row(
    row: InventoryRow,
    repository_counts: dict[str, int] | None = None,
    *,
    generated_at: datetime | None = None,
    show_state: bool = False,
) -> str:
    repository_counts = repository_counts or {}
    archived = repository_archived(row.repository_archived)
    repository = render_repository(
        row.repository,
        usage_count=repository_counts.get(row.repository, 0),
        archived=archived,
    )
    state = render_state_cell(row.last_seen_at, generated_at) if show_state else ""
    return (
        f'          <tr data-repository-archived="{str(archived).lower()}">'
        f"<td>{render_product_cell(row.product, row.product_title)}</td>"
        f"<td>{render_code_cell(row.cluster)}</td>"
        f"<td>{render_code_cell(row.namespace)}</td>"
        f"{state}"
        f"<td>{repository}</td>"
        f"<td>{render_cell(row.owner_team)}</td>"
        "</tr>"
    )


def inventory_summary(rows: list[InventoryRow]) -> dict[str, int]:
    return {
        "namespaces": len(rows),
        "products": len({row.product for row in rows if row.product}),
        "clusters": len({row.cluster for row in rows if row.cluster}),
        "missing_repositories": sum(1 for row in rows if not row.repository),
        "missing_owner_teams": sum(1 for row in rows if not row.owner_team),
    }


def inventory_repository_counts(rows: list[InventoryRow]) -> dict[str, int]:
    return dict(Counter(row.repository for row in rows if row.repository))


def render_product_cell(product: str, product_title: str = "") -> str:
    if not product and not product_title:
        return '<span class="missing">missing</span>'
    if product_title and product_title != product:
        return f'<span class="primary">{escape(product_title)}</span><code class="secondary">{escape(product)}</code>'
    return render_cell(product_title or product)


__all__ = [
    "inventory_page_stats",
    "inventory_page_styles",
    "inventory_repository_counts",
    "inventory_summary",
    "inventory_table_header",
    "inventory_table_rows",
    "render_inventory_html",
    "render_inventory_row",
    "render_product_cell",
    "render_repository",
    "render_state_cell",
    "repository_archived",
    "repository_label",
]
