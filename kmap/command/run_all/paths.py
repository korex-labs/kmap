"""Output path defaults for run-all."""

import argparse
import os
from pathlib import Path

from ...config import slug_name
from ...paths import KMAP_TMP_DIR

DEFAULT_REPORTS_DIR = str(KMAP_TMP_DIR / "reports")
DEFAULT_DEPENDENCIES_FILE = str(KMAP_TMP_DIR / "reports" / "dependencies.list")
DEFAULT_ARCHITECTURE_FILE = str(KMAP_TMP_DIR / "reports" / "architecture.json")


def apply_default_output_paths(args: argparse.Namespace, namespaces: list[str]) -> None:
    """Resolve run-all default output paths in-place."""

    default_out_dir = os.environ.get("OUT_DIR", DEFAULT_REPORTS_DIR)
    if args.out_dir == default_out_dir:
        if len(namespaces) == 1:
            args.out_dir = str(KMAP_TMP_DIR / namespaces[0])
        else:
            args.out_dir = str(KMAP_TMP_DIR / f"{slug_name(args.product or 'product')}-multi")

    default_deps_file = os.environ.get("OUTPUT_FILE", DEFAULT_DEPENDENCIES_FILE)
    if args.dependencies_file == default_deps_file:
        args.dependencies_file = str(Path(args.out_dir) / "dependencies.list")

    if args.dependencies_json_output_file is None and os.environ.get("JSON_OUTPUT_FILE") is None:
        args.dependencies_json_output_file = str(Path(args.out_dir) / "dependencies.json")

    if args.architecture_output_file == DEFAULT_ARCHITECTURE_FILE:
        args.architecture_output_file = str(Path(args.out_dir) / "architecture.json")
