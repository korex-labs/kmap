from kmap.inspection.dependencies.core import (
    BaseDependencyCandidateInput,
    DependencyCandidateInput,
    attach_dependency_database_metadata,
    base_dependency_candidate,
    container_literal_env,
    dedupe_dependency_candidates,
    dependency_alias_key,
    dependency_candidate_dedupe_key,
    dependency_candidate_from_input,
    dependency_candidate_from_raw_part,
    dependency_candidate_key,
    dependency_candidate_sort_key,
    dependency_candidate_source_rank,
    dependency_candidates_from_map,
    dependency_candidates_from_sources,
    dependency_value_parts,
    mark_internal_dependency_candidates,
    mock_database_metadata,
    mock_dependency_candidate_fields,
    mock_dns_label,
    mock_host,
    mock_hostish_value,
    mock_identity_label,
    mock_label,
    parse_dependency_hostish,
    parse_env_block,
    referenced_configmap_values,
    referenced_secret_values,
    referenced_source_name,
    sanitize_dependency_candidate,
    sanitize_dependency_source_name,
    should_consider_dependency_pair,
    workload_dependency_candidates,
    workload_dependency_sources,
)


def test_dependency_candidates_from_map_extracts_hostish_values_and_filters_noise():
    rows = dependency_candidates_from_map(
        {
            "API_URL": "https://api.example.com/path,10.0.0.1:5432",
            "PASSWORD": "https://secret.example.com",
            "MODE": "https://ignored.example.com",
        },
        "Env",
        "spec",
    )

    assert rows == [
        {
            "source": "Env",
            "source_name": "spec",
            "var": "API_URL",
            "key": "api.example.com",
            "value": "https://api.example.com/path,10.0.0.1:5432",
            "host": "api.example.com",
            "port": None,
            "path": "/path",
            "class": "external_candidate",
        }
    ]


def test_dependency_candidates_from_map_adds_database_metadata():
    rows = dependency_candidates_from_map(
        {
            "POSTGRES_DSN": "jdbc:postgresql://pg.example.com:5432/app_db?ssl=true",
            "POSTGRES_DB": "fallback_db",
        },
        "Env",
        "spec",
    )

    assert rows[0]["metadata"] == {
        "database": {
            "engine": "postgresql",
            "names": ["app_db", "fallback_db"],
            "source_vars": ["POSTGRES_DB", "POSTGRES_DSN"],
            "sources": ["dsn_path", "companion_var"],
        }
    }


def test_dependency_candidate_from_raw_part_returns_empty_for_unparseable_values():
    assert dependency_candidate_from_raw_part({}, "API_URL", "not hostish", "not hostish", "Env", "spec") == {}
    assert dependency_candidate_from_raw_part(
        {},
        "API_URL",
        "https://api.example.com",
        "https://api.example.com",
        "Env",
        "spec",
    ) == {
        "source": "Env",
        "source_name": "spec",
        "var": "API_URL",
        "key": "api.example.com",
        "value": "https://api.example.com",
        "host": "api.example.com",
        "port": None,
        "path": None,
        "class": "external_candidate",
    }


def test_dependency_pair_and_value_parsing_helpers_filter_noise_and_jdbc_values():
    assert should_consider_dependency_pair("API_URL", "https://api.example.com") is True
    assert should_consider_dependency_pair("PASSWORD", "https://secret.example.com") is False
    assert should_consider_dependency_pair("API_URL", "") is False
    assert dependency_value_parts(" https://a.example.com, https://b.example.com ,,") == [
        "https://a.example.com",
        "https://b.example.com",
    ]
    assert parse_dependency_hostish("jdbc:postgresql://pg.example.com:5432/app") == (
        "pg.example.com",
        5432,
        "/app",
    )


def test_dependency_candidate_construction_helpers_build_base_and_attach_database_metadata():
    item = base_dependency_candidate(
        BaseDependencyCandidateInput(
            key="POSTGRES_DSN",
            value="jdbc:postgresql://pg.example.com:5432/app_db",
            host="pg.example.com",
            port=5432,
            path="/app_db",
            source="Env",
            source_name="spec",
        )
    )

    assert item == {
        "source": "Env",
        "source_name": "spec",
        "var": "POSTGRES_DSN",
        "key": "pg.example.com:5432",
        "value": "jdbc:postgresql://pg.example.com:5432/app_db",
        "host": "pg.example.com",
        "port": 5432,
        "path": "/app_db",
        "class": "external_candidate",
    }

    attach_dependency_database_metadata(
        item,
        {
            "POSTGRES_DSN": "jdbc:postgresql://pg.example.com:5432/app_db",
            "POSTGRES_DB": "fallback_db",
        },
        "POSTGRES_DSN",
        "jdbc:postgresql://pg.example.com:5432/app_db",
        "pg.example.com",
    )

    assert item["metadata"] == {
        "database": {
            "engine": "postgresql",
            "names": ["app_db", "fallback_db"],
            "source_vars": ["POSTGRES_DB", "POSTGRES_DSN"],
            "sources": ["dsn_path", "companion_var"],
        }
    }


