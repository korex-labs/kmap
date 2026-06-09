"""Shared helpers for LikeC4 generated views."""

from typing import Any, Dict, List

from ...config import clean_metadata_string
from ...identifiers import q
from .common import likec4_alias


def quote(value: str) -> str:
    return q(value)


def view_title(*parts: str) -> str:
    cleaned = [clean_metadata_string(part) for part in parts if clean_metadata_string(part)]
    return " / ".join(cleaned)


def system_ref(system_id: str) -> str:
    return likec4_alias(system_id)


def system_ref_from_item(system: Dict[str, Any]) -> str:
    return system_ref(system.get("id") or "")


def include_line(ref: str) -> str:
    return f"    include {ref}"


def include_system_line(system_id: str) -> str:
    return include_line(system_ref(system_id))


def view_token(value: str) -> str:
    return likec4_alias(value.lower())


def view_footer_lines(layout: str) -> List[str]:
    return [f"    autoLayout {layout}", "  }", ""]


__all__ = [
    "include_line",
    "include_system_line",
    "quote",
    "system_ref",
    "system_ref_from_item",
    "view_footer_lines",
    "view_title",
    "view_token",
]
