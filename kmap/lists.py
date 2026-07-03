"""Small list de-duplication helpers."""

from typing import Any

from .config import clean_metadata_string


def append_unique(items: list[Any], value: Any) -> None:
    if value not in items:
        items.append(value)


def append_truthy_unique(items: list[Any], value: Any) -> None:
    if value:
        append_unique(items, value)


def append_clean_unique(items: list[Any], value: Any) -> None:
    if value is None:
        return
    if isinstance(value, str):
        value = clean_metadata_string(value)
        if not value:
            return
    append_unique(items, value)


def append_clean_unique_string(items: list[str], value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            append_clean_unique_string(items, item)
        return
    text = clean_metadata_string(value)
    if text:
        append_unique(items, text)


__all__ = ["append_clean_unique", "append_clean_unique_string", "append_truthy_unique", "append_unique"]
