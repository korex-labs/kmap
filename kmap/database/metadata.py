"""Database dependency metadata extraction."""

import re
from typing import Any

from ..config import clean_metadata_string
from ..lists import append_unique
from .types import database_engine_from_text
from .url import (
    clean_database_name,
    database_hostish_parts,
    database_url_parts,
    normalized_database_url_text,
    parse_database_url,
)

DATABASE_NAME_KEY_RE = re.compile(
    r"(^|_)(DATABASE|DB|DBNAME|DB_NAME|MYSQL_DATABASE|MYSQL_DB|POSTGRES_DB|POSTGRES_DATABASE|PGDATABASE)($|_)",
    re.IGNORECASE,
)
DATABASE_INDEX_KEY_RE = re.compile(
    r"(redis|mongo|mongodb|clickhouse|elastic|elasticsearch).*(_|^)db($|_)", re.IGNORECASE
)


def _clean_database_name(value: Any) -> str:
    return clean_database_name(value)


def _database_name_entries(data: dict[str, str]) -> list[dict[str, str]]:
    entries = []
    for key, value in (data or {}).items():
        key_text = clean_metadata_string(key)
        if DATABASE_INDEX_KEY_RE.search(key_text):
            continue
        value_text = _clean_database_name(value)
        if not key_text or not value_text:
            continue
        if not DATABASE_NAME_KEY_RE.search(key_text):
            continue
        entries.append(
            {
                "var": key_text,
                "name": value_text,
                "engine": database_engine_from_text(key_text),
            }
        )
    return entries


def database_metadata_for_candidate(
    data: dict[str, str],
    candidate_key: str,
    candidate_value: str,
    host: str,
) -> dict[str, Any]:
    engine, url_host, url_names = parse_database_url(candidate_value)
    engine = engine or database_engine_from_text(candidate_key, candidate_value, host)
    if url_host and host and url_host != host:
        url_names = []

    names = list(url_names)
    source_vars = [candidate_key] if url_names else []
    sources = ["dsn_path"] if url_names else []

    if engine in {"mysql", "postgresql"}:
        merge_companion_database_entries(data, engine, names, source_vars, sources)

    if not engine and not names:
        return {}

    out: dict[str, Any] = {
        "engine": engine,
        "names": sorted(names),
        "source_vars": sorted(source_vars),
        "sources": sources,
    }
    return {key: value for key, value in out.items() if value}


def merge_companion_database_entries(
    data: dict[str, str],
    engine: str,
    names: list[str],
    source_vars: list[str],
    sources: list[str],
) -> None:
    for entry in _database_name_entries(data):
        entry_engine = entry.get("engine") or engine
        if entry_engine != engine:
            continue
        append_unique(names, entry["name"])
        append_unique(source_vars, entry["var"])
        append_unique(sources, "companion_var")


__all__ = [
    "append_unique",
    "database_engine_from_text",
    "database_hostish_parts",
    "database_metadata_for_candidate",
    "database_url_parts",
    "merge_companion_database_entries",
    "normalized_database_url_text",
    "parse_database_url",
]
