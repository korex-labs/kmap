"""Dependency candidate input models."""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class DependencyCandidateInput:
    data: Dict[str, str]
    key: str
    value: str
    source: str
    source_name: str


@dataclass(frozen=True)
class BaseDependencyCandidateInput:
    key: str
    value: str
    host: str
    port: int | None
    path: str
    source: str
    source_name: str


__all__ = [
    "BaseDependencyCandidateInput",
    "DependencyCandidateInput",
]
