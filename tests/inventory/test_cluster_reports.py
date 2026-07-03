from datetime import datetime, timezone

from kmap.inventory.cluster_inventory import load_cluster_inventory
from kmap.inventory.cluster_reports import (
    cluster_bucket_rows,
    cluster_namespace_rows,
    render_cluster_buckets_html,
    render_cluster_namespaces_html,
    render_cluster_reports,
    render_clusters_index_html,
    write_cluster_report_files,
)


def test_render_cluster_reports_writes_aggregate_json_and_html(tmp_path):
    cluster_dir = tmp_path / "Inventory" / "clusters" / "cluster-a"
    fragments_dir = cluster_dir / "fragments"
    fragments_dir.mkdir(parents=True)
    (fragments_dir / "team-a.json").write_text(
        """
{
  "schema_version": 1,
  "cluster": "cluster-a",
  "fragment_id": "team-a",
  "namespaces": [
    {"cluster": "cluster-a", "namespace": "api-prod", "stage": "prod", "labels": {"app": "api"}, "product": "demo", "product_title": "Demo Payments", "repository": "https://git.example/api", "owner_team": "Ops"}
  ],
  "repositories": [],
  "buckets": [
    {"bucket": "reports", "endpoint": "", "confidence": "high", "cluster": "cluster-a", "namespace": "api-prod", "repository": "https://git.example/api", "owner_team": "Ops", "product": "demo", "product_title": "Demo Payments", "source_var": "S3_BUCKET"}
  ]
}
""",
        encoding="utf-8",
    )

    written = render_cluster_reports(
        output_dir=tmp_path / "Inventory",
        generated_at=datetime(2026, 5, 19, 9, 30, tzinfo=timezone.utc),
    )

    assert [path.name for path in written] == ["inventory.json", "namespaces.html", "buckets.html", "clusters.html"]
    assert '"cluster": "cluster-a"' in (cluster_dir / "inventory.json").read_text(encoding="utf-8")
    assert "cluster-a Product Namespaces" in (cluster_dir / "namespaces.html").read_text(encoding="utf-8")
    assert "cluster-a Storage Buckets" in (cluster_dir / "buckets.html").read_text(encoding="utf-8")
    assert "Cluster Inventory" in (tmp_path / "Inventory" / "clusters.html").read_text(encoding="utf-8")
    assert not (cluster_dir / "repositories.html").exists()


def test_render_cluster_reports_can_filter_cluster(tmp_path):
    for cluster in ("cluster-a", "cluster-b"):
        fragments_dir = tmp_path / "Inventory" / "clusters" / cluster / "fragments"
        fragments_dir.mkdir(parents=True)
        (fragments_dir / "team.json").write_text(
            f'{{"schema_version": 1, "cluster": "{cluster}", "fragment_id": "team", "namespaces": [], "repositories": [], "buckets": []}}',
            encoding="utf-8",
        )

    written = render_cluster_reports(
        output_dir=tmp_path / "Inventory",
        generated_at=datetime(2026, 5, 19, 9, 30, tzinfo=timezone.utc),
        cluster="cluster-b",
    )

    assert all("cluster-b" in str(path) for path in written[:-1])
    assert written[-1] == tmp_path / "Inventory" / "clusters.html"
    assert not (tmp_path / "Inventory" / "clusters" / "cluster-a" / "inventory.json").exists()


def test_render_cluster_reports_removes_stale_repositories_page(tmp_path):
    cluster_dir = tmp_path / "Inventory" / "clusters" / "cluster-a"
    fragments_dir = cluster_dir / "fragments"
    fragments_dir.mkdir(parents=True)
    (cluster_dir / "repositories.html").write_text("stale", encoding="utf-8")
    (fragments_dir / "team.json").write_text(
        '{"schema_version": 1, "cluster": "cluster-a", "fragment_id": "team", "namespaces": [], "repositories": [], "buckets": []}',
        encoding="utf-8",
    )

    render_cluster_reports(
        output_dir=tmp_path / "Inventory",
        generated_at=datetime(2026, 5, 19, 9, 30, tzinfo=timezone.utc),
    )

    assert not (cluster_dir / "repositories.html").exists()


