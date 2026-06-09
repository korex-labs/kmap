"""Database dependency metadata extraction."""

from .metadata import (
    append_unique,
    database_metadata_for_candidate,
    merge_companion_database_entries,
)
from .types import database_engine_from_text
from .url import (
    clean_database_name,
    database_hostish_parts,
    database_url_parts,
    normalized_database_url_text,
    parse_database_url,
)

__all__ = [
    "append_unique",
    "clean_database_name",
    "database_engine_from_text",
    "database_hostish_parts",
    "database_metadata_for_candidate",
    "database_url_parts",
    "merge_companion_database_entries",
    "normalized_database_url_text",
    "parse_database_url",
]
