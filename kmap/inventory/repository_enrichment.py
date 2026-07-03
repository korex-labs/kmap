"""Inventory row enrichment from repository catalog records."""

import os
from dataclasses import replace
from urllib.error import HTTPError, URLError

from ..logging import eprint
from .heuristics import namespace_heuristics, namespace_project_id
from .namespaces import InventoryRow
from .repository_cache import load_repository_cache, merge_repository_records, write_repository_cache
from .repository_gitlab import fetch_gitlab_repositories
from .repository_matching import normalize_repository_key, repository_index
from .repository_model import (
    RepositoryConfig,
    RepositoryRecord,
    repository_catalog_is_configured,
    repository_config_from_tool_config,
)


def enrich_inventory_rows_from_repositories(
    rows: list[InventoryRow], tool_config: dict[str, object]
) -> list[InventoryRow]:
    if not repository_catalog_is_configured(tool_config):
        return rows
    rows = attach_repository_ids(rows, tool_config)
    repository_ids = sorted({row.repository_id for row in rows if row.repository_id})
    records = repository_records_for_inventory(tool_config, repository_ids)
    if not records:
        return rows
    index = repository_index(records)
    return [enrich_inventory_row(row, index) for row in rows]


def attach_repository_ids(rows: list[InventoryRow], tool_config: dict[str, object]) -> list[InventoryRow]:
    heuristics = namespace_heuristics(tool_config or {})
    return [attach_repository_id(row, heuristics) for row in rows]


def attach_repository_id(row: InventoryRow, heuristics: dict[str, object]) -> InventoryRow:
    if row.repository_id:
        return row
    repository_id = namespace_project_id(row.namespace, heuristics)
    if not repository_id:
        return row
    return replace(row, repository_id=repository_id)


def repository_records_for_inventory(
    tool_config: dict[str, object], repository_ids: list[str]
) -> list[RepositoryRecord]:
    if not repository_catalog_is_configured(tool_config):
        return []
    config = repository_config_from_tool_config(tool_config)
    cached = load_repository_cache(config.cache_file)
    if config.enabled and config.provider == "gitlab":
        cached = refresh_repository_cache_if_possible(config, repository_ids, cached)
    return cached


def refresh_repository_cache_if_possible(
    config: RepositoryConfig,
    repository_ids: list[str],
    cached: list[RepositoryRecord],
) -> list[RepositoryRecord]:
    if not config.base_url or not repository_ids:
        return cached
    token = os.environ.get(config.token_env, "")
    if not token:
        eprint(f"[kmap] repository cache refresh skipped: {config.token_env} is not set")
        return cached
    try:
        records = fetch_gitlab_repositories(config, token, repository_ids)
    except (HTTPError, URLError, TimeoutError) as exc:
        eprint(f"[kmap] repository cache refresh skipped: {exc}")
        return cached
    merged = merge_repository_records(cached, records)
    write_repository_cache(config.cache_file, merged, provider=config.provider, base_url=config.base_url)
    return merged


def enrich_inventory_row(row: InventoryRow, index: dict[str, RepositoryRecord]) -> InventoryRow:
    record = index.get(normalize_repository_key(row.repository_id)) or index.get(
        normalize_repository_key(row.repository)
    )
    if record is None:
        return row
    return replace(
        row,
        repository=enriched_repository_url(row.repository, record),
        repository_id=record.id,
        repository_name=record.name,
        repository_path=record.path_with_namespace,
        repository_group=record.group_path,
        repository_archived=record.archived,
    )


def enriched_repository_url(repository: str, record: RepositoryRecord) -> str:
    normalized = normalize_repository_key(repository)
    if not repository or repository.startswith("repository:") or normalized == normalize_repository_key(record.id):
        return record.web_url or record.url or repository
    return repository


__all__ = [
    "attach_repository_id",
    "attach_repository_ids",
    "enrich_inventory_row",
    "enrich_inventory_rows_from_repositories",
    "enriched_repository_url",
    "refresh_repository_cache_if_possible",
    "repository_records_for_inventory",
]
