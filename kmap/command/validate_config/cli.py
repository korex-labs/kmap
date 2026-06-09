"""CLI wiring for the validate-config command."""

import argparse

from . import validate_config


def add_validate_config_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("validate-config", help="Validate a kmap product config")
    parser.add_argument("config_file", help="YAML config file to validate")
    parser.set_defaults(func=validate_config)
    return parser


__all__ = ["add_validate_config_parser"]
