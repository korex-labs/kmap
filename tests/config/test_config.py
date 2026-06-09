from argparse import Namespace

import pytest

from kmap.cli import apply_config_overrides, build_parser
from kmap.command.validate_config import validate_config
from kmap.config import apply_scalar_config_overrides, attach_empty_config_metadata
from kmap.config.discovery import (
    clean_discovery_target_values,
    namespace_discovery_targets,
    normalize_discovery_config,
    resolve_discovery_target,
)
from kmap.config.metadata import clean_metadata_resources, merge_project_metadata, normalize_project_metadata_item
from kmap.config.options import (
    clean_bool,
    clean_int,
    normalize_dependency_hotspots_config,
    normalize_system_naming_config,
)
from kmap.config.projects import infer_project_from_namespace, normalize_config_metadata, normalize_namespace_config
from kmap.config.validation import validate_config_shape, validate_url_like


def test_infer_project_from_namespace_handles_empty_product_and_numeric_tokens():
    assert infer_project_from_namespace("") == "project"
    assert infer_project_from_namespace("---") == "project"
    assert infer_project_from_namespace("demo-api-prod-1234", "demo") == "demo"
    assert infer_project_from_namespace("pay-api-prod-1234") == "pay-api"
    assert infer_project_from_namespace("1234-pay-api") == "1234"


def test_normalize_namespace_config_list_dedupes_and_applies_explicit_projects():
    namespaces, namespace_projects, project_metadata = normalize_namespace_config(
        {
            "namespace": ["api", "api", "", "worker"],
            "namespace_project": {"worker": "jobs", "new-ns": "new-project", "ignored": ""},
        },
        "demo",
    )

    assert namespaces == ["api", "worker", "new-ns", "ignored"]
    assert namespace_projects == {"worker": "jobs", "new-ns": "new-project"}
    assert project_metadata == {}


def test_normalize_namespace_config_falls_back_for_empty_or_invalid_project_entries():
    namespaces, namespace_projects, project_metadata = normalize_namespace_config(
        {
            "product": "demo",
            "namespaces": {
                "demo-api-prod-1234": {"project": ""},
                "demo-worker-prod": {"project": 123},
                "demo-web-prod": 123,
                "demo-billing-prod": "billing",
                "": {"project": "ignored"},
            },
            "namespace_projects": "ignored",
        },
        "demo",
    )

    assert namespaces == ["demo-api-prod-1234", "demo-worker-prod", "demo-web-prod", "demo-billing-prod"]
    assert namespace_projects == {
        "demo-api-prod-1234": "demo",
        "demo-worker-prod": "demo",
        "demo-billing-prod": "billing",
    }
    assert project_metadata == {}


def test_normalize_namespace_config_mapping_with_project_metadata():
    config = {
        "product": "pay",
        "namespaces": {
            "pay-api-prod-1234": {
                "project": {"title": "Payment API", "element_type": "GoLang_App"},
                "resources": {"repo": "https://git.example/pay-api"},
            }
        },
    }

    namespaces, namespace_projects, project_metadata = normalize_namespace_config(config, "pay")

    assert namespaces == ["pay-api-prod-1234"]
    assert namespace_projects == {"pay-api-prod-1234": "payment-api"}
    assert project_metadata["payment-api"]["title"] == "Payment API"
    assert project_metadata["payment-api"]["repo"] == "https://git.example/pay-api"


