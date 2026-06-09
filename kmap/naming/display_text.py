"""Generic display text helpers."""

import re
from typing import List
from urllib.parse import urlparse

from ..config import clean_metadata_string
from ..identifiers import architecture_id_part


def is_url(value: str) -> bool:
    text = clean_metadata_string(value)
    if not text:
        return False
    parsed = urlparse(text)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def clip_text(value: str, limit: int = 120) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def short_label(value: str, limit: int = 36) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return clip_text(text, limit)


def humanize_slug(value: str) -> str:
    parts = [p for p in re.split(r"[-_.\s]+", value or "") if p]
    acronyms = {
        "api",
        "db",
        "dns",
        "go",
        "hpa",
        "http",
        "https",
        "k8s",
        "nats",
        "qa",
        "s3",
        "tcp",
        "uat",
        "vm",
    }
    out = []
    for part in parts:
        if part.lower() in acronyms:
            out.append(part.upper())
        else:
            out.append(part.capitalize())
    return " ".join(out) or (value or "")


def slug_parts(value: str) -> List[str]:
    return [architecture_id_part(part) for part in re.split(r"[-_.\s]+", value or "") if architecture_id_part(part)]


__all__ = ["clip_text", "humanize_slug", "is_url", "short_label", "slug_parts"]
