"""Shared LikeC4 metadata value helpers."""

from collections.abc import Iterable
from typing import Dict, List, Tuple

from ...config import clean_metadata_string

MetadataItems = List[Tuple[str, str]]
MetadataMap = Dict[str, List[str]]


def metadata_map(items: Iterable[Tuple[str, str]]) -> MetadataMap:
    metadata: MetadataMap = {}
    for raw_key, raw_value in items:
        key = clean_metadata_string(raw_key)
        value = clean_metadata_string(raw_value)
        if not key or not value:
            continue
        values = metadata.setdefault(key, [])
        if value not in values:
            values.append(value)
    return metadata


def append_summary(items: MetadataItems, key: str, value: str) -> None:
    text = clean_metadata_string(value)
    if text:
        items.append((key, text))


def preserved_items(metadata: MetadataMap, preserve_keys: Iterable[str]) -> MetadataItems:
    items: MetadataItems = []
    for key in preserve_keys:
        value = first(metadata, key)
        if value:
            items.append((key, value))
    return items


def first(metadata: MetadataMap, key: str) -> str:
    values = metadata.get(key) or []
    return values[0] if values else ""


def field(metadata: MetadataMap, key: str, label: str = "") -> str:
    value = first(metadata, key)
    if not value:
        return ""
    return f"{label or key}: {value}"


def summary(parts: Iterable[str]) -> str:
    return "; ".join(part for part in parts if part)


__all__ = [
    "MetadataItems",
    "MetadataMap",
    "append_summary",
    "field",
    "first",
    "metadata_map",
    "preserved_items",
    "summary",
]