def test_config_projects_normalize_product_and_project_metadata():
    product_metadata, project_metadata = normalize_config_metadata(
        {
            "product": "pay",
            "title": "Payments",
            "team": "Platform",
            "tags": "core,pci",
            "resources": {"logs": "https://logs/pay", "repo": "https://git/pay-product"},
            "namespaces": {"pay-api-prod": {"project": {"title": "API"}}},
            "projects": {"payment-api": {"owner_team": "Team API", "resources": {"repo": "https://git/pay-api"}}},
        }
    )

    assert product_metadata == {
        "title": "Payments",
        "owner_team": "Platform",
        "tags": ["core", "pci"],
        "resources": {"logs": "https://logs/pay", "repo": "https://git/pay-product"},
    }
    assert project_metadata["api"]["title"] == "API"
    assert project_metadata["api"]["resources"]["logs"] == "https://logs/pay"
    assert project_metadata["api"]["resources"]["repo"] == "https://git/pay-product"
    assert project_metadata["payment-api"]["owner_team"] == "Team API"
    assert project_metadata["payment-api"]["repo"] == "https://git/pay-api"
    assert project_metadata["payment-api"]["resources"]["logs"] == "https://logs/pay"
    assert project_metadata["payment-api"]["resources"]["repo"] == "https://git/pay-api"


def test_config_metadata_helpers_normalize_and_merge_resources():
    item = normalize_project_metadata_item(
        {
            "title": "Payments",
            "tags": "api, critical",
            "resources": {"Repo URL": "https://git.example/pay"},
        }
    )

    assert item == {
        "title": "Payments",
        "tags": ["api", "critical"],
        "resources": {"Repo_URL": "https://git.example/pay"},
    }

    merged = merge_project_metadata(
        {"tags": ["api"], "resources": {"repo": "https://git.example/old"}},
        {"tags": ["critical", "api"], "resources": {"docs": "https://docs.example/pay"}},
    )

    assert merged == {
        "repo": "https://git.example/old",
        "tags": ["api", "critical"],
        "resources": {
            "repo": "https://git.example/old",
            "docs": "https://docs.example/pay",
        },
    }
    assert clean_metadata_resources({"Bad Key!": " value "}) == {"Bad_Key": "value"}


def test_config_options_normalize_booleans_numbers_and_hotspots():
    default_int = 3
    assert clean_bool("yes", False) is True
    assert clean_bool("off", True) is False
    assert clean_bool("maybe", True) is True
    assert clean_int("0", default_int, minimum=1) == 1
    assert clean_int("bad", default_int, minimum=1) == default_int

    assert normalize_dependency_hotspots_config(
        {
            "dependency_hotspots": {
                "enabled": "no",
                "metric": "unsupported",
                "min_count": "0",
                "max_nodes": "2",
            }
        }
    ) == {
        "enabled": False,
        "metric": "incoming_distinct_source_container_count",
        "min_count": 1,
        "max_hotspots": 2,
    }


def test_config_options_normalize_system_naming_fallback():
    assert normalize_system_naming_config(
        {
            "system_naming": {
                "fallback": {
                    "enabled": "false",
                    "strip_prefix_tokens": "blue,green",
                    "strip_suffix_tokens": ["old"],
                    "collapse_project_wrapped_names": "no",
                    "rewrites": [{"regex": "^api-(.+)$", "replacement": "\\1"}, {"regex": "ignored"}],
                },
                "service_aliases": {
                    "rewrites": [{"regex": r"(^|-)alias-", "replacement": r"\1"}],
                },
            }
        }
    ) == {
        "fallback": {
            "enabled": False,
            "strip_prefix_tokens": [
                "blue",
                "dev",
                "green",
                "main",
                "prod",
                "production",
                "qa",
                "stage",
                "staging",
                "test",
                "uat",
            ],
            "strip_suffix_tokens": [
                "dev",
                "main",
                "old",
                "prod",
                "production",
                "qa",
                "stage",
                "staging",
                "test",
                "uat",
            ],
            "collapse_project_wrapped_names": False,
            "rewrites": [{"match_regex": "^api-(.+)$", "replace": "\\1"}],
        },
        "service_aliases": {
            "rewrites": [{"match_regex": r"(^|-)alias-", "replace": r"\1"}],
        },
    }


def test_validate_config_shape_requires_namespaces():
    errors, warnings = validate_config_shape({"product": "demo"})

    assert "namespaces: required and must not be empty" in errors
    assert "owner_team: recommended" in warnings


