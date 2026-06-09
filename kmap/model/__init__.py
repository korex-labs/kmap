"""Normalized architecture model command entry points."""

from .build import architecture_model_from_reports
from .core import normalize_architecture

__all__ = ["architecture_model_from_reports", "normalize_architecture"]
