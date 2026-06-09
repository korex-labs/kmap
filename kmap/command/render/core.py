"""Render command orchestration."""

import argparse
import sys
from pathlib import Path
from typing import Callable

from ...config import slug_name
from ...io import load_required_json_file
from ...paths import SCHEMAS_ROOT
from ...render.likec4 import render_likec4
from ...render.structurizr.architecture import render_structurizr_architecture

RENDER_MODES = {"structurizr", "likec4", "both"}


def default_structurizr_output_dir(product: str) -> Path:
    return SCHEMAS_ROOT / "Structurizr" / slug_name(product or "product")


def architecture_product_name(architecture_file: str) -> str:
    architecture = load_required_json_file(Path(architecture_file))
    if not isinstance(architecture, dict) or not architecture:
        raise SystemExit(f"Invalid architecture model: {architecture_file}")
    return (
        ((architecture.get("product") or {}).get("name"))
        or ((architecture.get("workspace") or {}).get("product"))
        or "product"
    )


def render_outputs(args: argparse.Namespace) -> int:
    render_mode = getattr(args, "render", "both") or "both"
    if render_mode not in RENDER_MODES:
        raise SystemExit("--render must be one of structurizr, likec4, both")

    if render_mode in {"structurizr", "both"}:
        rc = render_structurizr_output(args)
        if rc != 0:
            return rc

    if render_mode in {"likec4", "both"}:
        rc = render_likec4_output(args)
        if rc != 0:
            return rc

    return 0


def render_structurizr_output(args: argparse.Namespace) -> int:
    output_dir = getattr(args, "struct_output_dir", "") or str(
        default_structurizr_output_dir(_architecture_product_name(args.architecture_file))
    )
    return _render_structurizr_architecture(
        argparse.Namespace(
            architecture_file=args.architecture_file,
            output_dir=output_dir,
        )
    )


def render_likec4_output(args: argparse.Namespace) -> int:
    return _render_likec4(
        argparse.Namespace(
            architecture_file=args.architecture_file,
            output_dir=getattr(args, "likec4_output_dir", ""),
            common_path=getattr(args, "likec4_common_path", "../common"),
        )
    )


def _package_attr(name: str, default: Callable):
    package = sys.modules.get("kmap.command.render")
    return getattr(package, name, default)


def _architecture_product_name(architecture_file: str) -> str:
    return _package_attr("architecture_product_name", architecture_product_name)(architecture_file)


def _render_structurizr_architecture(args: argparse.Namespace) -> int:
    return _package_attr("render_structurizr_architecture", render_structurizr_architecture)(args)


def _render_likec4(args: argparse.Namespace) -> int:
    return _package_attr("render_likec4", render_likec4)(args)


__all__ = [
    "RENDER_MODES",
    "architecture_product_name",
    "default_structurizr_output_dir",
    "render_likec4",
    "render_likec4_output",
    "render_outputs",
    "render_structurizr_architecture",
    "render_structurizr_output",
]
