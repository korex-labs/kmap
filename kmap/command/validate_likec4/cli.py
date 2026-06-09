"""CLI wiring for the validate-likec4 command."""

import argparse
import os

from . import validate_likec4


def add_validate_likec4_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("validate-likec4", help="Validate generated LikeC4 projects")
    parser.add_argument("--root", default="../../Likec4", help="LikeC4 root directory")
    parser.add_argument("--docker", default=os.environ.get("DOCKER_BIN", "docker"), help="Docker binary")
    parser.add_argument("--image", default=os.environ.get("KMAP_VALIDATE_LIKEC4_IMAGE", "likec4/likec4"))
    parser.add_argument(
        "--product",
        action="append",
        default=[],
        help="Product project to validate; may be passed multiple times",
    )
    parser.add_argument(
        "--include-multi-project",
        action="store_true",
        help="Include top-level LikeC4 folders that also contain nested LikeC4 projects",
    )
    parser.set_defaults(func=validate_likec4)
    return parser


__all__ = ["add_validate_likec4_parser"]
