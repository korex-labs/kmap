"""Optional repository catalog discovery and inventory enrichment."""

from .repository_cache import load_repository_cache, merge_repository_records, write_repository_cache
from .repository_enrichment import enrich_inventory_rows_from_repositories
from .repository_gitlab import fetch_gitlab_project, gitlab_project_url, repository_record_from_gitlab_project
from .repository_matching import repository_index
from .repository_model import (
    DEFAULT_REPOSITORY_CACHE_FILE,
    REPOSITORY_CACHE_SCHEMA_VERSION,
    RepositoryConfig,
    RepositoryRecord,
    repository_config_from_tool_config,
)


def fetch_gitlab_repositories(
    config: RepositoryConfig,
    token: str,
    repository_ids: list[str],
) -> list[RepositoryRecord]:
    records: dict[str, RepositoryRecord] = {}
    for repository_id in repository_ids:
        project = fetch_gitlab_project(config.base_url, repository_id, token)
        if not project:
            continue
        record = repository_record_from_gitlab_project(project)
        if record.id:
            records[record.id] = record
    return sorted(records.values(), key=lambda item: item.path_with_namespace.lower())


__all__ = [
    "DEFAULT_REPOSITORY_CACHE_FILE",
    "REPOSITORY_CACHE_SCHEMA_VERSION",
    "RepositoryConfig",
    "RepositoryRecord",
    "enrich_inventory_rows_from_repositories",
    "fetch_gitlab_repositories",
    "gitlab_project_url",
    "load_repository_cache",
    "merge_repository_records",
    "repository_config_from_tool_config",
    "repository_index",
    "repository_record_from_gitlab_project",
    "write_repository_cache",
]
