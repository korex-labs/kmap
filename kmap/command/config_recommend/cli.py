"""CLI wiring for the recommend-config command."""

import argparse

from . import config_recommend


def add_config_recommend_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("recommend-config", help="Recommend improvements for a kmap product config")
    parser.add_argument("config_file", help="YAML config file to inspect")
    parser.add_argument("--details", action="store_true", help="List every affected config path")
    parser.add_argument("--include-low", action="store_true", help="Include low-priority suggestions")
    parser.add_argument("--include-optional", action="store_true", help="Include optional resource suggestions")
    parser.set_defaults(func=config_recommend)
    return parser


__all__ = ["add_config_recommend_parser"]
