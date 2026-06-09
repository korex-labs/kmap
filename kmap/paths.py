"""Shared filesystem roots for kmap commands."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
KMAP_DIR = PACKAGE_DIR.parent
SCHEMAS_ROOT = Path.cwd()
KMAP_TMP_DIR = SCHEMAS_ROOT / ".tmp"

__all__ = ["KMAP_DIR", "KMAP_TMP_DIR", "PACKAGE_DIR", "SCHEMAS_ROOT"]
