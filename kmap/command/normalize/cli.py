"""CLI wiring for the normalize command."""

import argparse
import os

from . import normalize_architecture


def add_normalize_parser(
    subparsers: argparse._SubParsersAction,
    *,
    default_reports_dir: str,
    default_dependencies_file: str,
    default_architecture_file: str,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("normalize", help="Write normalized architecture.json from inspect reports")
    parser.add_argument("reports_dir", nargs="?", default=default_reports_dir)
    parser.add_argument("output_file", nargs="?", default=default_architecture_file)
    parser.add_argument("--config", help="YAML config file with product and project metadata")
    parser.add_argument("--dependencies-file", default=os.environ.get("OUTPUT_FILE", default_dependencies_file))
    parser.add_argument("--org", default=os.environ.get("KMAP_ORG", "org"))
    parser.add_argument("--product", default=os.environ.get("KMAP_PRODUCT", "product"))
    parser.add_argument("--project", default=os.environ.get("KMAP_PROJECT", ""))
    parser.add_argument("--env", default=os.environ.get("KMAP_ENV", "prod"))
    parser.set_defaults(func=normalize_architecture)
    return parser


__all__ = ["add_normalize_parser"]
