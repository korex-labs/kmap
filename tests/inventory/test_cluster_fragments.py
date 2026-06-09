from datetime import datetime, timezone

import pytest

from kmap.inventory.cluster_fragments import (
    bucket_rows_for_config_fragment,
    cluster_fragment_path,
    render_cluster_fragments,
)


def test_render_cluster_fragments_writes_per_cluster_product_fragments(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    bucket_artifacts_dir = tmp_path / "artifacts" / "buckets"
    bucket_artifacts_dir.mkdir(parents=True)
    output_dir = tmp_path / "Inventory"
    (config_dir / "demo.yaml").write_text(
        """
product: demo
title: Demo Product
env: prod
owner_team: Ops
discovery:
  context: cluster-a
namespaces:
  api-prod:
    project:
      title: API
    resources:
      repo: https://git.example/api
  worker-dev:
    env: dev
    discovery:
      context: cluster-b
    resources:
      repo: https://git.example/worker
""",
        encoding="utf-8",
    )
    (bucket_artifacts_dir / "demo.json").write_text(
        """
{
  "schema_version": 1,
  "report_key": "demo",
  "product": "demo",
  "rows": [
    {"bucket": "reports", "endpoint": "reports.s3.example.com", "confidence": "high", "cluster": "cluster-a", "namespace": "api-prod", "source": "Env", "source_var": "S3_BUCKET_NAME"}
  ]
}
""",
        encoding="utf-8",
    )

    written = render_cluster_fragments(
        config_dir=config_dir,
        bucket_artifacts_dir=bucket_artifacts_dir,
        output_dir=output_dir,
        generated_at=datetime(2026, 5, 19, 9, 30, tzinfo=timezone.utc),
    )

    assert sorted(path.name for path in written) == ["demo.json", "demo.json"]
    cluster_a = output_dir / "clusters" / "cluster-a" / "fragments" / "demo.json"
    cluster_b = output_dir / "clusters" / "cluster-b" / "fragments" / "demo.json"
    assert cluster_a.exists()
    assert cluster_b.exists()

    payload = cluster_a.read_text(encoding="utf-8")
    assert '"schema_version": 1' in payload
    assert '"cluster": "cluster-a"' in payload
    assert '"namespace": "api-prod"' in payload
    assert '"stage": "prod"' in payload
    assert '"repository": "https://git.example/api"' in payload
    assert '"bucket": "reports"' in payload
    assert '"repositories": [' in payload


def test_render_cluster_fragments_can_filter_cluster(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    output_dir = tmp_path / "Inventory"
    (config_dir / "demo.yaml").write_text(
        """
product: demo
title: Demo
env: prod
owner_team: Ops
namespaces:
  api-prod:
    discovery:
      context: cluster-a
  worker-prod:
    discovery:
      context: cluster-b
""",
        encoding="utf-8",
    )

    written = render_cluster_fragments(
        config_dir=config_dir,
        bucket_artifacts_dir=tmp_path / "missing-buckets",
        output_dir=output_dir,
        generated_at=datetime(2026, 5, 19, 9, 30, tzinfo=timezone.utc),
        cluster="cluster-b",
    )

    assert written == [output_dir / "clusters" / "cluster-b" / "fragments" / "demo.json"]
    assert not (output_dir / "clusters" / "cluster-a").exists()
    assert '"namespace": "worker-prod"' in written[0].read_text(encoding="utf-8")


def test_cluster_fragment_path_slugs_cluster_and_fragment_id(tmp_path):
    assert cluster_fragment_path(tmp_path, "Prod Cluster", "demo.product") == (
        tmp_path / "clusters" / "prod-cluster" / "fragments" / "demo-product.json"
    )


def test_bucket_rows_for_config_fragment_rejects_unknown_schema(tmp_path):
    bucket_artifacts_dir = tmp_path / "artifacts" / "buckets"
    bucket_artifacts_dir.mkdir(parents=True)
    config_file = tmp_path / "demo.yaml"
    config_file.write_text("product: demo\n", encoding="utf-8")
    (bucket_artifacts_dir / "demo.json").write_text('{"schema_version": 999, "rows": []}', encoding="utf-8")

    with pytest.raises(SystemExit, match=r"Unsupported bucket report schema version in demo[.]json"):
        bucket_rows_for_config_fragment(
            bucket_artifacts_dir=bucket_artifacts_dir,
            config_file=config_file,
            namespace_rows=[],
        )
