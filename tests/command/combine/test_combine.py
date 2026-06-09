import json
from argparse import Namespace

import pytest

from kmap.command import combine as combine_module
from kmap.command.combine import combine_reports
from kmap.command.combine.relations import best_relation_candidate, build_dependency_rows, merge_relation_metadata
from kmap.relations import load_dependency_relations

ALIAS_CONFIG = {
    "service_aliases": {
        "rewrites": [
            {
                "match_regex": r"(^|-)alias-",
                "replace": r"\1",
            }
        ]
    }
}


def test_best_relation_candidate_prefers_internal_service_and_source_origin():
    rows = [
        {"match_type": "external", "source_origin": "Env", "source_var": "A"},
        {"match_type": "Service:same_namespace", "source_origin": "ConfigMap", "source_var": "B"},
        {"match_type": "Service:same_namespace", "source_origin": "VaultEnv", "source_var": "C"},
    ]

    assert best_relation_candidate(rows)["source_var"] == "C"


def test_merge_relation_metadata_deduplicates_database_fields():
    metadata = merge_relation_metadata(
        [
            {
                "metadata": {
                    "database": {
                        "engine": "postgres",
                        "names": ["orders", "orders"],
                        "source_vars": ["DB_NAME"],
                        "sources": ["url"],
                    }
                }
            },
            {
                "metadata": {
                    "database": {
                        "engine": "ignored",
                        "names": ["billing"],
                        "source_vars": ["DB_NAME", "DB_SCHEMA"],
                        "sources": ["url", "env"],
                    }
                }
            },
        ]
    )

    assert metadata == {
        "database": {
            "engine": "postgres",
            "names": ["billing", "orders"],
            "source_vars": ["DB_NAME", "DB_SCHEMA"],
            "sources": ["url", "env"],
        }
    }


def test_load_dependency_relations_accepts_json_and_pipe_files(tmp_path):
    json_path = tmp_path / "deps.json"
    list_path = tmp_path / "dependencies.list"
    json_path.write_text('[{"source_service": "svc-json"}]\n', encoding="utf-8")
    list_path.write_text(
        "# comment\nsvc | VAR | dep | EXTERNAL |  | Env | external | value\nbad line\n",
        encoding="utf-8",
    )

    assert load_dependency_relations(str(json_path)) == [{"source_service": "svc-json"}]
    assert load_dependency_relations(str(list_path)) == [
        {
            "source_service": "svc",
            "source_var": "VAR",
            "dependency_key": "dep",
            "dependency_type": "EXTERNAL",
            "target_service": "",
            "source_origin": "Env",
            "match_type": "external",
            "evidence": "value",
        }
    ]


def test_combine_reports_remains_available_from_command_package():
    assert callable(combine_reports)
    assert combine_module.combine_reports is combine_reports


def test_build_dependency_rows_is_pure_and_groups_internal_external_relations():
    rows = build_dependency_rows(
        [
            {
                "service_id": "c1.payments.svc-a",
                "service_name": "svc-a",
                "namespace": "payments",
                "cluster": "c1",
                "project": "pay",
                "dependency_candidates": [
                    {
                        "var": "API_B_URL",
                        "key": "api-b.payments.svc.cluster.local",
                        "host": "api-b.payments.svc.cluster.local",
                        "source": "Env",
                        "value": "http://api-b.payments.svc.cluster.local",
                    },
                    {
                        "var": "THIRD_PARTY_URL",
                        "key": "third-party.example.com",
                        "host": "third-party.example.com",
                        "source": "ConfigMap",
                        "value": "https://third-party.example.com",
                    },
                ],
            },
            {
                "service_id": "c1.payments.api-b",
                "service_name": "api-b",
                "namespace": "payments",
                "cluster": "c1",
                "project": "pay",
                "entrypoints": [
                    {
                        "type": "Service",
                        "endpoint": "api-b.payments.svc.cluster.local:80",
                        "host": "api-b.payments.svc.cluster.local",
                    }
                ],
                "dependency_candidates": [],
            },
        ]
    )

    assert rows == [
        {
            "source_service": "c1.payments.svc-a",
            "source_var": "THIRD_PARTY_URL",
            "dependency_key": "third-party.example.com",
            "dependency_type": "EXTERNAL",
            "target_service": "",
            "source_origin": "ConfigMap",
            "match_type": "external",
            "evidence": "https://third-party.example.com",
        },
        {
            "source_service": "c1.payments.svc-a",
            "source_var": "API_B_URL",
            "dependency_key": "api-b.payments.svc.cluster.local",
            "dependency_type": "INTERNAL",
            "target_service": "c1.payments.api-b",
            "source_origin": "Env",
            "match_type": "Service:same_namespace",
            "evidence": "http://api-b.payments.svc.cluster.local",
        },
    ]