def test_validate_config_shape_reports_namespace_entry_errors_and_warnings():
    errors, warnings = validate_config_shape(
        {
            "product": "demo",
            "title": "Demo",
            "env": "prod",
            "owner_team": "Team",
            "namespaces": {
                "": {},
                "api": {
                    "project": {"element_type": "Nope", "tags": 123},
                    "resources": {"": "x", "repo": "https://"},
                    "discovery": {"context": ["bad"], "extra": "value"},
                    "unexpected": True,
                },
                "worker": {"project": 123, "resources": "bad", "discovery": "bad"},
                "bad-entry": 123,
            },
        }
    )

    assert "namespaces: namespace name must not be empty" in errors
    assert "namespaces.api.project.element_type: unknown element type 'Nope'" in errors
    assert "namespaces.api.project.tags: expected list or comma-separated string" in errors
    assert "namespaces.api.resources: resource key must not be empty" in errors
    assert "namespaces.api.resources.repo: invalid URL" in errors
    assert "namespaces.api.discovery.context: expected string" in errors
    assert "namespaces.worker.project: expected mapping or string" in errors
    assert "namespaces.worker.resources: expected mapping" in errors
    assert "namespaces.worker.discovery: expected mapping" in errors
    assert "namespaces.bad-entry: expected mapping, string project name, or empty mapping" in errors
    assert "namespaces.api.discovery.extra: unknown discovery target key" in warnings
    assert "namespaces.api.unexpected: unknown namespace config key" in warnings


def test_validate_config_shape_reports_product_resource_errors():
    errors, _warnings = validate_config_shape(
        {
            "product": "demo",
            "title": "Demo",
            "env": "prod",
            "owner_team": "Team",
            "resources": {"repo": "https://"},
            "namespaces": {"api": {}},
        }
    )

    assert "resources.repo: invalid URL" in errors


def test_validate_config_shape_accepts_string_like_resource_and_discovery_values():
    errors, warnings = validate_config_shape(
        {
            "product": "demo",
            "title": "Demo",
            "env": "prod",
            "owner_team": "Team",
            "resources": {"build": 123},
            "namespaces": {
                "api": {
                    "resources": {"port": 8080},
                    "discovery": {"context": 1, "kubeconfig": 2.0},
                }
            },
            "discovery": {"context": 1, "kubeconfig": 2.0},
        }
    )

    assert errors == []
    assert warnings == []


def test_validate_config_shape_reports_project_mapping_and_external_mapping_errors():
    errors, _ = validate_config_shape(
        {
            "product": "demo",
            "title": "Demo",
            "env": "prod",
            "owner_team": "Team",
            "namespaces": ["api"],
            "projects": {"api": {"element_type": "Nope"}, "worker": "bad"},
            "external_mappings": [
                "bad",
                {
                    "element_type": "Nope",
                    "match": "bad",
                    "match_regex": ["["],
                },
            ],
            "dependency_hotspots": "bad",
            "render": "html",
            "discovery": {"context": [], "extra": "value"},
        }
    )

    assert "projects.api.element_type: unknown element type 'Nope'" in errors
    assert "projects.worker: expected mapping" in errors
    assert "external_mappings[0]: expected mapping" in errors
    assert "external_mappings[1].name: required" in errors
    assert "external_mappings[1].element_type: unknown element type 'Nope'" in errors
    assert "external_mappings[1].match: expected list" in errors
    assert "external_mappings[1].match_regex[0]: invalid regex:" in "\n".join(errors)
    assert "dependency_hotspots: expected mapping" in errors
    assert "render: expected one of structurizr, likec4, both" in errors
    assert "discovery.context: expected string" in errors


