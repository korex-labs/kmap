"""Database engine inference helpers."""

import re

from ..config import clean_metadata_string

MYSQL_RE = re.compile(r"(mysql|mariadb)", re.IGNORECASE)
POSTGRES_RE = re.compile(r"(postgres|postgresql|pgsql|pgdatabase)", re.IGNORECASE)


def database_engine_from_text(*values: str) -> str:
    text = " ".join(clean_metadata_string(value).lower() for value in values if clean_metadata_string(value))
    if MYSQL_RE.search(text):
        return "mysql"
    if POSTGRES_RE.search(text):
        return "postgresql"
    return ""


__all__ = ["MYSQL_RE", "POSTGRES_RE", "database_engine_from_text"]