def test_dependency_candidate_context_helpers_preserve_candidate_shape():
    candidate = dependency_candidate_from_input(
        DependencyCandidateInput(
            data={"API_URL": "https://api.example.com/path"},
            key="API_URL",
            value="https://api.example.com/path",
            source="Env",
            source_name="spec",
        ),
        "https://api.example.com/path",
    )
    base = base_dependency_candidate(
        BaseDependencyCandidateInput(
            key="API_URL",
            value="https://api.example.com/path",
            host="api.example.com",
            port=None,
            path="/path",
            source="Env",
            source_name="spec",
        )
    )

    assert candidate == base


def test_dependency_candidate_key_uses_port_when_present():
    assert dependency_candidate_key("api.example.com", None) == "api.example.com"
    assert dependency_candidate_key("api.example.com", 443) == "api.example.com:443"


def test_dedupe_dependency_candidates_prefers_higher_source_rank():
    configmap_candidate = {"source": "ConfigMap", "var": "URL", "key": "api.example.com"}
    vault_candidate = {"source": "VaultEnv", "var": "URL", "key": "api.example.com"}

    assert dependency_candidate_dedupe_key(configmap_candidate) == ("URL", "api.example.com")
    assert dependency_candidate_sort_key(configmap_candidate) == ("URL", "api.example.com")
    assert dependency_candidate_source_rank(vault_candidate) > dependency_candidate_source_rank(configmap_candidate)

    rows = dedupe_dependency_candidates(
        [
            configmap_candidate,
            vault_candidate,
            {"source": "Env", "var": "BROKER", "key": "kafka.example.com"},
        ]
    )

    assert rows == [
        {"source": "Env", "var": "BROKER", "key": "kafka.example.com"},
        {"source": "VaultEnv", "var": "URL", "key": "api.example.com"},
    ]


def test_dependency_candidates_from_sources_preserves_source_order():
    rows = dependency_candidates_from_sources(
        [
            ({"API_URL": "https://api.example.com"}, "ConfigMap", "app-config"),
            ({"RUNTIME_URL": "https://runtime.example.com"}, "Env", "runtime"),
        ]
    )

    assert [(row["source"], row["source_name"], row["var"]) for row in rows] == [
        ("ConfigMap", "app-config", "API_URL"),
        ("Env", "runtime", "RUNTIME_URL"),
    ]


def test_parse_env_block():
    assert parse_env_block("A=one\nBAD\nB = two\n") == {"A": "one", "B": "two"}


def test_dependency_source_value_helpers_collect_referenced_data_in_sorted_order():
    assert referenced_source_name({"b-config", "a-config"}) == "a-config,b-config"
    assert referenced_source_name(set()) == "referenced"
    assert referenced_configmap_values(
        {"b-config", "a-config"},
        {
            "a-config": {"data": {"A": "one"}},
            "b-config": {"data": {"B": 2}},
        },
    ) == {"A": "one", "B": "2"}
    assert referenced_secret_values(
        {"api-secret"},
        {"api-secret": {"data": {"TOKEN": "dmFsdWU="}}},
    ) == {"TOKEN": "value"}
    assert container_literal_env(
        [
            {"env": [{"name": "A", "value": "one"}]},
            {"env": [{"name": "B", "value": "two"}]},
        ]
    ) == {"A": "one", "B": "two"}


def test_workload_dependency_sources_preserve_existing_source_descriptors():
    sources = workload_dependency_sources(
        containers=[{"env": [{"name": "SPEC_URL", "value": "https://spec.example.com"}]}],
        referenced_configmaps={"b-config", "a-config"},
        referenced_secrets={"api-secret"},
        configmaps={
            "a-config": {"data": {"A_URL": "https://a.example.com"}},
            "b-config": {"data": {"B_URL": "https://b.example.com"}},
        },
        secrets={"api-secret": {"data": {"SECRET_URL": "aHR0cHM6Ly9zZWNyZXQuZXhhbXBsZS5jb20="}}},
        runtime_env={"RUNTIME_URL": "https://runtime.example.com"},
        vault_env={"VAULT_URL": "https://vault.example.com"},
    )

    assert sources == [
        (
            {"A_URL": "https://a.example.com", "B_URL": "https://b.example.com"},
            "ConfigMap",
            "a-config,b-config",
        ),
        ({"SECRET_URL": "https://secret.example.com"}, "Secret", "api-secret"),
        ({"SPEC_URL": "https://spec.example.com"}, "Env", "spec"),
        ({"RUNTIME_URL": "https://runtime.example.com"}, "Env", "runtime"),
        ({"VAULT_URL": "https://vault.example.com"}, "VaultEnv", "runtime"),
    ]


