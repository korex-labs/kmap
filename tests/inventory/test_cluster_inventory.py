import pytest

from kmap.inventory.cluster_inventory import (
    load_cluster_fragment,
    load_cluster_inventory,
    merge_bucket_rows,
    merge_namespace_rows,
    repositories_for_cluster_namespaces,
    rows_with_last_seen,
)


def test_load_cluster_inventory_merges_fragments_and_dedupes_rows(tmp_path):
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
    {"cluster": "cluster-a", "namespace": "shared-prod", "stage": "prod", "product": "demo", "product_title": "Demo Payments", "repository": "", "owner_team": "Ops"},
    {"cluster": "cluster-a", "namespace": "api-prod", "stage": "prod", "product": "demo", "product_title": "Demo Payments", "repository": "https://git.example/api", "owner_team": "Ops"}
  ],
  "repositories": [],
  "buckets": [
    {"bucket": "reports", "endpoint": "reports.s3.example.com", "confidence": "high", "cluster": "cluster-a", "namespace": "api-prod", "repository": "https://git.example/api", "owner_team": "Ops", "product": "demo", "product_title": "Demo Payments", "source_var": "S3_BUCKET"}
  ]
}
""",
        encoding="utf-8",
    )
    (fragments_dir / "team-b.json").write_text(
        """
{
  "schema_version": 1,
  "cluster": "cluster-a",
  "fragment_id": "team-b",
  "namespaces": [
    {"cluster": "cluster-a", "namespace": "shared-prod", "stage": "prod", "product": "demo", "product_title": "Demo Payments", "repository": "https://git.example/shared", "owner_team": "Ops"}
  ],
  "repositories": [],
  "buckets": [
    {"bucket": "reports", "endpoint": "reports.s3.example.com", "confidence": "high", "cluster": "cluster-a", "namespace": "api-prod", "repository": "https://git.example/api", "owner_team": "Ops", "product": "demo", "product_title": "Demo Payments", "source_var": "S3_BUCKET"}
  ]
}
""",
        encoding="utf-8",
    )

    inventory = load_cluster_inventory(cluster_dir)

    assert inventory.cluster == "cluster-a"
    assert inventory.fragments == ["team-a", "team-b"]
    assert [row["namespace"] for row in inventory.namespaces] == ["api-prod", "shared-prod"]
    assert next(row for row in inventory.namespaces if row["namespace"] == "shared-prod")["repository"] == (
        "https://git.example/shared"
    )
    assert [row["repository"] for row in inventory.repositories] == [
        "https://git.example/api",
        "https://git.example/shared",
    ]
    assert len(inventory.buckets) == 1


def test_load_cluster_inventory_reads_namespace_state_files(tmp_path):
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

    assert inventory.fragments == []
    assert inventory.states == ["api-prod"]
    assert [row["namespace"] for row in inventory.namespaces] == ["api-prod"]
    assert inventory.namespaces[0]["last_seen_at"] == "2026-05-20T09:30:00+00:00"
    assert inventory.buckets[0]["bucket"] == "reports"
    assert inventory.buckets[0]["last_seen_at"] == "2026-05-20T09:30:00+00:00"


def test_load_cluster_inventory_merges_namespace_labels_from_state_and_fragments(tmp_path):
    cluster_dir = tmp_path / "Inventory" / "clusters" / "cluster-a"
    fragments_dir = cluster_dir / "fragments"
    state_dir = cluster_dir / "state" / "namespaces"
    fragments_dir.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    (fragments_dir / "team-a.json").write_text(
        """
{
  "schema_version": 1,
  "cluster": "cluster-a",
  "fragment_id": "team-a",
  "namespaces": [
    {"cluster": "cluster-a", "namespace": "api-prod", "product": "demo", "repository": "https://git.example/api", "owner_team": "Ops"}
  ],
  "repositories": [],
  "buckets": []
}
""",
        encoding="utf-8",
    )
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
    "labels": {"app": "api"}
  },
  "buckets": []
}
""",
        encoding="utf-8",
    )

    inventory = load_cluster_inventory(cluster_dir)

    assert inventory.namespaces == [
        {
            "cluster": "cluster-a",
            "namespace": "api-prod",
            "product": "demo",
            "repository": "https://git.example/api",
            "owner_team": "Ops",
            "labels": {"app": "api"},
        }
    ]


