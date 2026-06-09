"""Stable identifier and escaping helpers."""

import hashlib
import re
from urllib.parse import urlparse

from .config import slug_name


def ident(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        value = "id"
    if value[0].isdigit():
        value = "_" + value
    return value


def q(value: str) -> str:
    text = str(value or "")
    return text.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t").replace('"', '\\"')


def sq(value: str) -> str:
    text = str(value or "")
    return text.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t").replace("'", "\\'")


def dsl_url(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    if re.search(r"[\s\"'`{}<>\\\\]", text):
        return ""
    return text


def short_hash(value: str, length: int = 8) -> str:
    return hashlib.sha1(str(value or "").encode("utf-8")).hexdigest()[:length]


def architecture_id_part(value: str) -> str:
    return ident(slug_name(value).replace("-", "_")).lower()


def architecture_id(*parts: str) -> str:
    return ".".join(architecture_id_parts(parts))


def architecture_id_parts(parts) -> list[str]:
    return [part for part in (architecture_id_part(raw) for raw in parts) if part]


__all__ = [
    "architecture_id",
    "architecture_id_part",
    "architecture_id_parts",
    "dsl_url",
    "ident",
    "q",
    "short_hash",
    "sq",
]
