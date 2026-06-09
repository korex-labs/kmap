"""Docker command builders for local viewers."""

import argparse
import shlex

from ...paths import SCHEMAS_ROOT


def likec4_run_command(args: argparse.Namespace, product: str, name: str) -> list[str]:
    return [
        args.docker,
        "run",
        "-d",
        "--init",
        "--name",
        name,
        "-p",
        f"{args.likec4_port}:5173",
        "-v",
        f"{SCHEMAS_ROOT}:/data",
        args.likec4_image,
        "start",
        "--host",
        "0.0.0.0",
        f"Likec4/{product}",
    ]


def structurizr_command_args(value: str) -> list[str]:
    try:
        return shlex.split(value or "")
    except ValueError as exc:
        raise SystemExit(f"Invalid --structurizr-args: {exc}") from exc


def structurizr_run_command(args: argparse.Namespace, product: str, name: str) -> list[str]:
    return [
        args.docker,
        "run",
        "-d",
        "--init",
        "--name",
        name,
        "-p",
        f"{args.structurizr_port}:8080",
        "-v",
        f"{SCHEMAS_ROOT / 'Structurizr' / product}:/usr/local/structurizr",
        "-v",
        f"{SCHEMAS_ROOT / 'Structurizr' / 'common'}:/usr/local/common",
        args.structurizr_image,
        *structurizr_command_args(args.structurizr_args),
    ]


__all__ = ["likec4_run_command", "structurizr_command_args", "structurizr_run_command"]
