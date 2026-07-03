from datetime import UTC, datetime

from kmap.inventory.bucket_html import render_buckets_html
from kmap.inventory.bucket_rows import BucketUsageRow


def test_render_buckets_html_contains_summary_filter_and_reuse_chip():
    rendered = render_buckets_html(
        [
            BucketUsageRow(
                "reports", "", "high", "ctx", "demo", "payments", "pay", "api", "Env", "S3_BUCKET", "", "Ops"
            ),
            BucketUsageRow(
                "reports",
                "reports.ceph.example.com",
                "medium",
                "ctx",
                "demo",
                "workers",
                "pay",
                "worker",
                "Env",
                "S3_ENDPOINT",
                "https://git.example/pay",
                "Ops",
            ),
            BucketUsageRow(
                "payment-files",
                "auth.servers.com",
                "high",
                "ctx",
                "demo",
                "payments",
                "pay",
                "api",
                "Env",
                "FILES_OS_AUTH_URL, FILES_OS_BUCKET_NAME",
                "https://git.example/pay",
                "Ops",
            ),
            BucketUsageRow(
                "reports-eu",
                "s3.eu-central-1.amazonaws.com",
                "low",
                "ctx",
                "demo",
                "reports",
                "pay",
                "api",
                "Env",
                "S3_ENDPOINT_URL",
                "https://git.example/pay",
                "Ops",
                repository_archived="true",
            ),
        ],
        generated_at=datetime(2026, 5, 18, 9, 30, 0, tzinfo=UTC),
    )

    assert "<title>Storage Buckets</title>" in rendered
    assert "Generated: 2026-05-18 09:30:00 UTC" in rendered
    assert '<input id="bucket-filter" type="search"' in rendered
    assert 'title="Bucket appears in 2 usage signals">x2</span>' in rendered
    assert (
        "<th>Product</th><th>K8s cluster</th><th>Bucket</th><th>Storage location</th><th>Type</th><th>Match</th>"
        in rendered
    )
    assert "<th>Workload</th>" not in rendered
    assert '<span class="confidence high">high</span>' in rendered
    assert "<td>Ceph</td>" in rendered
    assert "<td>Servers.com</td>" in rendered
    assert '<input id="bucket-filter-archived" type="checkbox"> Archived only</label>' in rendered
    assert '<tr data-repository-archived="true">' in rendered
    assert '<span class="chip archived" title="Repository is archived">archived</span>' in rendered
    assert "<td>S3 (eu-central-1)</td>" in rendered
    assert ".confidence.medium { color: #075985;" in rendered
    assert ".confidence.low { color: #52525b;" in rendered
    assert "Detected from" in rendered
    assert 'title="https://git.example/pay"' in rendered
    assert ">pay</a>" in rendered
    assert ">https://git.example/pay</a>" not in rendered
    assert '<span class="missing">missing</span>' in rendered


def test_render_buckets_html_accepts_custom_title_navigation_and_storage_type_rules():
    rendered = render_buckets_html(
        [
            BucketUsageRow(
                "reports",
                "reports.ceph-primary.example.com",
                "high",
                "ctx",
                "demo",
                "payments",
                "pay",
                "api",
                "Env",
                "S3_BUCKET",
                "",
                "Ops",
            )
        ],
        page_title="cluster-a Storage Buckets",
        nav_links=[("../../clusters.html", "Clusters"), ("buckets.html", "Buckets")],
        storage_type_rules=[{"match": "ceph-primary", "label": "Ceph New"}],
    )

    assert "<title>cluster-a Storage Buckets</title>" in rendered
    assert "<h1>cluster-a Storage Buckets</h1>" in rendered
    assert '<nav><a href="../../clusters.html">Clusters</a><a href="buckets.html">Buckets</a></nav>' in rendered
    assert "<td>Ceph New</td>" in rendered


def test_render_buckets_html_marks_missing_storage_type_location_and_source():
    rendered = render_buckets_html(
        [
            BucketUsageRow(
                "",
                "",
                "",
                "ctx",
                "",
                "payments",
                "",
                "",
                "",
                "",
                "",
                "",
            )
        ]
    )

    assert '<span class="missing">not detected</span>' in rendered
    assert '<span class="missing">unknown</span>' in rendered
    assert '<span class="missing">missing</span>' in rendered