def test_validate_config_shape_reports_additional_mapping_shape_errors():
    errors, warnings = validate_config_shape(
        {
            "product": "demo",
            "title": "Demo",
            "env": "prod",
            "devops_team": "Team",
            "namespace": ["api", ""],
            "external_mappings": "bad",
            "discovery": "bad",
        }
    )

    assert "namespaces[1]: expected non-empty namespace name" in errors
    assert "external_mappings: expected list" in errors
    assert "discovery: expected mapping" in errors
    assert warnings == []

    errors, _ = validate_config_shape(
        {
            "product": "demo",
            "title": "Demo",
            "env": "prod",
            "team": "Team",
            "namespaces": {"api": ""},
            "external_mappings": [
                {"name": "Missing match"},
                {"name": "Bad regex list", "match_regex": "not-a-list"},
            ],
        }
    )

    assert "namespaces.api: project name must not be empty" in errors
    assert "external_mappings[0]: at least one of match or match_regex is required" in errors
    assert "external_mappings[1].match_regex: expected list" in errors


def test_validate_config_shape_accepts_container_element_type():
    errors, _ = validate_config_shape(
        {
            "product": "demo",
            "title": "Demo",
            "env": "prod",
            "owner_team": "Team",
            "namespaces": {
                "api": {
                    "project": {"element_type": "container"},
                }
            },
            "projects": {"worker": {"element_type": "container"}},
            "external_mappings": [{"name": "Endpoint", "element_type": "container", "match": ["endpoint.local"]}],
        }
    )

    assert errors == []


def test_config_validation_url_like_values():
    assert validate_url_like("https://example.com")
    assert validate_url_like("repo-name")
    assert not validate_url_like("")
    assert not validate_url_like("https://")


