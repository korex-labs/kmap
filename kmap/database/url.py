"""Database URL parsing helpers."""

from typing import List, Optional, Tuple
from urllib.parse import unquote, urlparse

from ..config import clean_metadata_string
from ..hostish import parse_hostish
from .types import database_engine_from_text


def clean_database_name(value) -> str:
    text = clean_metadata_string(value)
    if not text:
        return ""
    text = unquote(text).strip().strip('"').strip("'")
    if not text or text in {"/", ".", ".."}:
        return ""
    if text.isdigit():
        return ""
    if "/" in text:
        text = text.split("/", 1)[0]
    if text.isdigit():
        return ""
    return text.strip()


def parse_database_url(value: str) -> Tuple[str, Optional[str], List[str]]:
    text = normalized_database_url_text(value)
    if not text:
        return "", None, []

    parsed = urlparse(text)
    engine, host, names = database_url_parts(parsed)

    if not host:
        host, names = database_hostish_parts(text, engine, names)

    return engine, host or None, sorted(names)


def normalized_database_url_text(value: str) -> str:
    text = clean_metadata_string(value).strip('"').strip("'")
    return text[5:] if text.lower().startswith("jdbc:") else text


def database_url_parts(parsed) -> Tuple[str, str, List[str]]:
    engine = database_engine_from_text(parsed.scheme)
    host = (parsed.hostname or "").lower()
    names = []
    db_name = clean_database_name(parsed.path.lstrip("/")) if engine and host else ""
    if db_name:
        names.append(db_name)
    return engine, host, names


def database_hostish_parts(text: str, engine: str, names: List[str]) -> Tuple[str, List[str]]:
    hostish = parse_hostish(text)
    if not hostish:
        return "", names
    host = hostish[0]
    db_name = clean_database_name((hostish[2] or "").lstrip("/")) if engine else ""
    if db_name and db_name not in names:
        names.append(db_name)
    return host, names


__all__ = [
    "clean_database_name",
    "database_hostish_parts",
    "database_url_parts",
    "normalized_database_url_text",
    "parse_database_url",
]
