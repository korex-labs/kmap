import argparse

from kmap.cli import parse_non_negative_float, parse_positive_int
from kmap.command.inspect.cli import add_inspect_parser
from kmap.command.inspect.namespace import inspect_namespaces


def test_add_inspect_parser_wires_namespace_options_and_function():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_inspect_parser(
        subparsers,
        default_reports_dir=".tmp/reports",
        default_match_re="main",
        parse_non_negative_float=parse_non_negative_float,
        parse_positive_int=parse_positive_int,
    )

    args = parser.parse_args(
        [
            "inspect",
            "-n",
            "payments",
            "--namespace-project",
            "payments=pay",
            "--format",
            "json",
            "--max-exec-pods-per-workload",
            "2",
        ]
    )

    assert args.func is inspect_namespaces
    assert args.namespace == ["payments"]
    assert args.namespace_project == ["payments=pay"]
    assert args.format == "json"
    assert args.max_exec_pods_per_workload == 2
    assert args.match_regex == "main"
