"""View command argument validation."""

import argparse
from typing import Callable

ValidatePort = Callable[[str, str], str]


def validate_view_args(args: argparse.Namespace, *, validate_port: ValidatePort) -> str:
    product = (args.product or "").strip()
    if not product:
        raise SystemExit("Product name is required")
    if args.no_likec4 and args.no_structurizr:
        raise SystemExit("Nothing to view: both --no-likec4 and --no-structurizr were provided")
    args.likec4_port = validate_port(args.likec4_port, "--likec4-port")
    args.structurizr_port = validate_port(args.structurizr_port, "--structurizr-port")
    return product


__all__ = ["ValidatePort", "validate_view_args"]
