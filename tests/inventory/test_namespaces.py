from argparse import Namespace
from datetime import datetime, timezone

import pytest

from kmap.inventory.namespaces import (
    InventoryNamespaceContext,
    InventoryRow,
    collect_inventory_rows,
    config_files,
    inventory_row_for_namespace,
    inventory_row_from_context,
    inventory_rows_for_config,
    render_inventory,
    render_inventory_html,
)


def test_render_inventory_full_delegates_to_live_discovery(monkeypatch, tmp_path):
    calls = []

    def fake_discover_full_inventory(args, *, generated_at):
        calls.append((args, generated_at))
        return 7

    monkeypatch.setattr("kmap.inventory.full_discovery.discover_full_inventory", fake_discover_full_inventory)

    args = Namespace(
        config_dir=str(tmp_path / "config"),
        bucket_artifacts_dir=str(tmp_path / "artifacts" / "buckets"),
        output_dir=str(tmp_path / "Inventory"),
        full=True,
        cluster="cluster-a",
    )

    assert render_inventory(args) == 7

    assert calls
    assert calls[0][0] is args
    assert calls[0][1].tzinfo is not None
    assert not (tmp_path / "Inventory" / "namespaces.html").exists()
    assert not (tmp_path / "Inventory" / "buckets.html").exists()


def test_inventory_rows_for_config_use_effective_config_values():
    rows = inventory_rows_for_config(
        {
            "product": "demo",
            "title": "Demo",
            "env": "prod",
            "owner_team": "Platform Ops",
            "discovery": {"context": "prod-cluster"},
            "resources": {"repo": "https://git.example/product"},
            "namespaces": {
                "api-prod": {
                    "project": {"title": "API", "domain_team": "API Developers"},
                    "resources": {"repo": "https://git.example/api"},
                },
                "worker-prod": {
                    "discovery": {"context": "worker-cluster"},
                    "project": {"title": "Worker", "owner_team": "Worker Ops"},
                },
            },
        }
    )

    assert rows == [
        InventoryRow(
            cluster="prod-cluster",
            product="demo",
            namespace="api-prod",
            repository="https://git.example/api",
            owner_team="Platform Ops",
            product_title="Demo",
            stage="prod",
        ),
        InventoryRow(
            cluster="worker-cluster",
            product="demo",
            namespace="worker-prod",
            repository="https://git.example/product",
            owner_team="Worker Ops",
            product_title="Demo",
            stage="prod",
        ),
    ]


def test_inventory_rows_for_config_handles_list_namespaces_and_defaults():
    rows = inventory_rows_for_config(
        {
            "product": "demo",
            "owner_team": "Platform Ops",
            "resources": {"repo": "https://git.example/product"},
            "namespaces": ["api-dev", "", "worker-prod"],
        }
    )

    assert rows == [
        InventoryRow(
            cluster="default",
            product="demo",
            namespace="api-dev",
            repository="",
            owner_team="Platform Ops",
            stage="dev",
        ),
        InventoryRow(
            cluster="default",
            product="demo",
            namespace="worker-prod",
            repository="",
            owner_team="Platform Ops",
            stage="prod",
        ),
    ]


def test_inventory_row_from_context_preserves_row_rules():
    row = inventory_row_from_context(
        InventoryNamespaceContext(
            namespace="api-prod",
            namespace_entry={"discovery": {"context": "namespace-cluster"}},
            config={"env": "prod"},
            product_name="demo",
            product_context="product-cluster",
            product_owner="Platform Ops",
            product_title="Demo",
            namespace_projects={"api-prod": "api"},
            project_metadata={"api": {"owner_team": "API Ops", "resources": {"repo": "https://git.example/api"}}},
        )
    )

    assert row == InventoryRow(
        cluster="namespace-cluster",
        product="demo",
        namespace="api-prod",
        repository="https://git.example/api",
        owner_team="API Ops",
        product_title="Demo",
        stage="prod",
    )