def test_write_cluster_report_files_returns_written_cluster_outputs(tmp_path):
    cluster_dir = tmp_path / "Inventory" / "clusters" / "cluster-a"
    fragments_dir = cluster_dir / "fragments"
    fragments_dir.mkdir(parents=True)
    (cluster_dir / "repositories.html").write_text("stale", encoding="utf-8")
    (fragments_dir / "team.json").write_text(
        """
{
  "schema_version": 1,
  "cluster": "cluster-a",
  "fragment_id": "team",
  "namespaces": [
    {"cluster": "cluster-a", "namespace": "api-prod", "product": "demo"}
  ],
  "repositories": [],
  "buckets": [
    {"bucket": "reports", "namespace": "api-prod", "source_var": "S3_BUCKET"}
  ]
}
""",
        encoding="utf-8",
    )

    written = write_cluster_report_files(
        cluster_dir,
        generated_at=datetime(2026, 5, 19, 9, 30, tzinfo=timezone.utc),
        tool_config={},
    )

    assert written == [cluster_dir / "inventory.json", cluster_dir / "namespaces.html", cluster_dir / "buckets.html"]
    assert '"fragment_id"' not in (cluster_dir / "inventory.json").read_text(encoding="utf-8")
    assert "cluster-a Product Namespaces" in (cluster_dir / "namespaces.html").read_text(encoding="utf-8")
    assert "cluster-a Storage Buckets" in (cluster_dir / "buckets.html").read_text(encoding="utf-8")
    assert not (cluster_dir / "repositories.html").exists()


def test_cluster_html_renderers_include_cluster_title_and_back_navigation(tmp_path):
    cluster_dir = tmp_path / "Inventory" / "clusters" / "cluster-a"
    fragments_dir = cluster_dir / "fragments"
    fragments_dir.mkdir(parents=True)
    (fragments_dir / "team.json").write_text(
        """
{
  "schema_version": 1,
  "cluster": "cluster-a",
  "fragment_id": "team",
  "generated_at": "2026-05-19T09:30:00+00:00",
  "namespaces": [
    {"cluster": "cluster-a", "namespace": "api-prod", "stage": "prod", "labels": {"app": "api"}, "product": "demo", "product_title": "Demo Payments", "repository": "https://git.example/api", "owner_team": "Ops"}
  ],
  "repositories": [],
  "buckets": []
}
""",
        encoding="utf-8",
    )
    inventory = load_cluster_inventory(cluster_dir)
    generated_at = datetime(2026, 5, 19, 9, 30, tzinfo=timezone.utc)

    namespaces_html = render_cluster_namespaces_html(inventory, generated_at)
    buckets_html = render_cluster_buckets_html(inventory, generated_at)

    assert "<title>cluster-a Product Namespaces</title>" in namespaces_html
    assert "<title>cluster-a Storage Buckets</title>" in buckets_html
    assert "<th>State</th>" in namespaces_html
    assert '<span class="state current"' in namespaces_html
    assert '<span class="chip namespace-label">app=api</span>' in namespaces_html
    expected_nav = (
        '<nav><a href="../../clusters.html">Clusters</a><a href="namespaces.html">Namespaces</a>'
        '<a href="buckets.html">Buckets</a></nav>'
    )
    assert expected_nav in namespaces_html
    assert expected_nav in buckets_html


