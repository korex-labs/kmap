import re

from kmap.naming import (
    alias_variants,
    architecture_id,
    canonical_fallback_system_name,
    container_description,
    container_display_qualifier,
    dependency_display_name,
    dependency_heat_tag,
    display_container_name,
    display_system_name,
    display_title_from_discovered_name,
    display_title_from_discovered_name_with_context,
    endpoint_label,
    external_description,
    generated_system_category,
    humanize_slug,
    ident,
    is_url,
    matches_release_name,
    namespace_alias_variants,
    naming_context_from_args,
    normalize_release_name,
    normalized_likec4_internal_system_type,
    q,
    service_name_alias_variants,
    service_reference_variants,
    short_hash,
    short_label,
    short_service_name_variants,
    should_collapse_container_title_to_app,
    should_model_workload,
    slug_name,
    slug_parts,
    view_key_suffix,
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


def test_service_reference_variants_expand_project_and_configured_aliases():
    assert "prod-consent-api.pay-main.svc.cluster.local:8080" in service_reference_variants(
        "prod-alias-consent-api.main.svc.cluster.local:8080",
        "pay",
        SERVICE_ALIAS_CONFIG,
    )
    assert "prod-alias-consent-api.main.svc.cluster.local:8080" in service_reference_variants(
        "prod-alias-consent-api.main.svc.cluster.local:8080",
        "pay",
        SERVICE_ALIAS_CONFIG,
    )


def test_namespace_alias_variants_strip_environment_tokens_and_project_prefix():
    assert namespace_alias_variants("pay-prod-main", "pay") == [
        "main",
        "pay-main",
        "pay-prod-main",
        "prod-main",
    ]


def test_basic_alias_and_release_helpers():
    assert alias_variants("api", "payments", "10.0.0.1") == [
        "10.0.0.1",
        "api",
        "api.payments",
        "api.payments.svc",
        "api.payments.svc.cluster.local",
    ]
    assert service_name_alias_variants("prod-alias-orders") == ["prod-alias-orders"]
    assert service_name_alias_variants("prod-alias-orders", SERVICE_ALIAS_CONFIG) == [
        "prod-alias-orders",
        "prod-orders",
    ]
    assert short_service_name_variants("prod-orders") == ["orders", "prod-orders"]
    assert normalize_release_name("hello world/api") == "hello-world-api"
    assert matches_release_name("release-main", re.compile(r"main"))


def test_display_and_identifier_helpers():
    assert ident("123/api-name") == "_123_api_name"
    assert q('a "quoted" value') == 'a \\"quoted\\" value'
    assert is_url("https://example.com/path")
    assert short_hash("abc", 6) == "a9993e"
    assert short_label("abcdef", 4) == "a..."
    assert humanize_slug("api-edge-s3") == "API Edge S3"
    assert display_system_name("payments", "Demo") == "Demo / Payments"
    assert display_container_name("prod-payment-api") == "Payment API"
    assert endpoint_label("api.payments.svc.cluster.local:80") == "api"


def test_slug_and_architecture_id_are_stable():
    assert slug_name("Payment Gateway GO") == "Payment-Gateway-GO"
    assert architecture_id("sys", "Demo", "Payment Gateway") == "sys.demo.payment_gateway"


def test_display_title_removes_product_noise():
    assert display_title_from_discovered_name("prod-demo-payment-gateway-go", "demo") == "Payment Gateway GO"
    assert dependency_display_name("api.payments.svc.cluster.local") == "API"


def test_fallback_system_and_type_helpers():
    name, source = canonical_fallback_system_name(
        "prod-demo-payments-main",
        "demo",
        "payments",
        {"fallback": {"enabled": True}},
    )

    assert name == "payments"
    assert source["normalization_rules"] == [
        "strip_env_prefix",
        "strip_env_suffix",
        "strip_product_prefix",
    ]
    assert slug_parts("Demo payments_api") == ["demo", "payments", "api"]
    assert (
        display_title_from_discovered_name_with_context(
            "prod-demo-payments-api-main",
            "demo",
            "payments",
            {"title": "Demo"},
        )
        == "Payments API"
    )
    assert generated_system_category("payment gateway") == "Gateway"
    assert normalized_likec4_internal_system_type("orders postgres") == "PgSQL_DB"
    assert not should_collapse_container_title_to_app("Kafka", "Data")


def test_descriptions_context_and_workload_filter(monkeypatch):
    args = type("Args", (), {"org": "", "product": "Demo", "project": "pay", "env": "prod"})()
    monkeypatch.setenv("KMAP_ORG", "acme")
    naming = naming_context_from_args(args)

    assert naming.base() == "acme-Demo-pay"
    assert naming.container_name("api") == "acme-Demo-pay-api-prod"
    assert container_display_qualifier("prod-api-01") == "prod 01"
    assert container_description({"namespace": "payments", "service_name": "api"}, 3) == (
        "Namespace: payments\\nWorkload: api\\nUsed by: 3"
    )
    assert external_description("api.example.com", 2) == "External dependency\\nEndpoint: api.example.com\\nUsed by: 2"
    assert view_key_suffix("payments-api") == "payments_api"
    assert dependency_heat_tag(0) is None
    assert dependency_heat_tag(3) == "Dependency Heat 2"
    assert not should_model_workload(
        {"service_name": "cert-operator", "selector": {}, "entrypoints": [], "dependency_candidates": []}
    )
    assert should_model_workload(
        {"service_name": "cert-operator", "entrypoints": [{"port": 443}], "dependency_candidates": []}
    )
