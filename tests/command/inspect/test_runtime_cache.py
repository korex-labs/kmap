import json
from argparse import Namespace

from kmap.command.inspect.runtime_cache import (
    cached_runtime_candidate,
    previous_runtime_candidates_by_workload,
    runtime_candidates,
    with_cached_runtime_candidates,
)


def test_previous_runtime_candidates_returns_empty_for_missing_or_invalid_report(tmp_path):
    args = Namespace(namespace="payments")

    assert previous_runtime_candidates_by_workload(args, tmp_path) == {}

    (tmp_path / "payments.report.json").write_text("[]", encoding="utf-8")

    assert previous_runtime_candidates_by_workload(args, tmp_path) == {}


def test_previous_runtime_candidates_loads_only_runtime_candidates(tmp_path):
    args = Namespace(namespace="payments")
    previous_report = {
        "workloads": [
            {
                "cluster": "ctx",
                "namespace": "payments",
                "kind": "Deployment",
                "service_name": "api",
                "dependency_candidates": [
                    {"source": "Env", "source_name": "runtime", "var": "API_URL", "key": "api.example.com"},
                    {"source": "VaultEnv", "source_name": "runtime", "var": "VAULT_URL", "key": "vault.example.com"},
                    {"source": "Env", "source_name": "spec", "var": "SPEC_URL", "key": "spec.example.com"},
                    {"source": "ConfigMap", "source_name": "runtime", "var": "CFG_URL", "key": "cfg.example.com"},
                ],
            },
            "not-a-workload",
        ]
    }
    (tmp_path / "payments.report.json").write_text(json.dumps(previous_report), encoding="utf-8")

    assert previous_runtime_candidates_by_workload(args, tmp_path) == {
        ("ctx", "payments", "Deployment", "api"): [
            {"source": "Env", "source_name": "runtime", "var": "API_URL", "key": "api.example.com"},
            {"source": "VaultEnv", "source_name": "runtime", "var": "VAULT_URL", "key": "vault.example.com"},
        ]
    }


def test_runtime_candidate_helpers_filter_and_copy_cache_metadata():
    source = {"source": "Env", "source_name": "runtime", "var": "API_URL", "key": "api.example.com"}
    ignored = {"source": "ConfigMap", "source_name": "runtime", "var": "CFG_URL", "key": "cfg.example.com"}

    assert runtime_candidates([source, ignored, "bad"]) == [source]

    cached = cached_runtime_candidate(source)

    assert cached == {
        "source": "Env",
        "source_name": "runtime",
        "var": "API_URL",
        "key": "api.example.com",
        "cache": True,
        "cache_source": "previous_report",
    }
    assert source == {"source": "Env", "source_name": "runtime", "var": "API_URL", "key": "api.example.com"}


def test_runtime_candidate_cache_keeps_current_runtime_candidates():
    current = [
        {
            "source": "Env",
            "source_name": "runtime",
            "var": "LIVE_URL",
            "key": "live.example.com",
        }
    ]
    cached = {
        ("ctx", "payments", "Deployment", "api"): [
            {
                "source": "VaultEnv",
                "source_name": "runtime",
                "var": "CACHED_URL",
                "key": "cached.example.com",
            }
        ]
    }

    assert with_cached_runtime_candidates(current, cached, ("ctx", "payments", "Deployment", "api")) is current


def test_runtime_candidate_cache_ignores_different_workload_identity():
    current = [
        {
            "source": "ConfigMap",
            "source_name": "app-config",
            "var": "STATIC_URL",
            "key": "static.example.com",
        }
    ]
    cached = {
        ("ctx", "payments", "Deployment", "other-api"): [
            {
                "source": "Env",
                "source_name": "runtime",
                "var": "API_URL",
                "key": "api.example.com",
            }
        ]
    }

    assert with_cached_runtime_candidates(current, cached, ("ctx", "payments", "Deployment", "api")) is current
