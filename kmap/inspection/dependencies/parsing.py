"""Dependency candidate value parsing helpers."""

from typing import List, Tuple

from ...hostish import parse_hostish


def dependency_value_parts(value: str) -> List[str]:
    raw_parts = [part.strip() for part in value.split(",")] if "," in value else [value]
    return [part for part in raw_parts if part]


def parse_dependency_hostish(raw_part: str) -> Tuple[str, int | None, str] | None:
    parsed = parse_hostish(raw_part)
    if not parsed and raw_part.lower().startswith("jdbc:"):
        parsed = parse_hostish(raw_part[5:])
    return parsed


def dependency_candidate_key(host: str, port: int | None) -> str:
    return f"{host}:{port}" if port else host


__all__ = ["dependency_candidate_key", "dependency_value_parts", "parse_dependency_hostish"]
