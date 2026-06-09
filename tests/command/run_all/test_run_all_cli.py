import argparse

from kmap.cli import parse_non_negative_float, parse_positive_int
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