def test_inventory_row_for_namespace_legacy_wrapper_still_works():
    row = inventory_row_for_namespace(
        "api-prod",
        {},
        config={"env": "prod"},
        product_name="demo",
        product_context="cluster-a",
        product_owner="Platform Ops",
        product_title="Demo",
        namespace_projects={"api-prod": ""},
        project_metadata={},
    )

    assert row == InventoryRow(
        cluster="cluster-a",
        product="demo",
        namespace="api-prod",
        repository="",
        owner_team="Platform Ops",
        product_title="Demo",
        stage="prod",
    )


def test_collect_inventory_rows_sorts_and_skips_example_configs(tmp_path):
    (tmp_path / "example.full.yaml").write_text("product: example\n", encoding="utf-8")
    (tmp_path / "demo.yaml").write_text(
        """
product: demo
title: Demo
env: prod
owner_team: Ops
discovery:
  context: z-cluster
namespaces:
  z-prod: {}
  a-prod:
    discovery:
      context: a-cluster
    resources:
      repo: https://git.example/a
""",
        encoding="utf-8",
    )

    assert [path.name for path in config_files(tmp_path)] == ["demo.yaml"]
    rows = collect_inventory_rows(tmp_path)

    assert [row.namespace for row in rows] == ["a-prod", "z-prod"]
    assert rows[0].cluster == "a-cluster"
    assert rows[0].product == "demo"
    assert rows[0].repository == "https://git.example/a"


