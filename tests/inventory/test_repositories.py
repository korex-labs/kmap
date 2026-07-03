import json
from urllib.error import HTTPError

import pytest

from kmap.inventory import repository_gitlab
from kmap.inventory.namespaces import InventoryRow
from kmap.inventory.repositories import (
    REPOSITORY_CACHE_SCHEMA_VERSION,
    RepositoryRecord,
    enrich_inventory_rows_from_repositories,
    fetch_gitlab_repositories,
    gitlab_project_url,
    load_repository_cache,
    repository_config_from_tool_config,
    repository_index,
    repository_record_from_gitlab_project,
    write_repository_cache,
)


def test_repository_config_is_disabled_by_default_and_resolves_relative_cache_path():
    config = repository_config_from_tool_config({})

    assert config.enabled is False
    assert config.provider == "gitlab"
    assert config.token_env == "GITLAB_TOKEN"
    assert str(config.cache_file).endswith("artifacts/repositories/gitlab.json")

    configured = repository_config_from_tool_config(
        {
            "inventory": {
                "repositories": {
                    "enabled": True,
                    "base_url": "https://git.example",
                    "token_env": "TEAM_GITLAB_TOKEN",
                    "cache_file": "tmp/repos.json",
                }
            }
        }
    )

    assert configured.enabled is True
    assert configured.base_url == "https://git.example"
    assert configured.token_env == "TEAM_GITLAB_TOKEN"
    assert configured.cache_file.is_absolute()


def test_repository_record_from_gitlab_project_keeps_generic_identity_fields():
    record = repository_record_from_gitlab_project(
        {
            "id": 123,
            "name": "Payments API",
            "path": "payments-api",
            "path_with_namespace": "team/backend/payments-api",
            "http_url_to_repo": "https://git.example/team/backend/payments-api.git",
            "web_url": "https://git.example/team/backend/payments-api",
            "default_branch": "main",
            "archived": False,
            "namespace": {"full_path": "team/backend"},
        }
    )

    assert record.id == "123"
    assert record.name == "Payments API"
    assert record.path_with_namespace == "team/backend/payments-api"
    assert record.group_path == "team/backend"
    assert record.url.endswith(".git")
    assert record.web_url.endswith("/payments-api")
    assert record.default_branch == "main"
    assert record.archived == "false"


def test_repository_cache_round_trip_and_index_match_multiple_repository_shapes(tmp_path):
    cache_file = tmp_path / "repositories.json"
    record = RepositoryRecord(
        id="123",
        name="Payments API",
        path="payments-api",
        path_with_namespace="team/backend/payments-api",
        namespace_full_path="team/backend",
        group_path="team/backend",
        url="https://git.example/team/backend/payments-api.git",
        web_url="https://git.example/team/backend/payments-api",
        default_branch="main",
        archived="false",
    )

    write_repository_cache(cache_file, [record], provider="gitlab", base_url="https://git.example/")

    payload = json.loads(cache_file.read_text(encoding="utf-8"))
    assert payload["schema_version"] == REPOSITORY_CACHE_SCHEMA_VERSION
    loaded = load_repository_cache(cache_file)
    index = repository_index(loaded)
    assert index["123"].name == "Payments API"
    assert index["team/backend/payments-api"].id == "123"
    assert index["https://git.example/team/backend/payments-api"].id == "123"


def test_enrich_inventory_rows_uses_cache_without_requiring_token(monkeypatch, tmp_path):
    cache_file = tmp_path / "repositories.json"
    write_repository_cache(
        cache_file,
        [
            RepositoryRecord(
                id="123",
                name="Payments API",
                path="payments-api",
                path_with_namespace="team/backend/payments-api",
                namespace_full_path="team/backend",
                group_path="team/backend",
                url="https://git.example/team/backend/payments-api.git",
                web_url="https://git.example/team/backend/payments-api",
                default_branch="main",
                archived="false",
            )
        ],
        provider="gitlab",
        base_url="https://git.example",
    )
    monkeypatch.delenv("TEAM_GITLAB_TOKEN", raising=False)

    rows = enrich_inventory_rows_from_repositories(
        [
            InventoryRow(
                cluster="cluster-a",
                product="pay",
                namespace="payments-api-prod",
                repository="https://git.example/team/backend/payments-api",
                owner_team="Payments",
                repository_id="123",
                labels={"app": "payments"},
                last_seen_at="2026-05-20T09:30:00+00:00",
            )
        ],
        {
            "inventory": {
                "repositories": {
                    "enabled": True,
                    "base_url": "https://git.example",
                    "token_env": "TEAM_GITLAB_TOKEN",
                    "cache_file": str(cache_file),
                }
            }
        },
    )

    assert rows[0].repository_id == "123"
    assert rows[0].repository_name == "Payments API"
    assert rows[0].repository_path == "team/backend/payments-api"
    assert rows[0].repository_group == "team/backend"
    assert rows[0].repository_archived == "false"
    assert rows[0].labels == {"app": "payments"}
    assert rows[0].last_seen_at == "2026-05-20T09:30:00+00:00"


