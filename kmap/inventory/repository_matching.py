"""Repository catalog matching helpers."""

from urllib.parse import urlparse

from ..config import clean_metadata_string
from .repository_model import RepositoryRecord


def repository_index(records: list[RepositoryRecord]) -> dict[str, RepositoryRecord]:
    index: dict[str, RepositoryRecord] = {}
    for record in records:
        for key in repository_match_keys(record):
            index.setdefault(key, record)
    return index


def repository_match_keys(record: RepositoryRecord) -> list[str]:
    values = [
        record.id,
        record.url,
        record.web_url,
        record.path_with_namespace,
        strip_git_suffix(record.path_with_namespace),
    ]
    values.extend(repository_url_path_keys(record.url))
    values.extend(repository_url_path_keys(record.web_url))
    return sorted({normalize_repository_key(value) for value in values if normalize_repository_key(value)})


def repository_url_path_keys(url: str) -> list[str]:
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path:
        return []
    return [path, strip_git_suffix(path)]


def strip_git_suffix(value: str) -> str:
    return value.removesuffix(".git")


def normalize_repository_key(value: str) -> str:
    return clean_metadata_string(strip_git_suffix(value)).strip("/").lower()


__all__ = [
    "normalize_repository_key",
    "repository_index",
    "repository_match_keys",
    "repository_url_path_keys",
    "strip_git_suffix",
]
