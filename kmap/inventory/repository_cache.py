"""Repository catalog cache serialization."""

from pathlib import Path
from typing import Any

from ..config import clean_metadata_string
from ..io import dump_json, ensure_dir, load_required_json_file
from ..logging import eprint
from .repository_model import REPOSITORY_CACHE_SCHEMA_VERSION, RepositoryRecord
from .schema import require_schema_version


def write_repository_cache(path: Path, records: list[RepositoryRecord], *, provider: str, base_url: str) -> Path:
    ensure_dir(path.parent)
    dump_json(
        path,
        {
            "schema_version": REPOSITORY_CACHE_SCHEMA_VERSION,
            "provider": provider,
            "base_url": base_url.rstrip("/"),
            "repositories": [repository_record_dict(record) for record in records],
        },
    )
    eprint(f"[kmap] wrote repository cache: {path}")
    return path


def load_repository_cache(path: Path) -> list[RepositoryRecord]:
    if not path.exists():
        return []
    payload = load_required_json_file(path)
    require_schema_version(
        payload,
        expected=REPOSITORY_CACHE_SCHEMA_VERSION,
        source=path,
        kind="repository cache",
    )
    return [
        repository_record_from_cache_item(item) for item in payload.get("repositories") or [] if isinstance(item, dict)
    ]


def merge_repository_records(
    cached: list[RepositoryRecord],
    fetched: list[RepositoryRecord],
) -> list[RepositoryRecord]:
    records = {record.id: record for record in cached if record.id}
    records.update({record.id: record for record in fetched if record.id})
    return sorted(records.values(), key=lambda item: item.path_with_namespace.lower())


def repository_record_from_cache_item(item: dict[str, Any]) -> RepositoryRecord:
    return RepositoryRecord(
        id=clean_metadata_string(item.get("id")),
        name=clean_metadata_string(item.get("name")),
        path=clean_metadata_string(item.get("path")),
        path_with_namespace=clean_metadata_string(item.get("path_with_namespace")),
        namespace_full_path=clean_metadata_string(item.get("namespace_full_path")),
        group_path=clean_metadata_string(item.get("group_path")),
        url=clean_metadata_string(item.get("url")),
        web_url=clean_metadata_string(item.get("web_url") or item.get("url")),
        default_branch=clean_metadata_string(item.get("default_branch")),
        archived=clean_metadata_string(item.get("archived")),
    )


def repository_record_dict(record: RepositoryRecord) -> dict[str, str]:
    return {
        "id": record.id,
        "name": record.name,
        "path": record.path,
        "path_with_namespace": record.path_with_namespace,
        "namespace_full_path": record.namespace_full_path,
        "group_path": record.group_path,
        "url": record.url,
        "web_url": record.web_url,
        "default_branch": record.default_branch,
        "archived": record.archived,
    }


__all__ = [
    "load_repository_cache",
    "merge_repository_records",
    "repository_record_dict",
    "repository_record_from_cache_item",
    "write_repository_cache",
]
