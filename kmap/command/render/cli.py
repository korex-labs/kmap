"""CLI wiring for the render command."""

import argparse
import os

from . import render_outputs


def add_render_parser(
    subparsers: argparse._SubParsersAction,
    *,
    default_architecture_file: str,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("render", help="Render architecture.json outputs")
    parser.add_argument("architecture_file", nargs="?", default=default_architecture_file)
    parser.add_argument(
        "--render",
        choices=["structurizr", "likec4", "both"],
        default=os.environ.get("KMAP_RENDER", "both"),
        help="Renderer output to write",
    )
    parser.add_argument("--struct-output-dir", default=os.environ.get("STRUCTURIZR_OUTPUT_DIR", ""))
    parser.add_argument("--likec4-output-dir", default=os.environ.get("LIKEC4_OUTPUT_DIR", ""))
    parser.add_argument(
        "--likec4-common-path",
        default=os.environ.get("LIKEC4_COMMON_PATH", "../common"),
        help="Relative path to LikeC4 common layer from generated likec4.config.json",
    )
    parser.set_defaults(func=render_outputs)
    return parser


__all__ = ["add_render_parser"]
