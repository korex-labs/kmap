import argparse

from kmap.command.combine import combine_reports
from kmap.command.combine.cli import add_combine_parser


def test_add_combine_parser_wires_defaults_and_function():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_combine_parser(
        subparsers,
        default_reports_dir=".tmp/reports",
        default_dependencies_file=".tmp/reports/dependencies.list",
    )

    args = parser.parse_args(["combine", "reports", "--output-file", "deps.list", "--json-output-file", "deps.json"])

    assert args.func is combine_reports
    assert args.reports_dir == "reports"
    assert args.output_file == "deps.list"
    assert args.json_output_file == "deps.json"