def test_internal_dependency_candidate_helpers_mark_alias_matches_in_place():
    external = {"host": "orders", "key": "orders:8080", "class": "external_candidate"}
    fallback = {"key": "billing", "class": "external_candidate"}
    rows = [external, fallback]

    assert dependency_alias_key(external) == "orders"
    assert dependency_alias_key(fallback) == "billing"
    assert (
        mark_internal_dependency_candidates(
            rows,
            {"orders": ["orders-api", "orders-api"], "billing": ["billing-api"]},
        )
        is rows
    )
    assert rows == [
        {
            "host": "orders",
            "key": "orders:8080",
            "class": "internal_namespace_candidate",
            "internal_candidates": ["orders-api"],
        },
        {
            "key": "billing",
            "class": "internal_namespace_candidate",
            "internal_candidates": ["billing-api"],
        },
    ]


def test_workload_dependency_candidates_collects_sources_and_marks_internal_services():
    rows = workload_dependency_candidates(
        containers=[
            {
                "env": [
                    {"name": "SPEC_URL", "value": "https://spec.example.com"},
                    {"name": "FROM_CM", "valueFrom": {"configMapKeyRef": {"name": "app-config"}}},
                ]
            }
        ],
        referenced_configmaps={"app-config"},
        referenced_secrets={"app-secret"},
        configmaps={
            "app-config": {
                "data": {
                    "CM_URL": "https://cm.example.com",
                    "INTERNAL_URL": "http://orders:8080",
                }
            }
        },
        secrets={"app-secret": {"data": {"SECRET_URL": "aHR0cHM6Ly9zZWNyZXQuZXhhbXBsZS5jb20="}}},
        runtime_env={"RUNTIME_URL": "https://runtime.example.com"},
        vault_env={"VAULT_URL": "https://vault.example.com"},
        internal_alias_to_service={"orders": ["orders-api"]},
    )

    by_var = {row["var"]: row for row in rows}
    assert sorted(by_var) == ["CM_URL", "INTERNAL_URL", "RUNTIME_URL", "SECRET_URL", "SPEC_URL", "VAULT_URL"]
    assert by_var["CM_URL"]["source"] == "ConfigMap"
    assert by_var["SECRET_URL"]["source"] == "Secret"
    assert by_var["SPEC_URL"]["source"] == "Env"
    assert by_var["RUNTIME_URL"]["source_name"] == "runtime"
    assert by_var["VAULT_URL"]["source"] == "VaultEnv"
    assert by_var["INTERNAL_URL"]["class"] == "internal_namespace_candidate"
    assert by_var["INTERNAL_URL"]["internal_candidates"] == ["orders-api"]


def test_dependency_sanitization_modes_redact_and_mock_sensitive_fields():
    candidate = {
        "source": "Secret",
        "source_name": "app-secret",
        "var": "PASSWORD_URL",
        "key": "db.example.com:5432",
        "value": "postgresql://db.example.com:5432/app",
        "host": "db.example.com",
        "port": 5432,
        "path": "/app",
        "class": "external_candidate",
        "internal_candidates": ["db-service"],
        "metadata": {"database": {"names": ["app"], "source_vars": ["POSTGRES_DB"]}},
    }

    assert sanitize_dependency_candidate(candidate, "raw") == candidate

    sanitized = sanitize_dependency_candidate(candidate, "sanitized")
    assert sanitized["value"] == "<redacted>"
    assert sanitized["value_redacted"] is True
    assert sanitized["source_name"] == "referenced"
    assert sanitized["var_redacted"] is True
    assert sanitized["host"] == "db.example.com"

    mocked = sanitize_dependency_candidate(candidate, "mocked", "seed")
    assert mocked["source_name"] != "app-secret"
    assert mocked["var"] != "PASSWORD_URL"
    assert mocked["key"] != "db.example.com:5432"
    assert mocked["host"] != "db.example.com"
    assert mocked["path"].startswith("/")
    assert mocked["internal_candidates"] != ["db-service"]
    assert mocked["metadata"]["database"]["names"] != ["app"]


def test_dependency_mock_helpers_are_deterministic_and_shape_preserving():
    assert mock_label("var", "API_URL", "seed") == mock_label("var", "API_URL", "seed")
    assert mock_dns_label("svc", "very-long-service-name", "seed").startswith("svc-")
    assert mock_identity_label("orders", "seed").startswith("id-")
    assert mock_host("orders.svc.cluster.local", "seed").endswith(".cluster.local")
    assert mock_host("orders", "seed").startswith("id-")
    assert mock_hostish_value("orders:8080", "seed").endswith(":8080")
    assert mock_database_metadata({"names": ["app"], "source_vars": ["APP_DB"]}, "seed") != {
        "names": ["app"],
        "source_vars": ["APP_DB"],
    }

    candidate = {"source": "ConfigMap", "source_name": "app-config"}
    sanitize_dependency_source_name(candidate, "mocked", "seed")
    assert candidate["source_name"] != "app-config"

    out = {"key": "orders", "host": "orders"}
    mock_dependency_candidate_fields(out, "seed")
    assert out["key"] == out["host"]
