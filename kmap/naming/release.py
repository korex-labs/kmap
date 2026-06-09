"""Release-name matching and normalization helpers."""

import re


def matches_release_name(name: str, match_re: re.Pattern) -> bool:
    return bool(name and match_re.search(name))


def normalize_release_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name or "").strip("-")


__all__ = [
    "matches_release_name",
    "normalize_release_name",
]
