from kmap.command.inspect.observability import (
    matched_services,
    otel_observability_signals,
    workload_observability_context,
)


def test_workload_observability_context_collects_prometheus_annotations_from_workload_and_services():
    workload = {
        "metadata": {"annotations": {"prometheus.io/scrape": "true"}},
        "spec": {"template": {"metadata": {"annotations": {"prometheus.io/path": "/metrics"}}}},
    }
    services = [
        {
            "metadata": {
                "name": "api",
                "annotations": {
                    "prometheus.io/port": "9090",
                    "prometheus.io/scheme": "http",
                },
            }
        },
        {"metadata": {"name": "other", "annotations": {"prometheus.io/port": "9999"}}},
    ]

    context = workload_observability_context(
        workload=workload,
        services=services,
        matched_service_names=["api"],
        containers=[],
        runtime_env={},
        vault_env={},
    )

    assert context == {
        "prometheus_scrapes": ["true"],
        "prometheus_paths": ["/metrics"],
        "prometheus_ports": ["9090"],
        "prometheus_schemes": ["http"],
        "prometheus_sources": ["pod_template", "service:api", "workload"],
    }


def test_matched_services_filters_by_name_without_reordering():
    services = [
        {"metadata": {"name": "first"}},
        {"metadata": {"name": ""}},
        {"metadata": {"name": "second"}},
        {"metadata": {"name": "third"}},
    ]

    assert [service["metadata"]["name"] for service in matched_services(services, ["third", "first"])] == [
        "first",
        "third",
    ]


def test_workload_observability_context_collects_otel_env_from_spec_runtime_and_vault():
    context = workload_observability_context(
        workload={},
        services=[],
        matched_service_names=[],
        containers=[
            {
                "env": [
                    {"name": "OTEL_SERVICE_NAME", "value": "pay-api"},
                    {"name": "IGNORED", "value": "value"},
                ]
            }
        ],
        runtime_env={
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://otel-collector:4317",
            "OTEL_RESOURCE_ATTRIBUTES": "deployment.environment=prod",
        },
        vault_env={"OTEL_EXPORTER_OTLP_TRACES_ENDPOINT": "http://traces:4317"},
    )

    assert context == {
        "otel_service_names": ["pay-api"],
        "otel_exporter_otlp_endpoints": ["http://otel-collector:4317", "http://traces:4317"],
        "otel_env_vars": [
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
            "OTEL_RESOURCE_ATTRIBUTES",
            "OTEL_SERVICE_NAME",
        ],
    }


def test_otel_observability_signals_deduplicates_and_sorts_env_sources_in_context():
    signals = otel_observability_signals(
        [{"env": [{"name": "OTEL_SERVICE_NAME", "value": "pay-api"}]}],
        {
            "OTEL_SERVICE_NAME": "pay-api",
            "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT": "http://metrics:4317",
            "IGNORED": "value",
        },
        {"OTEL_EXPORTER_OTLP_METRICS_ENDPOINT": "http://metrics:4317"},
    )

    assert signals == {
        "otel_service_names": ["pay-api"],
        "otel_exporter_otlp_endpoints": ["http://metrics:4317"],
        "otel_env_vars": ["OTEL_SERVICE_NAME", "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT"],
    }


def test_workload_observability_context_returns_empty_context_without_signals():
    assert (
        workload_observability_context(
            workload={},
            services=[],
            matched_service_names=[],
            containers=[],
            runtime_env={},
            vault_env={},
        )
        == {}
    )
