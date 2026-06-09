"""Run-all command package."""

from .core import run_all
from .paths import DEFAULT_ARCHITECTURE_FILE, DEFAULT_DEPENDENCIES_FILE, DEFAULT_REPORTS_DIR

__all__ = ["DEFAULT_ARCHITECTURE_FILE", "DEFAULT_DEPENDENCIES_FILE", "DEFAULT_REPORTS_DIR", "run_all"]