def test_enrich_inventory_rows_is_noop_without_repository_catalog_config():
    rows = [
        InventoryRow(
            cluster="cluster-a",
            product="pay",
            namespace="payments-api-prod",
            repository="https://git.example/team/backend/payments-api",
            owner_team="Payments",
        )
    ]

    assert enrich_inventory_rows_from_repositories(rows, {}) is rows


def test_enrich_inventory_rows_can_attach_repository_id_from_configured_namespace_suffix(monkeypatch, tmp_path):
    cache_file = tmp_path / "repositories.json"
    write_repository_cache(
        cache_file,
        [
            RepositoryRecord(
                id="1234",
                name="Payments API",
                path="payments-api",
                path_with_namespace="team/backend/payments-api",
                namespace_full_path="team/backend",
                group_path="team/backend",
                url="https://git.example/team/backend/payments-api.git",
                web_url="https://git.example/team/backend/payments-api",
                default_branch="main",
                archived="false",
            )
        ],
        provider="gitlab",
        base_url="https://git.example",
    )
    monkeypatch.delenv("TEAM_GITLAB_TOKEN", raising=False)

    rows = enrich_inventory_rows_from_repositories(
        [
            InventoryRow(
                cluster="cluster-a",
                product="pay",
                namespace="payments-api-prod-1234",
                repository="repository:1234",
                owner_team="Payments",
                labels={"app": "payments"},
            )
        ],
        {
            "inventory": {
                "namespace_heuristics": {"project_id_suffix": {"enabled": True, "pattern": r"[-](?P<project_id>\d+)$"}},
                "repositories": {
                    "enabled": True,
                    "base_url": "https://git.example",
                    "token_env": "TEAM_GITLAB_TOKEN",
                    "cache_file": str(cache_file),
                },
            }
        },
    )

    assert rows[0].repository_id == "1234"
    assert rows[0].repository == "https://git.example/team/backend/payments-api"
    assert rows[0].labels == {"app": "payments"}


def test_load_repository_cache_rejects_malformed_schema_version(tmp_path):
    cache_file = tmp_path / "repositories.json"
    cache_file.write_text('{"schema_version": "bad", "repositories": []}', encoding="utf-8")

    with pytest.raises(SystemExit, match="Unsupported repository cache schema version"):
        load_repository_cache(cache_file)


def test_gitlab_project_url_encodes_repository_id():
    assert gitlab_project_url("https://git.example/", "team/backend/payments-api") == (
        "https://git.example/api/v4/projects/team%2Fbackend%2Fpayments-api"
    )


def test_fetch_gitlab_repositories_deduplicates_projects(monkeypatch):
    config = repository_config_from_tool_config(
        {
            "inventory": {
                "repositories": {
                    "enabled": True,
                    "base_url": "https://git.example",
                }
            }
        }
    )

    def fake_fetch_project(base_url, repository_id, token):
        assert base_url == "https://git.example"
        assert repository_id in {"123", "1234"}
        assert token == "secret"
        return {
            "id": 123,
            "name": "Payments API",
            "path": "payments-api",
            "path_with_namespace": "team/backend/payments-api",
            "web_url": "https://git.example/team/backend/payments-api",
            "namespace": {"full_path": "team/backend"},
        }

    monkeypatch.setattr("kmap.inventory.repositories.fetch_gitlab_project", fake_fetch_project)

    records = fetch_gitlab_repositories(config, "secret", ["123", "1234"])

    assert len(records) == 1
    assert records[0].path_with_namespace == "team/backend/payments-api"


def test_repository_gitlab_fetch_handles_inaccessible_and_non_object_payloads(monkeypatch, capsys):
    def inaccessible(_url, _token):
        raise HTTPError("https://git.example/api/v4/projects/404", 404, "Not Found", hdrs=None, fp=None)

    monkeypatch.setattr(repository_gitlab, "fetch_gitlab_json_page", inaccessible)
    assert repository_gitlab.fetch_gitlab_project("https://git.example", "missing", "secret") == {}
    assert "repository lookup skipped" in capsys.readouterr().err

    monkeypatch.setattr(repository_gitlab, "fetch_gitlab_json_page", lambda _url, _token: ([], 0))
    assert repository_gitlab.fetch_gitlab_project("https://git.example", "list-payload", "secret") == {}


def test_repository_gitlab_records_and_json_errors_are_normalized():
    record = repository_gitlab.repository_record_from_gitlab_project(
        {
            "id": 456,
            "name": "Worker",
            "path": "worker",
            "path_with_namespace": "team/apps/worker",
            "web_url": "https://git.example/team/apps/worker",
            "archived": True,
        }
    )

    assert record.group_path == "team/apps"
    assert record.url == "https://git.example/team/apps/worker"
    assert record.web_url == "https://git.example/team/apps/worker"
    assert record.archived == "true"
    assert repository_gitlab.group_path_from_repo_path("/team/apps/worker/") == "team/apps"

    with pytest.raises(SystemExit) as exc_info:
        repository_gitlab.load_json_bytes(b"{", source="https://git.example/api")

    assert "Invalid JSON response from https://git.example/api" in str(exc_info.value)
