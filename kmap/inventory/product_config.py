"""Shared product config loading for inventory generation."""

from pathlib import Path
from typing import Any

from ..config import validate_config_shape
from ..io import load_yaml_config_or_error


def load_valid_product_config(config_file: Path) -> dict[str, Any]:
    config = load_yaml_config_or_error(config_file)
    errors, _warnings = validate_config_shape(config)
    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise SystemExit(f"Invalid product config: {config_file}\n{joined}")
    return config


__all__ = ["load_valid_product_config"]
