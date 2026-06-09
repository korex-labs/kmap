"""Generator metadata helpers for architecture models."""

import time
from typing import Dict

from .. import __version__
from ..config import clean_metadata_string

KMAP_GENERATOR_NAME = "kmap"
KMAP_GENERATOR_VERSION = __version__
KMAP_RULES_FILE = "GENERATION_RULES.md"


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def generator_metadata(config_file: str = "", renderer: str = "") -> Dict[str, str]:
    return {
        "tool": KMAP_GENERATOR_NAME,
        "version": KMAP_GENERATOR_VERSION,
        "rules_file": KMAP_RULES_FILE,
        "config_file": clean_metadata_string(config_file),
        "renderer": clean_metadata_string(renderer),
    }


__all__ = [
    "KMAP_GENERATOR_NAME",
    "KMAP_GENERATOR_VERSION",
    "KMAP_RULES_FILE",
    "generator_metadata",
    "utc_timestamp",
]