def test_load_cluster_inventory_rejects_unknown_fragment_schema(tmp_path):
    fragments_dir = tmp_path / "Inventory" / "clusters" / "cluster-a" / "fragments"
    fragments_dir.mkdir(parents=True)
    (fragments_dir / "bad.json").write_text('{"schema_version": 999}', encoding="utf-8")

    with pytest.raises(SystemExit, match="Unsupported cluster inventory schema version"):
        load_cluster_inventory(tmp_path / "Inventory" / "clusters" / "cluster-a")


def test_load_cluster_fragment_rejects_malformed_schema_version(tmp_path):
    fragment_file = tmp_path / "bad.json"
    fragment_file.write_text('{"schema_version": "bad"}', encoding="utf-8")

    with pytest.raises(SystemExit, match="Unsupported cluster inventory schema version"):
        load_cluster_fragment(fragment_file)


def test_rows_with_last_seen_fills_missing_values_without_overwriting():
    rows = rows_with_last_seen(
        [{"namespace": "api-prod", "last_seen_at": "custom"}, {"namespace": "worker-prod"}],
        "2026-05-20T09:30:00+00:00",
    )

    assert rows == [
        {"namespace": "api-prod", "last_seen_at": "custom"},
        {"namespace": "worker-prod", "last_seen_at": "2026-05-20T09:30:00+00:00"},
    ]


def test_merge_namespace_rows_ignores_missing_namespace_and_prefers_higher_quality():
    target = {}

    merge_namespace_rows(target, [{"product": "demo"}, {"namespace": "api-prod", "repository": ""}])
    merge_namespace_rows(
        target,
        [{"namespace": "api-prod", "repository": "https://git.example/api", "owner_team": "Ops"}],
    )

    assert target == {
        "api-prod": {
            "namespace": "api-prod",
            "repository": "https://git.example/api",
            "owner_team": "Ops",
        }
    }


def test_merge_namespace_rows_adds_labels_to_existing_row_without_replacing_metadata():
    target = {"api-prod": {"namespace": "api-prod", "repository": "https://git.example/api"}}

    merge_namespace_rows(target, [{"namespace": "api-prod", "labels": {"app": "api"}}])

    assert target == {
        "api-prod": {
            "namespace": "api-prod",
            "repository": "https://git.example/api",
            "labels": {"app": "api"},
        }
    }


def test_merge_bucket_rows_keeps_first_duplicate_bucket_payload():
    target = {}
    merge_bucket_rows(
        target,
        [
            {"namespace": "api-prod", "bucket": "reports", "source_var": "S3_BUCKET", "last_seen_at": "first"},
            {"namespace": "api-prod", "bucket": "reports", "source_var": "S3_BUCKET", "last_seen_at": "second"},
        ],
    )

    assert list(target.values()) == [
        {"namespace": "api-prod", "bucket": "reports", "source_var": "S3_BUCKET", "last_seen_at": "first"}
    ]


def test_repositories_for_cluster_namespaces_rolls_up_namespaces_and_best_metadata():
    repositories = repositories_for_cluster_namespaces(
        [
            {
                "namespace": "api-prod",
                "repository": "https://git.example/api",
                "product": "demo",
                "owner_team": "",
            },
            {
                "namespace": "api-review",
                "repository": "https://git.example/api",
                "product": "demo-review",
                "owner_team": "Ops",
                "repository_id": "42",
                "repository_name": "api",
            },
        ]
    )

    assert repositories == [
        {
            "repository": "https://git.example/api",
            "namespaces": ["api-prod", "api-review"],
            "products": ["demo", "demo-review"],
            "owner_team": "Ops",
            "repository_id": "42",
            "repository_name": "api",
            "repository_path": "",
            "repository_group": "",
            "repository_archived": "",
        }
    ]
