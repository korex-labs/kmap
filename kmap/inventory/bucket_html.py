"""Bucket inventory HTML rendering."""

from collections import Counter
from datetime import datetime
from html import escape

from .bucket_rows import BucketUsageRow
from .html import render_cell, render_code_cell, render_inventory_page
from .namespaces import render_product_cell, render_repository, render_state_cell, repository_archived
from .storage_types import storage_type_label


def render_buckets_html(
    rows: list[BucketUsageRow],
    generated_at: datetime | None = None,
    *,
    page_title: str = "Storage Buckets",
    nav_links: list[tuple[str, str]] | None = None,
    storage_type_rules: list[dict[str, str]] | None = None,
    show_state: bool = False,
) -> str:
    bucket_counts = Counter(row.bucket for row in rows if row.bucket)
    nav_links = nav_links or [("namespaces.html", "Namespaces"), ("buckets.html", "Buckets")]
    storage_type_rules = storage_type_rules or []
    table_rows = bucket_table_rows(
        rows,
        bucket_counts,
        generated_at=generated_at,
        storage_type_rules=storage_type_rules,
        show_state=show_state,
    )
    return render_inventory_page(
        page_title=page_title,
        summary=f"{len(rows)} storage bucket signals from kmap reports.",
        generated_at=generated_at,
        nav_links=nav_links,
        extra_styles=[
            "    main { width: min(1600px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0; }",
            "    .stats { display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 12px; margin-bottom: 16px; }",
            "    table { min-width: 1320px; }",
            "    th, td { padding: 0.68rem 0.75rem; }",
            "    th { font-size: 0.76rem; }",
            "    td code { font-size: 0.86rem; }",
            "    .confidence { display: inline-block; border-radius: 999px; padding: 2px 8px; font-size: 0.76rem; font-weight: 800; text-transform: uppercase; }",
            "    .confidence.high { color: #0b6b3a; background: #dff6e8; border: 1px solid #9bd8b3; }",
            "    .confidence.medium { color: #075985; background: #e0f2fe; border: 1px solid #7dd3fc; }",
            "    .confidence.low { color: #52525b; background: #f4f4f5; border: 1px solid #d4d4d8; }",
            "    @media (max-width: 900px) { main { width: min(100% - 20px, 1600px); padding: 20px 0; } header { display: block; } .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); } }",
        ],
        stats=bucket_summary_stats(rows, bucket_counts),
        stats_label="Bucket usage summary",
        filter_id="bucket-filter",
        filter_placeholder="Filter storage buckets",
        table_id="bucket-table",
        empty_id="bucket-empty",
        empty_text="No matching storage bucket rows.",
        table_header=bucket_table_header(show_state=show_state),
        table_rows=table_rows,
        generated_class="summary",
        repository_archive_filter=True,
    )


def bucket_summary_stats(rows: list[BucketUsageRow], bucket_counts: Counter) -> list[tuple[int, str]]:
    return [
        (len(bucket_counts), "Named buckets"),
        (len(rows), "Storage signals"),
        (sum(1 for row in rows if row.confidence == "high"), "High confidence"),
        (sum(1 for row in rows if not row.bucket), "Location only"),
    ]


def bucket_table_header(*, show_state: bool = False) -> str:
    state = "<th>State</th>" if show_state else ""
    return (
        "<tr><th>Product</th><th>K8s cluster</th><th>Bucket</th><th>Storage location</th><th>Type</th>"
        f"<th>Match</th><th>Namespace</th>{state}<th>Detected from</th><th>Repository</th><th>Owner team</th></tr>"
    )


def bucket_table_rows(
    rows: list[BucketUsageRow],
    bucket_counts: Counter,
    *,
    generated_at: datetime | None = None,
    storage_type_rules: list[dict[str, str]] | None = None,
    show_state: bool = False,
) -> list[str]:
    return [
        render_bucket_row(
            row,
            bucket_counts,
            generated_at=generated_at,
            storage_type_rules=storage_type_rules,
            show_state=show_state,
        )
        for row in rows
    ]


def render_bucket_row(
    row: BucketUsageRow,
    bucket_counts: Counter,
    *,
    generated_at: datetime | None = None,
    storage_type_rules: list[dict[str, str]] | None = None,
    show_state: bool = False,
) -> str:
    bucket = render_code_cell(row.bucket)
    if row.bucket and bucket_counts[row.bucket] > 1:
        bucket += f' <span class="chip" title="Bucket appears in {bucket_counts[row.bucket]} usage signals">x{bucket_counts[row.bucket]}</span>'
    state = render_state_cell(row.last_seen_at, generated_at) if show_state else ""
    return (
        f'          <tr data-repository-archived="{str(repository_archived(row.repository_archived)).lower()}">'
        f"<td>{render_product_cell(row.product, row.product_title)}</td>"
        f"<td>{render_code_cell(row.cluster)}</td>"
        f"<td>{bucket}</td>"
        f"<td>{render_storage_location(row.endpoint)}</td>"
        f"<td>{render_storage_backend(row, storage_type_rules or [])}</td>"
        f"<td>{render_confidence(row.confidence)}</td>"
        f"<td>{render_code_cell(row.namespace)}</td>"
        f"{state}"
        f"<td>{render_source(row.source, row.source_var)}</td>"
        f"<td>{render_repository(row.repository, archived=repository_archived(row.repository_archived))}</td>"
        f"<td>{render_cell(row.owner_team)}</td>"
        "</tr>"
    )


def render_storage_location(endpoint: str) -> str:
    return render_code_cell(endpoint) if endpoint else '<span class="missing">not detected</span>'


def render_storage_backend(row: BucketUsageRow, storage_type_rules: list[dict[str, str]] | None = None) -> str:
    label = storage_type_label(
        endpoint=row.endpoint,
        bucket=row.bucket,
        source_var=row.source_var,
        storage_type_rules=storage_type_rules or [],
    )
    return escape(label) if label else '<span class="missing">unknown</span>'


def render_confidence(confidence: str) -> str:
    if not confidence:
        return '<span class="missing">missing</span>'
    safe = escape(confidence.lower())
    return f'<span class="confidence {safe}">{escape(confidence)}</span>'


def render_source(source: str, source_var: str) -> str:
    if not source and not source_var:
        return '<span class="missing">missing</span>'
    if source and source_var:
        return f'<span class="primary">{escape(source)}</span><code class="secondary">{escape(source_var)}</code>'
    return render_cell(source or source_var)
