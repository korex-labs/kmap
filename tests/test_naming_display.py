from kmap.naming.display import (
    clip_text,
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
    humanize_slug,
    is_url,
    short_label,
    should_collapse_container_title_to_app,
    slug_parts,
    view_key_suffix,
)


def test_url_and_text_clipping_helpers_cover_empty_and_truncated_values():
    assert not is_url("")
    assert not is_url("ftp://example.com")
    assert is_url(" https://example.com/path ")
    assert clip_text(None) == ""
    assert clip_text("abcdef", 4) == "a..."
    assert short_label("abc", 4) == "abc"


def test_humanized_system_and_container_display_names():
    assert humanize_slug("") == ""
    assert humanize_slug("api-edge-s3") == "API Edge S3"
    assert display_system_name("Payment Gateway", "Payment Gateway") == "Payment Gateway"
    assert display_system_name("gateway", "") == "Gateway"
    assert display_container_name("") == "Workload"
    assert display_container_name("stage-payment-api") == "Payment API"


def test_dependency_and_endpoint_labels_for_internal_and_external_hosts():
    assert dependency_display_name("prod-api.payments.svc.cluster.local:8080") == "API"
    assert dependency_display_name("prod-api.service.demo.consul") == "API"
    assert dependency_display_name("localhost:8080") == "localhost:8080"
    assert endpoint_label("prod-api.payments.svc.cluster.local:8080") == "prod-api"
    assert endpoint_label("https://api.example.com/path") == "api.example.com"
    assert endpoint_label("not hostish") == "not hostish"


def test_display_titles_strip_environment_product_and_metadata_tokens():
    assert slug_parts("Demo payments_api") == ["demo", "payments", "api"]
    assert display_title_from_discovered_name("", "demo") == ""
    assert display_title_from_discovered_name("prod-demo-payments-dev", "demo") == "Payments"
    assert (
        display_title_from_discovered_name_with_context(
            "prod-demo-card-api-main",
            "demo",
            "cards",
            {"title": "Demo", "domain": "card"},
        )
        == "API"
    )
    assert display_title_from_discovered_name_with_context("prod-demo-prod", "demo") == "Prod Demo Prod"


def test_collapse_decision_qualifiers_descriptions_and_heat_tags():
    assert not should_collapse_container_title_to_app("Redis_DB", "Data")
    assert should_collapse_container_title_to_app("GoLang_App", "Gateway")
    assert container_display_qualifier("") == ""
    assert container_display_qualifier("prod-api-01-cy123") == "prod 01 cy123"
    assert container_display_qualifier("payment-gateway") == "ment-gateway"
    assert container_description({}) == "Kubernetes workload"
    assert container_description({"namespace": "payments", "service_name": "api"}, 2) == (
        "Namespace: payments\\nWorkload: api\\nUsed by: 2"
    )
    assert external_description() == "External dependency"
    assert external_description("prod-api.payments.svc.cluster.local:8080", 3) == (
        "External dependency\\nEndpoint: prod-api\\nUsed by: 3"
    )
    assert view_key_suffix("") == "system"
    assert dependency_heat_tag(0) is None
    assert dependency_heat_tag(2) == "Dependency Heat 1"
    assert dependency_heat_tag(4) == "Dependency Heat 2"
    assert dependency_heat_tag(5) == "Dependency Heat 3"