def test_collect_inventory_rows_fails_for_missing_or_invalid_config_dir(tmp_path):
    with pytest.raises(SystemExit, match="config directory not found"):
        collect_inventory_rows(tmp_path / "missing")

    config_file = tmp_path / "config.yaml"
    config_file.write_text("product: demo\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="config path is not a directory"):
        collect_inventory_rows(config_file)

    bad_dir = tmp_path / "bad"
    bad_dir.mkdir()
    (bad_dir / "bad.yaml").write_text("product: demo\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="Invalid product config"):
        collect_inventory_rows(bad_dir)


def test_render_inventory_html_escapes_values_and_links_repositories():
    rendered = render_inventory_html(
        [
            InventoryRow(
                cluster="<prod>",
                product="demo<product>",
                product_title="Demo <Product>",
                namespace="api&prod",
                repository="https://git.example/api?x=1&y=2",
                owner_team="Ops <Team>",
            )
        ]
    )

    assert "&lt;prod&gt;" in rendered
    assert "demo&lt;product&gt;" in rendered
    assert "Demo &lt;Product&gt;" in rendered
    assert "api&amp;prod" in rendered
    assert "<code>&lt;prod&gt;</code>" in rendered
    assert '<a href="https://git.example/api?x=1&amp;y=2"' in rendered
    assert 'title="https://git.example/api?x=1&amp;y=2"' in rendered
    assert 'target="_blank" rel="noopener">api</a>' in rendered
    assert "Ops &lt;Team&gt;" in rendered
    assert "<th>Product</th><th>K8s cluster</th>" in rendered


def test_render_inventory_html_shows_namespace_labels_as_badges():
    rendered = render_inventory_html(
        [
            InventoryRow(
                cluster="prod",
                product="demo",
                namespace="api-prod",
                repository="",
                owner_team="Ops",
                labels={"app.kubernetes.io/name": "api", "empty": "", "<bad>": "x&y"},
            )
        ]
    )

    assert '<div class="namespace-labels">' in rendered
    assert '<span class="chip namespace-label">&lt;bad&gt;=x&amp;y</span>' in rendered
    assert '<span class="chip namespace-label">app.kubernetes.io/name=api</span>' in rendered
    assert '<span class="chip namespace-label">empty</span>' in rendered


def test_render_inventory_html_includes_summary_and_missing_markers():
    rendered = render_inventory_html(
        [
            InventoryRow(
                cluster="prod",
                product="demo",
                namespace="api",
                repository="",
                owner_team="",
            )
        ]
    )

    assert '<section class="stats" aria-label="Inventory summary">' in rendered
    assert '<nav><a href="namespaces.html">Namespaces</a><a href="buckets.html">Buckets</a></nav>' in rendered
    assert '<div class="stat"><strong>1</strong><span>Missing repositories</span></div>' in rendered
    assert '<div class="stat"><strong>1</strong><span>Missing owner teams</span></div>' in rendered
    assert '<input id="inventory-filter" type="search"' in rendered
    assert '<span class="missing">missing</span>' in rendered
    assert '<input id="inventory-filter-archived" type="checkbox"> Archived only</label>' in rendered


def test_render_inventory_html_marks_archived_repositories():
    rendered = render_inventory_html(
        [
            InventoryRow(
                cluster="prod",
                product="demo",
                namespace="api",
                repository="https://git.example/team/api",
                owner_team="Ops",
                repository_archived="true",
            )
        ]
    )

    assert '<tr data-repository-archived="true">' in rendered
    assert '<span class="chip archived" title="Repository is archived">archived</span>' in rendered
    assert "row.dataset.repositoryArchived === 'true'" in rendered


def test_render_inventory_html_highlights_reused_repositories():
    rendered = render_inventory_html(
        [
            InventoryRow(
                cluster="prod",
                product="demo",
                namespace="api",
                repository="https://git.example/shared",
                owner_team="Ops",
            ),
            InventoryRow(
                cluster="prod",
                product="demo",
                namespace="worker",
                repository="https://git.example/shared",
                owner_team="Ops",
            ),
            InventoryRow(
                cluster="prod",
                product="demo",
                namespace="single",
                repository="https://git.example/single",
                owner_team="Ops",
            ),
        ]
    )

    assert rendered.count('title="Repository is used by 2 namespaces">x2</span>') == 2
    assert 'title="Repository is used by 1 namespaces">x1</span>' not in rendered


def test_render_inventory_html_includes_generated_date_when_provided():
    rendered = render_inventory_html(
        [],
        generated_at=datetime(2026, 5, 18, 9, 30, 0, tzinfo=timezone.utc),
    )

    assert "<title>Product Namespaces</title>" in rendered
    assert "<h1>Product Namespaces</h1>" in rendered
    assert "Generated: 2026-05-18 09:30:00 UTC" in rendered


def test_render_inventory_html_accepts_custom_title_and_navigation():
    rendered = render_inventory_html(
        [],
        page_title="cluster-a Product Namespaces",
        nav_links=[("../../clusters.html", "Clusters"), ("namespaces.html", "Namespaces")],
    )

    assert "<title>cluster-a Product Namespaces</title>" in rendered
    assert "<h1>cluster-a Product Namespaces</h1>" in rendered
    assert '<nav><a href="../../clusters.html">Clusters</a><a href="namespaces.html">Namespaces</a></nav>' in rendered


def test_render_inventory_writes_output_file(tmp_path, capsys):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    output_dir = tmp_path / "Inventory"
    bucket_artifacts_dir = tmp_path / "artifacts" / "buckets"
    bucket_artifacts_dir.mkdir(parents=True)
    (config_dir / "demo.yaml").write_text(
        """
product: demo
title: Demo
env: prod
owner_team: Ops
namespaces:
  api-prod: {}
""",
        encoding="utf-8",
    )

    assert (
        render_inventory(
            Namespace(
                config_dir=str(config_dir),
                bucket_artifacts_dir=str(bucket_artifacts_dir),
                output_dir=str(output_dir),
            )
        )
        == 0
    )

    assert "api-prod" in (output_dir / "namespaces.html").read_text(encoding="utf-8")
    assert "<title>Storage Buckets</title>" in (output_dir / "buckets.html").read_text(encoding="utf-8")
    captured = capsys.readouterr()
    assert f"[kmap] wrote namespaces inventory: {output_dir / 'namespaces.html'}" in captured.err
    assert f"[kmap] wrote bucket inventory: {output_dir / 'buckets.html'}" in captured.err


def test_render_inventory_full_requires_cluster(tmp_path):
    with pytest.raises(SystemExit, match="--full requires --cluster"):
        render_inventory(
            Namespace(
                config_dir=str(tmp_path),
                bucket_artifacts_dir=str(tmp_path),
                output_dir=str(tmp_path / "Inventory"),
                full=True,
                cluster="",
            )
        )
