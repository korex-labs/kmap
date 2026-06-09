"""CLI wiring for the validate-structurizr command."""

import argparse

from . import validate_structurizr


def add_validate_structurizr_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("validate-structurizr", help="Validate generated Structurizr workspaces")
    parser.add_argument("--root", default="../../Structurizr", help="Structurizr root directory")
    parser.add_argument(
        "--product",
        action="append",
        default=[],
        help="Product workspace to validate; may be passed multiple times",
    )
    parser.set_defaults(func=validate_structurizr)
    return parser


__all__ = ["add_validate_structurizr_parser"]
