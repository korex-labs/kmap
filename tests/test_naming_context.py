from kmap.naming.context import (
    NamingContext,
    container_subsystem_name,
    naming_context_from_args,
    should_model_workload,
)


def test_naming_context_builds_stable_base_and_container_names():
    naming = NamingContext(org="Acme Org", product="Payment", project="Gateway", env="prod")

    assert naming.base() == "Acme-Org-Payment-Gateway"
    assert naming.software_system_name() == "Acme-Org-Payment-Gateway"
    assert naming.container_name("API worker") == "Acme-Org-Payment-Gateway-API-worker-prod"


def test_naming_context_from_args_uses_environment_defaults(monkeypatch):
    args = type("Args", (), {"org": "", "product": "", "project": "", "env": ""})()
    monkeypatch.setenv("KMAP_ORG", "acme")
    monkeypatch.setenv("KMAP_PRODUCT", "payments")
    monkeypatch.setenv("KMAP_PROJECT", "gateway")
    monkeypatch.setenv("KMAP_ENV", "stage")

    assert naming_context_from_args(args) == NamingContext(
        org="acme",
        product="payments",
        project="gateway",
        env="stage",
    )


def test_naming_context_from_args_prefers_explicit_values(monkeypatch):
    args = type("Args", (), {"org": "arg-org", "product": "arg-product", "project": "arg-project", "env": "arg-env"})()
    monkeypatch.setenv("KMAP_ORG", "env-org")
    monkeypatch.setenv("KMAP_PRODUCT", "env-product")
    monkeypatch.setenv("KMAP_PROJECT", "env-project")
    monkeypatch.setenv("KMAP_ENV", "env-env")

    assert naming_context_from_args(args) == NamingContext(
        org="arg-org",
        product="arg-product",
        project="arg-project",
        env="arg-env",
    )


def test_container_subsystem_name_includes_available_scope_parts():
    assert container_subsystem_name({}) == "workload"
    assert (
        container_subsystem_name(
            {
                "service_name": "api",
                "namespace": "payments",
                "cluster": "prod",
            }
        )
        == "api-payments-prod"
    )


def test_should_model_workload_filters_operator_only_services():
    assert not should_model_workload(
        {
            "service_name": "cert-operator",
            "selector": {},
            "entrypoints": [],
            "dependency_candidates": [],
        }
    )
    assert not should_model_workload(
        {
            "service_name": "service",
            "selector": {"app": "controller-manager"},
            "entrypoints": [],
            "dependency_candidates": [],
        }
    )
    assert should_model_workload(
        {
            "service_name": "cert-operator",
            "selector": {},
            "entrypoints": [{"port": 443}],
            "dependency_candidates": [],
        }
    )
    assert should_model_workload(
        {
            "service_name": "plain-service",
            "selector": {},
            "entrypoints": [],
            "dependency_candidates": [],
        }
    )
