import pytest

from kmap.inventory.bucket_artifacts import (
    collect_bucket_usage_rows,
    collect_bucket_usage_rows_from_reports,
    write_bucket_report,
)


def test_collect_bucket_usage_rows_and_writes_artifact(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "demo.yaml").write_text(
        """
product: demo
title: Demo
env: prod
owner_team: Ops
namespaces:
  payments:
    resources:
      repo: https://git.example/pay
""",
        encoding="utf-8",
    )
    (reports_dir / "payments.report.json").write_text(
        """
{
  "cluster": "default",
  "namespace": "payments",
  "workloads": [
    {
      "namespace": "payments",
      "project": "pay",
      "service_name": "api",
      "bucket_candidates": [
        {"source": "Env", "var": "S3_BUCKET", "bucket": "reports", "endpoint": "", "confidence": "high"}
      ]
    }
  ]
}
""",
        encoding="utf-8",
    )

    rows = collect_bucket_usage_rows_from_reports(reports_dir, config_dir)
    assert rows[0].repository == "https://git.example/pay"
    written_report = write_bucket_report(
        reports_dir=reports_dir,
        config_dir=config_dir,
        config_path=str(config_dir / "demo.yaml"),
        product="demo",
        output_dir=tmp_path / "artifacts" / "buckets",
    )
    assert written_report.name == "demo.json"
    assert collect_bucket_usage_rows(tmp_path / "artifacts" / "buckets", config_dir)[0].bucket == "reports"


def test_collect_bucket_usage_rows_filters_false_positives_and_enriches_endpoint_prefix(tmp_path):
    bucket_reports_dir = tmp_path / "artifacts" / "buckets"
    bucket_reports_dir.mkdir(parents=True)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "demo.yaml").write_text(
        """
product: demo
title: Demo
env: prod
owner_team: Ops
namespaces:
  payments: {}
""",
        encoding="utf-8",
    )
    (bucket_reports_dir / "demo.json").write_text(
        """
{
  "schema_version": 1,
  "report_key": "demo",
  "product": "demo",
  "rows": [
    {"bucket": "tcp", "endpoint": "", "confidence": "high", "cluster": "default", "namespace": "payments", "source_var": "MAIN_BUCKET_PORT_9000_TCP_PROTO"},
    {"bucket": "prod", "endpoint": "", "confidence": "high", "cluster": "default", "namespace": "payments", "source_var": "PPROF_DUMPER_S3_BUCKET_NAME"},
    {"bucket": "reports", "endpoint": "", "confidence": "high", "cluster": "default", "namespace": "payments", "source_var": "S3_BUCKET_NAME", "repository": "https://git.example/pay"},
    {"bucket": "reports", "endpoint": "reports.s3.example.com", "confidence": "high", "cluster": "default", "namespace": "payments", "source_var": "S3_HOST_BUCKET", "repository": "https://git.example/pay"},
    {"bucket": "", "endpoint": "s3.eu-central-1.amazonaws.com", "confidence": "low", "cluster": "default", "namespace": "payments", "source_var": "S3_ENDPOINT_URL", "repository": "https://git.example/pay"},
    {"bucket": "", "endpoint": "s3.eu-central-1.amazonaws.com", "confidence": "low", "cluster": "default", "namespace": "payments", "source_var": "OTHER_S3_ENDPOINT_URL", "repository": "https://git.example/pay"},
    {"bucket": "", "endpoint": "main-bucket.ceph.example.internal", "confidence": "low", "cluster": "default", "namespace": "payments", "source_var": "PPROF_DUMPER_S3_ENDPOINT_URL"}
  ]
}
""",
        encoding="utf-8",
    )

    rows = collect_bucket_usage_rows(bucket_reports_dir, config_dir)

    assert [row.bucket for row in rows] == ["", "main-bucket", "reports"]
    assert rows[0].source_var == "OTHER_S3_ENDPOINT_URL"
    assert rows[0].confidence == "low"
    assert rows[1].confidence == "medium"
    assert rows[2].endpoint == "reports.s3.example.com"
    assert rows[2].source_var == "S3_BUCKET_NAME, S3_HOST_BUCKET"


def test_collect_bucket_usage_rows_fails_for_missing_reports(tmp_path):
    assert collect_bucket_usage_rows(tmp_path / "missing-artifacts", tmp_path) == []
    with pytest.raises(SystemExit, match="reports directory not found"):
        collect_bucket_usage_rows_from_reports(tmp_path / "missing", tmp_path)

    empty_reports = tmp_path / "empty-reports"
    empty_reports.mkdir()
    with pytest.raises(SystemExit, match=r"No \*\.report\.json found"):
        collect_bucket_usage_rows_from_reports(empty_reports, tmp_path)


def test_collect_bucket_usage_rows_rejects_stale_bucket_reports(tmp_path):
    bucket_reports_dir = tmp_path / "artifacts" / "buckets"
    bucket_reports_dir.mkdir(parents=True)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "demo.yaml").write_text("product: demo\n", encoding="utf-8")
    (bucket_reports_dir / "removed-product.json").write_text(
        '{"schema_version": 1, "report_key": "removed-product", "product": "removed", "rows": []}',
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="Stale bucket artifacts found"):
        collect_bucket_usage_rows(bucket_reports_dir, config_dir)