def test_apply_config_overrides_uses_config_namespaces(tmp_path):
    config_file = tmp_path / "product.yaml"
    config_file.write_text(
        """
org: web
product: demo
env: prod
render: both
owner_team: Team
namespaces:
  demo-api-prod-1234: {}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    args = Namespace(
        config=str(config_file),
        org="org",
        product="product",
        project="",
        env="prod",
        render="both",
        data_mode="sanitized",
        mock_seed="",
        namespace=[],
        namespace_project=[],
    )

    out = apply_config_overrides(args)

    assert out.org == "web"
    assert out.product == "demo"
    assert out.namespace == ["demo-api-prod-1234"]
    assert out.render == "both"
    assert out.discovery_config == {"namespaces": {}}


def test_apply_scalar_config_overrides_keeps_explicit_values():
    args = Namespace(
        org="custom-org",
        product="product",
        project="",
        env=None,
    )

    apply_scalar_config_overrides(
        args,
        {
            "org": "configured-org",
            "product": "configured-product",
            "project": "configured-project",
            "env": "stage",
        },
    )

    assert args.org == "custom-org"
    assert args.product == "configured-product"
    assert args.project == "configured-project"
    assert args.env == "stage"


def test_attach_empty_config_metadata_sets_missing_defaults_only():
    args = Namespace(product_metadata={"owner": "Team"})

    out = attach_empty_config_metadata(args)

    assert out.product_metadata == {"owner": "Team"}
    assert out.project_metadata == {}
    assert out.config_namespaces == []
    assert out.config_namespace_projects == {}
    assert out.system_naming_config["fallback"]["enabled"] is True
    assert out.dependency_hotspots_config["enabled"] is True
    assert out.discovery_config == {"namespaces": {}}


def test_apply_config_overrides_reports_missing_or_invalid_config(tmp_path):
    with pytest.raises(SystemExit, match="Config file not found"):
        apply_config_overrides(Namespace(config=str(tmp_path / "missing.yaml")))

    directory = tmp_path / "config-dir"
    directory.mkdir()
    with pytest.raises(SystemExit, match="Config path is not a file"):
        apply_config_overrides(Namespace(config=str(directory)))

    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("- list\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="Invalid config file format"):
        apply_config_overrides(Namespace(config=str(invalid)))


def test_apply_config_overrides_keeps_explicit_cli_values(tmp_path):
    config_file = tmp_path / "product.yaml"
    config_file.write_text(
        """
org: config-org
product: config-product
env: stage
data_mode: mocked
mock_seed: seed
render: likec4
namespaces:
  api: project-api
""".strip()
        + "\n",
        encoding="utf-8",
    )
    args = Namespace(
        config=str(config_file),
        org="cli-org",
        product="cli-product",
        project="cli-project",
        env="cli-env",
        render="structurizr",
        data_mode="cli-mode",
        mock_seed="cli-seed",
        namespace=["cli-ns"],
        namespace_project=["cli-ns=cli-project"],
    )

    out = apply_config_overrides(args)

    assert out.org == "cli-org"
    assert out.product == "cli-product"
    assert out.env == "cli-env"
    assert out.render == "structurizr"
    assert out.data_mode == "cli-mode"
    assert out.mock_seed == "cli-seed"
    assert out.namespace == ["cli-ns"]
    assert out.namespace_project == ["cli-ns=cli-project"]


def test_apply_config_overrides_fills_namespace_projects_from_config(tmp_path):
    config_file = tmp_path / "product.yaml"
    config_file.write_text(
        """
product: demo
namespaces:
  api: payments
  worker: jobs
""".strip()
        + "\n",
        encoding="utf-8",
    )
    args = Namespace(
        config=str(config_file),
        namespace=[],
        namespace_project=[],
    )

    out = apply_config_overrides(args)

    assert out.namespace == ["api", "worker"]
    assert out.namespace_project == ["api=payments", "worker=jobs"]


def test_discovery_config_normalizes_and_resolves_targets():
    config = {
        "discovery": {
            "context": "default-ctx",
            "kubeconfig": "/cfg/default",
        },
        "namespaces": {"api-prod": {"discovery": {"context": "namespace-ctx", "kubeconfig": "/cfg/ns"}}},
    }

    discovery = normalize_discovery_config(config)

    assert resolve_discovery_target(discovery, "api-prod", "api", "/cli/kubeconfig") == {
        "context": "namespace-ctx",
        "kubeconfig": "/cli/kubeconfig",
    }
    assert resolve_discovery_target(discovery, "worker-prod", "worker") == {
        "context": "default-ctx",
        "kubeconfig": "/cfg/default",
    }


def test_discovery_config_ignores_malformed_targets_and_cleans_values():
    assert normalize_discovery_config({"discovery": "bad", "namespace": "bad"}) == {"namespaces": {}}
    assert namespace_discovery_targets(
        {
            "api": {"discovery": {"context": " api-context ", "kubeconfig": ""}},
            "worker": {"discovery": "bad"},
            "": {"discovery": {"context": "ignored"}},
            "jobs": "bad",
        }
    ) == {"api": {"context": "api-context"}}
    assert clean_discovery_target_values({"context": " ctx ", "kubeconfig": None, "extra": ""}) == {"context": "ctx"}


def test_discovery_config_namespace_values_override_defaults_without_cli_override():
    discovery = normalize_discovery_config(
        {
            "discovery": {"context": "default-ctx", "kubeconfig": "/cfg/default"},
            "namespaces": {"api": {"discovery": {"context": "api-ctx"}}},
        }
    )

    assert resolve_discovery_target(discovery, "api", "payments") == {
        "context": "api-ctx",
        "kubeconfig": "/cfg/default",
    }


def test_validate_config_accepts_render_and_namespace_discovery():
    errors, warnings = validate_config_shape(
        {
            "product": "demo",
            "title": "Demo",
            "env": "prod",
            "render": "both",
            "owner_team": "Team",
            "discovery": {"context": "default", "kubeconfig": "/cfg/default"},
            "namespaces": {"api-prod": {"discovery": {"context": "api", "kubeconfig": "/cfg/api"}}},
        }
    )

    assert errors == []
    assert warnings == []


def test_run_all_parser_leaves_kubeconfig_empty_when_not_explicit(monkeypatch):
    monkeypatch.setenv("KUBECONFIG", "/tmp/kubeconfig-from-env")

    args = build_parser().parse_args(["run-all", "--config", "product.yaml"])

    assert args.kubeconfig == ""
    assert args.output == "progress"
    assert not hasattr(args, "context")

    line_args = build_parser().parse_args(["run-all", "--config", "product.yaml", "--output", "lines"])
    assert line_args.output == "lines"


def test_run_all_parser_accepts_explicit_kubeconfig(monkeypatch, tmp_path):
    kubeconfig = tmp_path / ".kube" / "config"
    kubeconfig.parent.mkdir()
    kubeconfig.write_text("apiVersion: v1\n")
    monkeypatch.delenv("KUBECONFIG", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    args = build_parser().parse_args(["run-all", "--config", "product.yaml", "--kubeconfig", str(kubeconfig)])

    assert args.kubeconfig == str(kubeconfig)


def test_parser_reports_invalid_numeric_env_values(monkeypatch):
    monkeypatch.setenv("EXEC_SLEEP", "slow")

    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["run-all", "--config", "product.yaml"])


def test_parser_reports_invalid_numeric_cli_values():
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["inspect", "-n", "demo", "--max-exec-pods-per-workload", "0"])


def test_parser_exposes_render_command():
    args = build_parser().parse_args(
        [
            "render",
            "architecture.json",
            "--render",
            "likec4",
            "--likec4-output-dir",
            "Likec4/demo",
            "--struct-output-dir",
            "Structurizr/demo",
        ]
    )

    assert args.architecture_file == "architecture.json"
    assert args.render == "likec4"
    assert args.likec4_output_dir == "Likec4/demo"
    assert args.struct_output_dir == "Structurizr/demo"


def test_parser_exposes_global_kmap_config_and_recommend_config():
    args = build_parser().parse_args(["--kmap-config", "kmap.local.yaml", "recommend-config", "config/demo.yaml"])

    assert args.kmap_config == "kmap.local.yaml"
    assert args.command == "recommend-config"
    assert args.config_file == "config/demo.yaml"


def test_parser_exposes_validate_likec4_command():
    args = build_parser().parse_args(["validate-likec4", "--root", "Likec4", "--product", "demo"])

    assert args.command == "validate-likec4"
    assert args.root == "Likec4"
    assert args.product == ["demo"]


def test_parser_no_longer_exposes_partial_render_commands():
    parser = build_parser()

    for command in ["likec4", "struct", "struct-model", "struct-views", "struct-arch"]:
        with pytest.raises(SystemExit):
            parser.parse_args([command, "--help"])


def test_validate_config_wrapper_reports_file_not_found(capsys, tmp_path):
    rc = validate_config(Namespace(config_file=str(tmp_path / "missing.yaml")))

    captured = capsys.readouterr()
    assert rc == 1
    assert "config validation failed" in captured.err
    assert "file not found" in captured.err


def test_validate_config_wrapper_reports_errors_and_warnings(capsys, tmp_path):
    config_file = tmp_path / "bad.yaml"
    config_file.write_text("product: demo\n", encoding="utf-8")

    rc = validate_config(Namespace(config_file=str(config_file)))

    captured = capsys.readouterr()
    assert rc == 1
    assert "- title: required" in captured.err
    assert "- owner_team: recommended" in captured.err


def test_validate_config_wrapper_reports_success_with_warnings(capsys, tmp_path):
    config_file = tmp_path / "ok.yaml"
    config_file.write_text(
        """
product: demo
title: Demo
env: prod
namespaces:
  api:
    unexpected: true
""".strip()
        + "\n",
        encoding="utf-8",
    )

    rc = validate_config(Namespace(config_file=str(config_file)))

    captured = capsys.readouterr()
    assert rc == 0
    assert "config ok" in captured.err
    assert "warning: owner_team: recommended" in captured.err
    assert "warning: namespaces.api.unexpected: unknown namespace config key" in captured.err
