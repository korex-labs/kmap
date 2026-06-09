from argparse import Namespace

import pytest

from kmap import tool_config
from kmap.tool_config import (
    apply_tool_config_overrides,
    load_tool_config,
    recommendation_resource_policy,
    resolve_view_config_value,
    validate_tool_config,
)


def test_load_tool_config_allows_missing_default(monkeypatch, tmp_path):
    monkeypatch.setattr(tool_config, "DEFAULT_KMAP_CONFIG_FILE", tmp_path / "missing.yaml")
    monkeypatch.delenv("KMAP_CONFIG", raising=False)

    assert load_tool_config(None) == {}


def test_load_tool_config_rejects_missing_explicit_path(tmp_path):
    with pytest.raises(SystemExit, match="kmap config file not found"):
        load_tool_config(str(tmp_path / "missing.yaml"))


def test_validate_tool_config_rejects_unknown_keys():
    assert validate_tool_config(
        {
            "unknown": {},
            "view": {"extra": "x"},
            "recommendations": {"unknown": True},
            "inventory": {"unknown": True},
        }
    ) == [
        "unknown: unknown kmap config key",
        "inventory.unknown: unknown inventory config key",
        "recommendations.unknown: unknown recommendations config key",
        "view.extra: unknown view config key",
    ]


def test_validate_tool_config_rejects_invalid_view_shapes():
    assert validate_tool_config({"view": "bad"}) == ["view: expected mapping"]
    assert validate_tool_config({"view": {"likec4_image": []}}) == ["view.likec4_image: expected string"]


def test_validate_tool_config_allows_numeric_view_values():
    assert validate_tool_config({"view": {"likec4_image": 123, "structurizr_args": 1.5}}) == []


def test_validate_tool_config_rejects_invalid_recommendation_resource_shapes():
    assert validate_tool_config({"recommendations": "bad"}) == ["recommendations: expected mapping"]
    assert validate_tool_config({"recommendations": {"resources": "bad"}}) == [
        "recommendations.resources: expected mapping"
    ]


def test_validate_tool_config_rejects_invalid_inventory_heuristic_shapes():
    assert validate_tool_config({"inventory": "bad"}) == ["inventory: expected mapping"]
    assert validate_tool_config({"inventory": {"namespace_heuristics": "bad"}}) == [
        "inventory.namespace_heuristics: expected mapping"
    ]
    assert validate_tool_config(
        {
            "inventory": {
                "namespace_heuristics": {
                    "unknown": True,
                    "stage_tokens": "prod",
                    "strip_project_id_suffix": "yes",
                    "project_id_suffix": {"extra": True, "enabled": "yes", "pattern": [], "repository_format": []},
                }
            }
        }
    ) == [
        "inventory.namespace_heuristics.unknown: unknown namespace heuristics config key",
        "inventory.namespace_heuristics.project_id_suffix.extra: unknown project id suffix config key",
        "inventory.namespace_heuristics.project_id_suffix.enabled: expected boolean",
        "inventory.namespace_heuristics.project_id_suffix.pattern: expected string",
        "inventory.namespace_heuristics.project_id_suffix.repository_format: expected string",
        "inventory.namespace_heuristics.stage_tokens: expected list of strings",
        "inventory.namespace_heuristics.strip_project_id_suffix: expected boolean",
    ]
    assert validate_tool_config({"recommendations": {"resources": {"extra": [], "required": "repo"}}}) == [
        "recommendations.resources.extra: unknown resources recommendation key",
        "recommendations.resources.required: expected list of strings",
    ]


def test_validate_tool_config_rejects_invalid_storage_type_label_shapes():
    assert validate_tool_config({"inventory": {"storage_type_labels": "bad"}}) == [
        "inventory.storage_type_labels: expected list of mappings"
    ]
    assert validate_tool_config(
        {"inventory": {"storage_type_labels": [{"unknown": "x", "match": "ceph"}, "bad", {"label": "Ceph"}]}}
    ) == [
        "inventory.storage_type_labels[0].unknown: unknown storage type label key",
        "inventory.storage_type_labels[0].label: expected string",
        "inventory.storage_type_labels[1]: expected mapping",
        "inventory.storage_type_labels[2].match: expected string",
    ]
    assert validate_tool_config({"inventory": {"storage_type_labels": [{"match": "[", "label": "Ceph"}]}}) == [
        "inventory.storage_type_labels[0].match: invalid regex: unterminated character set at position 0"
    ]


def test_validate_tool_config_accepts_optional_repository_catalog():
    assert (
        validate_tool_config(
            {
                "inventory": {
                    "repositories": {
                        "enabled": True,
                        "provider": "gitlab",
                        "base_url": "https://git.example",
                        "token_env": "TEAM_GITLAB_TOKEN",
                        "cache_file": "artifacts/repositories/gitlab.json",
                    }
                }
            }
        )
        == []
    )


