from kmap.naming.aliases import (
    alias_variants,
    namespace_alias_variants,
    service_name_alias_variants,
    service_reference_variants,
    short_service_name_variants,
)

SERVICE_ALIAS_CONFIG = {
    "service_aliases": {
        "rewrites": [
            {
                "match_regex": r"(^|-)alias-",
                "replace": r"\1",
            }
        ]
    }
}


def test_alias_variants_ignore_empty_cluster_ip():
    assert alias_variants("API", "Payments", "") == [
        "api",
        "api.payments",
        "api.payments.svc",
        "api.payments.svc.cluster.local",
    ]


def test_service_name_alias_variants_handles_empty_and_hostish_values():
    assert service_name_alias_variants("") == []
    assert service_name_alias_variants("https://prod-edge-orders.example.com:8443/path") == [
        "https://prod-edge-orders.example.com:8443/path",
    ]
    assert service_name_alias_variants(" PROD-ALIAS-ORDERS ") == ["prod-alias-orders"]


def test_service_name_alias_variants_applies_configured_rewrites():
    assert service_name_alias_variants("https://prod-alias-orders.example.com:8443/path", SERVICE_ALIAS_CONFIG) == [
        "https://prod-alias-orders.example.com:8443/path",
        "prod-orders.example.com:8443",
    ]
    assert service_name_alias_variants(" PROD-ALIAS-ORDERS ", SERVICE_ALIAS_CONFIG) == [
        "prod-alias-orders",
        "prod-orders",
    ]


def test_namespace_alias_variants_handles_empty_and_projectless_namespaces():
    assert namespace_alias_variants("") == []
    assert namespace_alias_variants("prod-pay-main") == ["pay-main", "prod-pay-main"]


def test_namespace_alias_variants_keeps_project_prefix_options():
    assert namespace_alias_variants("demo-stage-api", "demo") == [
        "api",
        "demo-api",
        "demo-stage-api",
        "stage-api",
    ]


def test_service_reference_variants_keeps_short_hosts_and_expands_namespaced_hosts():
    assert service_reference_variants("prod-alias-api") == ["prod-alias-api"]

    assert service_reference_variants("prod-alias-api.demo-prod.svc.cluster.local", "demo", SERVICE_ALIAS_CONFIG) == [
        "prod-alias-api.demo-demo.svc.cluster.local",
        "prod-alias-api.demo-prod.svc.cluster.local",
        "prod-alias-api.demo.svc.cluster.local",
        "prod-alias-api.prod.svc.cluster.local",
        "prod-api.demo-demo.svc.cluster.local",
        "prod-api.demo-prod.svc.cluster.local",
        "prod-api.demo.svc.cluster.local",
        "prod-api.prod.svc.cluster.local",
    ]


def test_short_service_name_variants_handles_empty_and_non_environment_prefixes():
    assert short_service_name_variants("") == []
    assert short_service_name_variants("main-orders") == ["main-orders"]
    assert short_service_name_variants(" QA-Orders ") == ["orders", "qa-orders"]
