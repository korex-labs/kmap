from datetime import datetime, timezone

from kmap.inventory.buckets import BucketUsageRow
from kmap.inventory.cluster_state import (
    bucket_rows_by_namespace,
    merge_bucket_dicts,
    namespace_state_path,
    write_namespace_state_files,
)
from kmap.inventory.namespaces import InventoryRow


def test_write_namespace_state_files_writes_one_file_per_namespace_with_last_seen(tmp_path):
    written = write_namespace_state_files(
        output_dir=tmp_path / "Inventory",
        cluster="cluster-a",
        generated_at=datetime(2026, 5, 20, 9, 30, tzinfo=timezone.utc),
        namespace_rows=[
            InventoryRow(
                cluster="cluster-a",
                product="demo",
                namespace="api-prod",
                repository="https://git.example/api",
                owner_team="Ops",
                stage="prod",
            )
        ],
        bucket_rows=[
            BucketUsageRow(
                bucket="reports",
                endpoint="reports.s3.example.com",
                confidence="high",
                cluster="cluster-a",
                product="demo",
                namespace="api-prod",
                project="demo",
                workload="api",
                source="Env",
                source_var="S3_BUCKET",
                repository="https://git.example/api",
                owner_team="Ops",
            )
        ],
    )

    state_file = namespace_state_path(tmp_path / "Inventory", "cluster-a", "api-prod")
    payload = state_file.read_text(encoding="utf-8")
    assert written == [state_file]
    assert '"last_seen_at": "2026-05-20T09:30:00+00:00"' in payload
    assert '"namespace_name": "api-prod"' in payload
    assert '"repository": "https://git.example/api"' in payload
    assert '"bucket": "reports"' in payload


def test_write_namespace_state_files_preserves_better_existing_metadata(tmp_path):
    output_dir = tmp_path / "Inventory"
    state_file = namespace_state_path(output_dir, "cluster-a", "api-prod")
    state_file.parent.mkdir(parents=True)
    state_file.write_text(
        """
{
  "schema_version": 1,
  "cluster": "cluster-a",
  "namespace_name": "api-prod",
  "last_seen_at": "2026-05-19T09:30:00+00:00",
  "namespace": {
    "cluster": "cluster-a",
    "namespace": "api-prod",
    "stage": "prod",
    "product": "demo",
    "product_title": "Demo",
    "repository": "https://git.example/api",
    "owner_team": "Ops"
  },
  "buckets": []
}
""",
        encoding="utf-8",
    )

    write_namespace_state_files(
        output_dir=output_dir,
        cluster="cluster-a",
        generated_at=datetime(2026, 5, 20, 9, 30, tzinfo=timezone.utc),
        namespace_rows=[
            InventoryRow(
                cluster="cluster-a",
                product="",
                namespace="api-prod",
                repository="",
                owner_team="",
                stage="prod",
            )
        ],
        bucket_rows=[],
    )

    payload = state_file.read_text(encoding="utf-8")
    assert '"last_seen_at": "2026-05-20T09:30:00+00:00"' in payload
    assert '"repository": "https://git.example/api"' in payload
    assert '"owner_team": "Ops"' in payload


def test_write_namespace_state_files_tracks_bucket_last_seen_independently(tmp_path):
    output_dir = tmp_path / "Inventory"
    state_file = namespace_state_path(output_dir, "cluster-a", "api-prod")
    state_file.parent.mkdir(parents=True)
    state_file.write_text(
        """
{
  "schema_version": 1,
  "cluster": "cluster-a",
  "namespace_name": "api-prod",
  "last_seen_at": "2026-05-19T09:30:00+00:00",
  "namespace": {
    "cluster": "cluster-a",
    "namespace": "api-prod"
  },
  "buckets": [
    {
      "bucket": "old-reports",
      "endpoint": "",
      "confidence": "high",
      "cluster": "cluster-a",
      "namespace": "api-prod",
      "source_var": "OLD_BUCKET",
      "last_seen_at": "2026-05-19T09:30:00+00:00"
    }
  ]
}
""",
        encoding="utf-8",
    )

    write_namespace_state_files(
        output_dir=output_dir,
        cluster="cluster-a",
        generated_at=datetime(2026, 5, 20, 9, 30, tzinfo=timezone.utc),
        namespace_rows=[
            InventoryRow(
                cluster="cluster-a",
                product="demo",
                namespace="api-prod",
                repository="https://git.example/api",
                owner_team="Ops",
            )
        ],
        bucket_rows=[
            BucketUsageRow(
                bucket="new-reports",
                endpoint="",
                confidence="high",
                cluster="cluster-a",
                product="demo",
                namespace="api-prod",
                project="demo",
                workload="api",
                source="Env",
                source_var="NEW_BUCKET",
                repository="https://git.example/api",
                owner_team="Ops",
            )
        ],
    )

    payload = state_file.read_text(encoding="utf-8")
    assert '"bucket": "old-reports"' in payload
    assert '"last_seen_at": "2026-05-19T09:30:00+00:00"' in payload
    assert '"bucket": "new-reports"' in payload
    assert '"last_seen_at": "2026-05-20T09:30:00+00:00"' in payload


def test_bucket_rows_by_namespace_keeps_rows_in_input_order():
    first = BucketUsageRow(
        bucket="api-reports",
        endpoint="",
        confidence="high",
        cluster="cluster-a",
        product="demo",
        namespace="api-prod",
        project="demo",
        workload="api",
        source="Env",
        source_var="S3_BUCKET",
        repository="https://git.example/api",
        owner_team="Ops",
    )
    second = BucketUsageRow(
        bucket="worker-reports",
        endpoint="",
        confidence="high",
        cluster="cluster-a",
        product="demo",
        namespace="worker-prod",
        project="demo",
        workload="worker",
        source="Env",
        source_var="S3_BUCKET",
        repository="https://git.example/worker",
        owner_team="Ops",
    )
    third = BucketUsageRow(
        bucket="api-archive",
        endpoint="",
        confidence="medium",
        cluster="cluster-a",
        product="demo",
        namespace="api-prod",
        project="demo",
        workload="api",
        source="Env",
        source_var="ARCHIVE_BUCKET",
        repository="https://git.example/api",
        owner_team="Ops",
    )

    assert bucket_rows_by_namespace([first, second, third]) == {
        "api-prod": [first, third],
        "worker-prod": [second],
    }


def test_merge_bucket_dicts_dedupes_by_bucket_key_and_sorts_rows():
    rows = merge_bucket_dicts(
        [
            {
                "namespace": "api-prod",
                "repository": "https://git.example/api",
                "bucket": "z-reports",
                "endpoint": "",
                "source_var": "S3_BUCKET",
                "last_seen_at": "old",
            },
            {
                "namespace": "api-prod",
                "repository": "https://git.example/api",
                "bucket": "a-reports",
                "endpoint": "",
                "source_var": "S3_BUCKET",
                "last_seen_at": "new",
            },
            {
                "namespace": "api-prod",
                "repository": "https://git.example/api",
                "bucket": "z-reports",
                "endpoint": "",
                "source_var": "S3_BUCKET",
                "last_seen_at": "new",
            },
        ]
    )

    assert [row["bucket"] for row in rows] == ["a-reports", "z-reports"]
    assert rows[1]["last_seen_at"] == "new"