def test_render_cluster_pages_mark_carried_state(tmp_path):
    cluster_dir = tmp_path / "Inventory" / "clusters" / "cluster-a"
    state_dir = cluster_dir / "state" / "namespaces"
    state_dir.mkdir(parents=True)
    (state_dir / "api-prod.json").write_text(
        """
{
  "schema_version": 1,
  "cluster": "cluster-a",
  "namespace_name": "api-prod",
  "last_seen_at": "2026-05-19T09:30:00+00:00",
  "namespace": {
    "cluster": "cluster-a",
    "namespace": "api-prod",
    "product": "demo",
    "repository": "https://git.example/api",
    "owner_team": "Ops"
  },
  "buckets": [
    {"bucket": "reports", "endpoint": "", "confidence": "high", "cluster": "cluster-a", "namespace": "api-prod", "repository": "https://git.example/api", "owner_team": "Ops", "product": "demo", "source_var": "S3_BUCKET", "last_seen_at": "2026-05-19T09:30:00+00:00"}
  ]
}
""",
        encoding="utf-8",
    )
    inventory = load_cluster_inventory(cluster_dir)
    generated_at = datetime(2026, 5, 20, 9, 30, tzinfo=timezone.utc)

    namespaces_html = render_cluster_namespaces_html(inventory, generated_at)
    buckets_html = render_cluster_buckets_html(inventory, generated_at)

    assert '<span class="state carried"' in namespaces_html
    assert '<span class="state carried"' in buckets_html
    assert 'title="Last seen: 2026-05-19T09:30:00+00:00"' in buckets_html


def test_render_clusters_index_html_links_cluster_reports(tmp_path):
    cluster_dir = tmp_path / "Inventory" / "clusters" / "cluster-a"
    state_dir = cluster_dir / "state" / "namespaces"
    state_dir.mkdir(parents=True)
    (state_dir / "api-prod.json").write_text(
        """
{
  "schema_version": 1,
  "cluster": "cluster-a",
  "namespace_name": "api-prod",
  "last_seen_at": "2026-05-20T09:30:00+00:00",
  "namespace": {
    "cluster": "cluster-a",
    "namespace": "api-prod",
    "stage": "prod",
    "product": "demo",
    "product_title": "Demo Payments",
    "repository": "https://git.example/api",
    "owner_team": "Ops"
  },
  "buckets": [
    {"bucket": "reports", "endpoint": "reports.s3.example.com", "confidence": "high", "cluster": "cluster-a", "namespace": "api-prod", "repository": "https://git.example/api", "owner_team": "Ops", "product": "demo", "product_title": "Demo Payments", "source_var": "S3_BUCKET"}
  ]
}
""",
        encoding="utf-8",
    )
    inventory = load_cluster_inventory(cluster_dir)

    rendered = render_clusters_index_html([inventory], datetime(2026, 5, 20, 9, 45, tzinfo=timezone.utc))

    assert "<title>Cluster Inventory</title>" in rendered
    assert "Generated: 2026-05-20 09:45:00 UTC" in rendered
    assert '<input id="cluster-filter" type="search"' in rendered
    assert '<a href="clusters/cluster-a/namespaces.html">Namespaces</a>' in rendered
    assert '<a href="clusters/cluster-a/buckets.html">Buckets</a>' in rendered
    assert "inventory.json" not in rendered
    assert "2026-05-20T09:30:00+00:00" in rendered


def test_cluster_row_adapters_fill_cluster_fallback_and_optional_fields(tmp_path):
    cluster_dir = tmp_path / "Inventory" / "clusters" / "cluster-a"
    fragments_dir = cluster_dir / "fragments"
    fragments_dir.mkdir(parents=True)
    (fragments_dir / "team.json").write_text(
        """
{
  "schema_version": 1,
  "cluster": "cluster-a",
  "fragment_id": "team",
  "namespaces": [
    {"namespace": "api-prod", "product": "demo", "repository": "https://git.example/api"}
  ],
  "repositories": [],
  "buckets": [
    {"bucket": "reports", "namespace": "api-prod", "source_var": "S3_BUCKET"}
  ]
}
""",
        encoding="utf-8",
    )
    inventory = load_cluster_inventory(cluster_dir)

    namespace_rows = cluster_namespace_rows(inventory)
    bucket_rows = cluster_bucket_rows(inventory)

    assert namespace_rows[0].cluster == "cluster-a"
    assert namespace_rows[0].owner_team == ""
    assert namespace_rows[0].repository == "https://git.example/api"
    assert bucket_rows[0].cluster == "cluster-a"
    assert bucket_rows[0].bucket == "reports"
    assert bucket_rows[0].source_var == "S3_BUCKET"