def test_validate_tool_config_rejects_invalid_repository_catalog_shapes():
    assert validate_tool_config(
        {
            "inventory": {
                "repositories": {
                    "enabled": "yes",
                    "surprise": True,
                }
            }
        }
    ) == [
        "inventory.repositories.surprise: unknown repositories config key",
        "inventory.repositories.enabled: expected boolean",
    ]


def test_recommendation_resource_policy_uses_config_or_defaults():
    assert recommendation_resource_policy({}) == {
        "optional": ["tasks", "logs", "monitoring", "chat"],
        "required": ["repo"],
    }
    assert recommendation_resource_policy(
        {"recommendations": {"resources": {"required": ["repo", "tasks"], "optional": ["chat"]}}}
    ) == {
        "optional": ["chat"],
        "required": ["repo", "tasks"],
    }


def test_apply_tool_config_leaves_non_view_commands_alone(monkeypatch, tmp_path):
    monkeypatch.setattr(tool_config, "DEFAULT_KMAP_CONFIG_FILE", tmp_path / "missing.yaml")
    args = Namespace(command="validate-config", kmap_config=None)

    apply_tool_config_overrides(args)

    assert args.kmap_tool_config == {}
    assert not hasattr(args, "likec4_image")


def test_apply_view_tool_config_uses_config_defaults(monkeypatch, tmp_path):
    config = tmp_path / "kmap.yaml"
    config.write_text(
        """
view:
  likec4_image: likec4/custom
  structurizr_image: structurizr/custom
  structurizr_args: lite
""",
        encoding="utf-8",
    )
    monkeypatch.delenv("KMAP_VIEW_LIKEC4_IMAGE", raising=False)
    args = Namespace(
        command="view",
        kmap_config=str(config),
        likec4_image=None,
        structurizr_image=None,
        structurizr_args=None,
    )

    apply_tool_config_overrides(args)

    assert args.likec4_image == "likec4/custom"
    assert args.structurizr_image == "structurizr/custom"
    assert args.structurizr_args == "lite"


def test_apply_view_tool_config_precedence_cli_env_config_default(monkeypatch, tmp_path):
    config = tmp_path / "kmap.yaml"
    config.write_text(
        """
view:
  likec4_image: likec4/config
  structurizr_image: structurizr/config
  structurizr_args: config-args
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("KMAP_VIEW_STRUCTURIZR_IMAGE", "structurizr/env")
    args = Namespace(
        command="view",
        kmap_config=str(config),
        likec4_image="likec4/cli",
        structurizr_image=None,
        structurizr_args=None,
    )

    apply_tool_config_overrides(args)

    assert args.likec4_image == "likec4/cli"
    assert args.structurizr_image == "structurizr/env"
    assert args.structurizr_args == "config-args"


def test_resolve_view_config_value_uses_cli_env_config_default_precedence(monkeypatch):
    monkeypatch.setenv("KMAP_VIEW_LIKEC4_IMAGE", "likec4/env")

    assert resolve_view_config_value("likec4_image", "likec4/cli", {"likec4_image": "likec4/config"}) == "likec4/cli"
    assert resolve_view_config_value("likec4_image", "", {"likec4_image": "likec4/config"}) == "likec4/env"

    monkeypatch.delenv("KMAP_VIEW_LIKEC4_IMAGE")

    assert resolve_view_config_value("likec4_image", None, {"likec4_image": "likec4/config"}) == "likec4/config"
    assert resolve_view_config_value("likec4_image", None, {}) == "likec4/likec4"


def test_apply_view_tool_config_uses_builtin_defaults(monkeypatch, tmp_path):
    monkeypatch.setattr(tool_config, "DEFAULT_KMAP_CONFIG_FILE", tmp_path / "missing.yaml")
    monkeypatch.delenv("KMAP_CONFIG", raising=False)
    for env_var in tool_config.VIEW_ENV_VARS.values():
        monkeypatch.delenv(env_var, raising=False)
    args = Namespace(
        command="view",
        kmap_config=None,
        likec4_image=None,
        structurizr_image=None,
        structurizr_args=None,
    )

    apply_tool_config_overrides(args)

    assert args.likec4_image == "likec4/likec4"
    assert args.structurizr_image == "structurizr/structurizr"
    assert args.structurizr_args == "local"


def test_load_tool_config_uses_env_as_explicit_path(monkeypatch, tmp_path):
    monkeypatch.setenv("KMAP_CONFIG", str(tmp_path / "missing.yaml"))

    with pytest.raises(SystemExit, match="kmap config file not found"):
        load_tool_config(None)


def test_load_tool_config_rejects_non_mapping(tmp_path):
    config = tmp_path / "kmap.yaml"
    config.write_text("- nope\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="Invalid YAML file format"):
        load_tool_config(str(config))
