"""Shared models for config recommendations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfigRecommendation:
    priority: str
    path: str
    reason: str
    snippet: str = ""
    details: tuple[str, ...] = ()


__all__ = ["ConfigRecommendation"]
