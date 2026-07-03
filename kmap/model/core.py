"""Entrypoints for normalized architecture model construction."""

import sys
from pathlib import Path
from typing import Any

from ..io import dump_json, ensure_dir
from ..logging import eprint
from .build import architecture_model_from_reports


def normalize_architecture(args) -> int:
    architecture = _architecture_model_from_reports(args)
    output_file = Path(args.output_file)
    ensure_dir(output_file.parent)
    dump_json(output_file, architecture)
    eprint(f"[kmap] wrote normalized architecture model: {output_file}")
    return 0


def _architecture_model_from_reports(args) -> dict[str, Any]:
    package = sys.modules.get("kmap.model")
    builder = getattr(package, "architecture_model_from_reports", architecture_model_from_reports)
    return builder(args)


__all__ = ["architecture_model_from_reports", "normalize_architecture"]
