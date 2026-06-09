import argparse

from kmap.command.normalize import normalize_architecture
from kmap.command.normalize.cli import add_normalize_parser


def test_add_normalize_parser_wires_paths_metadata_and_function():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_normalize_parser(
        subparsers,
        default_reports_dir=".tmp/reports",
        default_dependencies_file=".tmp/reports/dependencies.list",
        default_architecture_file=".tmp/reports/architecture.json",
    )

    args = parser.parse_args(
        [
            "normalize",
            "reports",
            "architecture.json",
            "--dependencies-file",
            "dependencies.json",
            "--product",
            "demo",
            "--env",
            "stage",
        ]
    )

    assert args.func is normalize_architecture
    assert args.reports_dir == "reports"
    assert args.output_file == "architecture.json"
    assert args.dependencies_file == "dependencies.json"
    assert args.product == "demo"
    assert args.env == "stage"
