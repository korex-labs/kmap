"""CLI wiring for the combine command."""

import argparse
import os

from . import combine_reports


def add_combine_parser(
    subparsers: argparse._SubParsersAction,
    *,
    default_reports_dir: str,
    default_dependencies_file: str,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("combine", help="Combine namespace reports")
    parser.add_argument("reports_dir", nargs="?", default=default_reports_dir)
    parser.add_argument("--output-file", default=os.environ.get("OUTPUT_FILE", default_dependencies_file))
    parser.add_argument("--json-output-file", default=os.environ.get("JSON_OUTPUT_FILE"))
    parser.set_defaults(func=combine_reports)
    return parser


__all__ = ["add_combine_parser"]
