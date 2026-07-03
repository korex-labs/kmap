import argparse
import json

from kmap import cli as cli_module
from kmap.cli import parse_non_negative_float, parse_positive_int
from kmap.command.inspect import namespace_context as namespace_context_module
from kmap.command.run_all import run_all
from kmap.command.run_all.cli import add_run_all_parser


def test_add_run_all_parser_wires_pipeline_options_and_function():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_run_all_parser(
        subparsers,
        default_reports_dir=".tmp/reports",
        default_dependencies_file=".tmp/reports/dependencies.list",
        default_architecture_file=".tmp/reports/architecture.json",
        default_match_re="main",
        parse_non_negative_float=parse_non_negative_float,
        parse_positive_int=parse_positive_int,
    )

    args = parser.parse_args(
        [
            "run-all",
            "--config",
            "product.yaml",
            "-n",
            "payments",
            "--output",
            "lines",
            "--render",
            "structurizr",
            "--inventory-output-dir",
            "Inventory",
        ]
    )

    assert args.func is run_all
    assert args.config == "product.yaml"
    assert args.namespace == ["payments"]
    assert args.output == "lines"
    assert args.render == "structurizr"
    assert args.inventory_output_dir == "Inventory"
    assert args.match_regex == "main"
    assert args.cluster_preflight is True


def test_add_run_all_parser_can_skip_cluster_preflight():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_run_all_parser(
        subparsers,
        default_reports_dir=".tmp/reports",
        default_dependencies_file=".tmp/reports/dependencies.list",
        default_architecture_file=".tmp/reports/architecture.json",
        default_match_re="main",
        parse_non_negative_float=parse_non_negative_float,
        parse_positive_int=parse_positive_int,
    )

    args = parser.parse_args(["run-all", "-n", "payments", "--skip-cluster-preflight"])

    assert args.cluster_preflight is False


def test_run_all_cli_smoke_generates_mocked_outputs(monkeypatch, tmp_path):
    class EmptyKubectlClient:
        def __init__(self, **kwargs):
            self.namespace = kwargs.get("namespace", "")

        def current_context(self):
            return "mock-cluster"

        def get_json(self, kind):
            return {"items": []}

        def helm_list(self, namespace):
            return []

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "product.yaml"
    config_file.write_text(
        "\n".join(
            [
                "org: web",
                "product: example-product",
                "title: Example Product",
                "env: prod",
                "namespaces:",
                "  example-api-prod-1234: {}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    reports_dir = tmp_path / "reports"
    architecture_file = reports_dir / "architecture.json"
    dependencies_file = reports_dir / "dependencies.list"
    dependencies_json_file = reports_dir / "dependencies.json"
    buckets_dir = tmp_path / "buckets"
    inventory_dir = tmp_path / "Inventory"
    structurizr_dir = tmp_path / "Structurizr" / "example-product"
    likec4_dir = tmp_path / "Likec4" / "example-product"

    monkeypatch.setattr(namespace_context_module, "KubectlClient", EmptyKubectlClient)

    rc = cli_module.main(
        [
            "run-all",
            "--config",
            str(config_file),
            "--data-mode",
            "mocked",
            "--mock-seed",
            "ci",
            "--no-exec",
            "--skip-cluster-preflight",
            "--output",
            "lines",
            "--out-dir",
            str(reports_dir),
            "--dependencies-file",
            str(dependencies_file),
            "--dependencies-json-output-file",
            str(dependencies_json_file),
            "--architecture-output-file",
            str(architecture_file),
            "--bucket-reports-dir",
            str(buckets_dir),
            "--inventory-output-dir",
            str(inventory_dir),
            "--struct-output-dir",
            str(structurizr_dir),
            "--likec4-output-dir",
            str(likec4_dir),
        ]
    )

    assert rc == 0
    assert (reports_dir / "example-api-prod-1234.report.json").is_file()
    assert dependencies_file.is_file()
    assert dependencies_json_file.is_file()
    assert architecture_file.is_file()
    assert (buckets_dir / "product.json").is_file()
    assert (inventory_dir / "namespaces.html").is_file()
    assert (inventory_dir / "buckets.html").is_file()
    assert (structurizr_dir / "workspace.dsl").is_file()
    assert (likec4_dir / "likec4.config.json").is_file()

    report = json.loads((reports_dir / "example-api-prod-1234.report.json").read_text(encoding="utf-8"))
    assert report["workloads"] == []
    architecture = json.loads(architecture_file.read_text(encoding="utf-8"))
    assert architecture["product"]["name"] == "example-product"
    bucket_payload = json.loads((buckets_dir / "product.json").read_text(encoding="utf-8"))
    assert bucket_payload["report_key"] == "product"
    assert bucket_payload["product"] == "example-product"
    assert bucket_payload["rows"] == []
    namespaces_html = (inventory_dir / "namespaces.html").read_text(encoding="utf-8")
    assert "example-api-prod-1234" in namespaces_html
    assert "Example Product" in namespaces_html
