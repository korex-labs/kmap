"""CLI wiring for the view command."""

import argparse
import os

from . import view_product


def add_view_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("view", help="Start local viewers for generated output")
    parser.add_argument("product", help="Generated product directory under Likec4/ and Structurizr/")
    parser.add_argument("--docker", default=os.environ.get("DOCKER_BIN", "docker"))
    parser.add_argument("--likec4-port", default=os.environ.get("KMAP_VIEW_LIKEC4_PORT", "5173"))
    parser.add_argument("--structurizr-port", default=os.environ.get("KMAP_VIEW_STRUCTURIZR_PORT", "8080"))
    parser.add_argument("--likec4-image", default=None)
    parser.add_argument(
        "--structurizr-image",
        default=None,
    )
    parser.add_argument(
        "--structurizr-args",
        default=None,
        help="Additional command arguments for the Structurizr image",
    )
    view_mode = parser.add_mutually_exclusive_group()
    view_mode.add_argument("--restart", action="store_true", help="Recreate viewer containers")
    view_mode.add_argument("--stop", action="store_true", help="Stop viewer containers")
    parser.add_argument("--no-likec4", action="store_true", help="Do not start or stop the LikeC4 viewer")
    parser.add_argument("--no-structurizr", action="store_true", help="Do not start or stop the Structurizr viewer")
    parser.set_defaults(func=view_product)
    return parser


__all__ = ["add_view_parser"]
