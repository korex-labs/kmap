"""Repository catalog dataclasses and config parsing."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import clean_bool, clean_metadata_string
from ..paths import SCHEMAS_ROOT

REPOSITORY_CACHE_SCHEMA_VERSION = 1
DEFAULT_REPOSITORY_CACHE_FILE = SCHEMAS_ROOT / "artifacts" / "repositories" / "gitlab.json"


@dataclass(frozen=True)
class RepositoryRecord:
    id: str
    name: str
    path: str
    path_with_namespace: str
    namespace_full_path: str
    group_path: str
    url: str
    web_url: str
    default_branch: str
    archived: str


@dataclass(frozen=True)
class RepositoryConfig:
    enabled: bool
    provider: str
    base_url: str
    token_env: str
    cache_file: Path


def repository_config_from_tool_config(tool_config: dict[str, Any]) -> RepositoryConfig:
    raw = (((tool_config or {}).get("inventory") or {}).get("repositories")) or {}
    if not isinstance(raw, dict):
        raw = {}
    provider = clean_metadata_string(raw.get("provider")) or "gitlab"
    return RepositoryConfig(
        enabled=clean_bool(raw.get("enabled"), False),
        provider=provider.lower(),
        base_url=clean_metadata_string(raw.get("base_url") or raw.get("url")),
        token_env=clean_metadata_string(raw.get("token_env")) or "GITLAB_TOKEN",
        cache_file=repository_cache_path(clean_metadata_string(raw.get("cache_file"))),
    )


def repository_cache_path(value: str) -> Path:
    if not value:
        return DEFAULT_REPOSITORY_CACHE_FILE
    path = Path(value)
    return path if path.is_absolute() else SCHEMAS_ROOT / path


def repository_catalog_is_configured(tool_config: dict[str, Any]) -> bool:
    inventory = (tool_config or {}).get("inventory")
    return isinstance(inventory, dict) and isinstance(inventory.get("repositories"), dict)


__all__ = [
    "DEFAULT_REPOSITORY_CACHE_FILE",
    "REPOSITORY_CACHE_SCHEMA_VERSION",
    "RepositoryConfig",
    "RepositoryRecord",
    "repository_cache_path",
    "repository_catalog_is_configured",
    "repository_config_from_tool_config",
]