def test_build_dependency_rows_uses_configured_service_alias_rewrites():
    rows = build_dependency_rows(
        [
            {
                "service_id": "c1.payments.svc-a",
                "service_name": "svc-a",
                "namespace": "payments",
                "cluster": "c1",
                "project": "pay",
                "dependency_candidates": [
                    {
                        "var": "API_B_URL",
                        "key": "prod-alias-api-b.payments.svc.cluster.local",
                        "host": "prod-alias-api-b.payments.svc.cluster.local",
                        "source": "Env",
                        "value": "http://prod-alias-api-b.payments.svc.cluster.local",
                    },
                ],
            },
            {
                "service_id": "c1.payments.api-b",
                "service_name": "prod-api-b",
                "namespace": "payments",
                "cluster": "c1",
                "project": "pay",
                "entrypoints": [],
                "dependency_candidates": [],
            },
        ],
        ALIAS_CONFIG,
    )

    assert rows[0]["dependency_type"] == "INTERNAL"
    assert rows[0]["target_service"] == "c1.payments.api-b"


def test_combine_reports_fails_on_malformed_report_json(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "bad.report.json").write_text("{bad", encoding="utf-8")

    with pytest.raises(SystemExit, match="Invalid JSON file"):
        combine_reports(Namespace(reports_dir=str(reports_dir), output_file=str(tmp_path / "deps.list")))


def test_combine_reports_writes_internal_and_external_dependencies(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "payments.report.json").write_text(
        json.dumps(
            {
                "workloads": [
                    {
                        "service_id": "c1.payments.svc-a",
                        "service_name": "svc-a",
                        "namespace": "payments",
                        "cluster": "c1",
                        "project": "pay",
                        "entrypoints": [],
                        "dependency_candidates": [
                            {
                                "var": "API_B_URL",
                                "key": "api-b.payments.svc.cluster.local",
                                "host": "api-b.payments.svc.cluster.local",
                                "source": "Env",
                                "value": "http://api-b.payments.svc.cluster.local",
                            },
                            {
                                "var": "THIRD_PARTY_URL",
                                "key": "third-party.example.com",
                                "host": "third-party.example.com",
                                "source": "ConfigMap",
                                "value": "https://third-party.example.com",
                                "metadata": {
                                    "database": {
                                        "engine": "mysql",
                                        "names": ["wallet"],
                                        "source_vars": ["MYSQL_DATABASE"],
                                        "sources": ["companion_var"],
                                    }
                                },
                            },
                        ],
                    },
                    {
                        "service_id": "c1.payments.api-b",
                        "service_name": "api-b",
                        "namespace": "payments",
                        "cluster": "c1",
                        "project": "pay",
                        "entrypoints": [
                            {
                                "type": "Service",
                                "endpoint": "api-b.payments.svc.cluster.local:80",
                                "host": "api-b.payments.svc.cluster.local",
                            }
                        ],
                        "dependency_candidates": [],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    output_file = tmp_path / "dependencies.list"
    json_output_file = tmp_path / "dependencies.json"

    rc = combine_reports(
        Namespace(
            reports_dir=str(reports_dir),
            output_file=str(output_file),
            json_output_file=str(json_output_file),
        )
    )

    assert rc == 0
    rows = json.loads(json_output_file.read_text(encoding="utf-8"))
    assert rows == [
        {
            "source_service": "c1.payments.svc-a",
            "source_var": "THIRD_PARTY_URL",
            "dependency_key": "third-party.example.com",
            "dependency_type": "EXTERNAL",
            "target_service": "",
            "source_origin": "ConfigMap",
            "match_type": "external",
            "evidence": "https://third-party.example.com",
            "metadata": {
                "database": {
                    "engine": "mysql",
                    "names": ["wallet"],
                    "source_vars": ["MYSQL_DATABASE"],
                    "sources": ["companion_var"],
                }
            },
        },
        {
            "source_service": "c1.payments.svc-a",
            "source_var": "API_B_URL",
            "dependency_key": "api-b.payments.svc.cluster.local",
            "dependency_type": "INTERNAL",
            "target_service": "c1.payments.api-b",
            "source_origin": "Env",
            "match_type": "Service:same_namespace",
            "evidence": "http://api-b.payments.svc.cluster.local",
        },
    ]
    assert output_file.read_text(encoding="utf-8").splitlines() == [
        "c1.payments.svc-a | THIRD_PARTY_URL | third-party.example.com | EXTERNAL |  | ConfigMap | external | https://third-party.example.com",
        "c1.payments.svc-a | API_B_URL | api-b.payments.svc.cluster.local | INTERNAL | c1.payments.api-b | Env | Service:same_namespace | http://api-b.payments.svc.cluster.local",
    ]
