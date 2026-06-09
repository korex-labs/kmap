from kmap.inspection.dependency_sanitization import sanitize_dependency_candidate
from kmap.inspection.sanitization import (
    mock_entrypoint,
    mock_selector,
    mock_traffic_route,
    mocked_report_identity_fields,
    mocked_workload_identity_fields,
    mocked_workload_runtime_reference_fields,
    raw_report_for_persistence,
    sanitize_name_list,
    sanitize_report_for_persistence,
    sanitized_report_for_persistence,
    sensitive_workload_fields,
    workload_copy_for_persistence,
)


def test_sanitize_dependency_candidate_hides_raw_value():
    dep = {
        "source": "Env",
        "source_name": "runtime",
        "var": "API_URL",
        "value": "https://api.example.com",
        "host": "api.example.com",
    }

    sanitized = sanitize_dependency_candidate(dep, "sanitized")

    assert sanitized["value"] == "<redacted>"
    assert sanitized["host"] == "api.example.com"


def test_sanitize_name_list_handles_raw_sanitized_and_mocked_modes():
    assert sanitize_name_list(["api", "", None, "worker"], "service", "raw") == ["api", "None", "worker"]
    assert sanitize_name_list(["api", "worker"], "service", "sanitized") == [
        "redacted-service-1",
        "redacted-service-2",
    ]

    mocked = sanitize_name_list(["api", "worker"], "service", "mocked", "seed")
    assert mocked[0].startswith("mock-service-")
    assert mocked != ["api", "worker"]


def test_mock_selector_entrypoint_and_traffic_route_hide_identifiers():
    selector = mock_selector({"app": "payments"}, "seed")
    assert selector
    assert "app" not in selector
    assert "payments" not in selector.values()

    with_host_and_port = mock_entrypoint(
        {"type": "Service", "name": "payments-api", "host": "payments.default.svc", "port": 8080},
        "seed",
    )
    assert with_host_and_port["name"].startswith("mock-service-")
    assert with_host_and_port["host"].endswith(".svc")
    assert with_host_and_port["host"] != "payments.default.svc"
    assert with_host_and_port["endpoint"] == f"{with_host_and_port['host']}:8080"

    with_host_only = mock_entrypoint({"host": "api.example.com"}, "seed")
    assert with_host_only["endpoint"] == with_host_only["host"]

    with_endpoint_only = mock_entrypoint({"endpoint": "db.example.com:5432"}, "seed")
    assert with_endpoint_only["endpoint"] != "db.example.com:5432"
    assert with_endpoint_only["endpoint"].endswith(":5432")

    route = mock_traffic_route(
        {
            "source": {"type": "External", "name": "api.example.com"},
            "hops": [
                {"type": "Ingress", "name": "web", "host": "api.example.com"},
                {"type": "Service", "name": "payments"},
            ],
            "target": {"type": "Container", "names": ["app"]},
        },
        "seed",
    )
    assert route["source"]["name"] != "api.example.com"
    assert route["hops"][0]["name"].startswith("mock-ingress-")
    assert route["hops"][0]["host"] != "api.example.com"
    assert route["hops"][1]["name"].startswith("mock-service-")
    assert route["target"]["names"][0].startswith("mock-container-")

    internal_source = mock_traffic_route({"source": {"name": "cluster-client"}}, "seed")
    assert internal_source["source"]["name"].startswith("mock-source-")


def test_sanitize_report_for_persistence_sanitized_and_mocked_modes():
    report = {
        "cluster": "ctx",
        "namespace": "payments",
        "helm_releases": ["pay-api"],
        "workloads": [
            {
                "service_id": "ctx:payments:Deployment:pay-api",
                "cluster": "ctx",
                "namespace": "payments",
                "project": "pay",
                "kind": "Deployment",
                "service_name": "pay-api",
                "containers": [{"name": "app", "image": "example/pay:1"}],
                "referenced_configmaps": ["cfg"],
                "referenced_secrets": ["sec"],
                "dependency_candidates": [
                    {
                        "source": "Secret",
                        "source_name": "sec",
                        "var": "PASSWORD_URL",
                        "key": "api.example.com",
                        "value": "https://api.example.com",
                        "metadata": {"database": {"engine": "mysql", "names": ["payments"], "source_vars": ["DB"]}},
                    }
                ],
            }
        ],
    }

    sanitized = sanitize_report_for_persistence(report, "sanitized")
    dep = sanitized["workloads"][0]["dependency_candidates"][0]
    assert sanitized["workloads"][0]["referenced_configmaps"] == ["cfg"]
    assert sanitized["workloads"][0]["referenced_secrets"] == ["redacted-secret-1"]
    assert dep["source_name"] == "referenced"
    assert dep["value"] == "<redacted>"
    assert dep["var_redacted"] is True
    assert dep["metadata"]["database"]["names"] == ["payments"]

    mocked = sanitize_report_for_persistence(report, "mocked", "seed")
    mocked_dep = mocked["workloads"][0]["dependency_candidates"][0]
    assert mocked_dep["metadata"]["database"]["names"][0].startswith("mock-database-")
    mocked_names = sanitize_name_list(["api", "worker"], "service", "mocked", "seed")
    assert mocked_names[0].startswith("mock-service-")
    assert mocked_names != ["api", "worker"]


def test_sanitize_report_for_persistence_raw_returns_original_report():
    report = {"cluster": "ctx", "namespace": "payments", "workloads": []}

    assert raw_report_for_persistence(report) is report
    assert sanitize_report_for_persistence(report, "raw") is report


def test_sanitized_report_for_persistence_builds_non_raw_copy():
    report = {
        "cluster": "ctx",
        "namespace": "payments",
        "discovery": {"context": "ctx"},
        "helm_releases": ["pay-api"],
        "workloads": [{"referenced_configmaps": ["cfg"], "referenced_secrets": ["sec"]}],
    }

    sanitized = sanitized_report_for_persistence(report, "sanitized")

    assert sanitized is not report
    assert sanitized["cluster"] == "ctx"
    assert sanitized["namespace"] == "payments"
    assert sanitized["discovery"] == {"context": "ctx"}
    assert sanitized["helm_releases"] == ["pay-api"]
    assert sanitized["workloads"][0]["referenced_configmaps"] == ["cfg"]
    assert sanitized["workloads"][0]["referenced_secrets"] == ["redacted-secret-1"]


def test_workload_copy_for_persistence_copies_referenced_configmaps_for_non_mocked_modes():
    workload = {"service_name": "payments-api", "referenced_configmaps": ["cfg"]}

    sanitized = workload_copy_for_persistence(workload, "sanitized")
    mocked = workload_copy_for_persistence(workload, "mocked")

    assert sanitized == workload
    assert sanitized is not workload
    assert sanitized["referenced_configmaps"] is not workload["referenced_configmaps"]
    assert mocked == workload
    assert mocked is not workload
    assert mocked["referenced_configmaps"] is workload["referenced_configmaps"]


def test_mocked_report_identity_fields_redact_report_level_values():
    report = {
        "cluster": "ctx",
        "namespace": "payments",
        "discovery": {"context": "ctx", "kubeconfig": "/home/user/.kube/config", "empty": ""},
        "helm_releases": ["payments-release"],
    }

    fields = mocked_report_identity_fields(report, "seed")

    assert fields["cluster"].startswith("mock-cluster-")
    assert fields["namespace"].startswith("id-")
    assert set(fields["discovery"]) == {"context", "kubeconfig"}
    assert fields["discovery"]["context"].startswith("mock-context-")
    assert fields["helm_releases"][0].startswith("mock-release-")


def test_mocked_workload_identity_fields_redact_workload_level_values():
    workload = {
        "service_id": "ctx:payments:Deployment:payments-api",
        "cluster": "ctx",
        "namespace": "payments",
        "project": "pay",
        "kind": "Deployment",
        "service_name": "payments-api",
        "app_service": "payments",
        "containers": [
            {"name": "app", "image": "example/pay:1"},
            {"image": "example/nameless:1"},
        ],
        "release": "payments-release",
        "selector": {"app": "payments"},
    }

    fields = mocked_workload_identity_fields(workload, "seed")

    assert fields["service_id"].startswith("mock-service-id-")
    assert fields["cluster"].startswith("mock-cluster-")
    assert fields["namespace"].startswith("id-")
    assert fields["project"].startswith("mock-project-")
    assert fields["app_service"].startswith("mock-app-service-")
    assert fields["service_name"].startswith("id-")
    assert fields["containers"][0]["name"].startswith("mock-container-")
    assert fields["containers"][0]["image"].startswith("mock-image-")
    assert len(fields["containers"]) == 1
    assert fields["release"].startswith("mock-release-")
    assert next(iter(fields["selector"])).startswith("label-")


def test_mocked_workload_runtime_reference_fields_redact_runtime_references():
    workload = {
        "replicasets": ["payments-api-abc"],
        "statefulsets": ["payments-db"],
        "daemonsets": ["payments-agent"],
        "services": ["payments"],
        "ingresses": ["payments-web"],
        "referenced_configmaps": ["payments-config"],
        "entrypoints": [{"type": "Ingress", "name": "payments-web", "host": "pay.example.com", "port": 443}],
        "traffic_routes": [
            {
                "source": {"type": "External", "name": "pay.example.com"},
                "hops": [{"type": "Service", "name": "payments"}],
                "target": {"type": "Container", "names": ["app"]},
            }
        ],
    }

    fields = mocked_workload_runtime_reference_fields(workload, "seed")

    assert fields["replicasets"][0].startswith("mock-replicaset-")
    assert fields["statefulsets"][0].startswith("mock-statefulset-")
    assert fields["daemonsets"][0].startswith("mock-daemonset-")
    assert fields["services"][0].startswith("mock-service-")
    assert fields["ingresses"][0].startswith("mock-ingress-")
    assert fields["referenced_configmaps"][0].startswith("mock-configmap-")
    assert fields["entrypoints"][0]["name"].startswith("mock-ingress-")
    assert fields["traffic_routes"][0]["target"]["names"][0].startswith("mock-container-")


def test_sensitive_workload_fields_sanitize_secrets_dependencies_and_buckets():
    workload = {
        "referenced_secrets": ["payments-secret"],
        "runtime": {"ready_pods": 1},
        "dependency_candidates": [
            {
                "source": "Secret",
                "source_name": "payments-secret",
                "var": "PASSWORD_URL",
                "key": "api.example.com",
                "value": "https://api.example.com",
                "host": "api.example.com",
            }
        ],
        "bucket_candidates": [
            {
                "source": "Secret",
                "source_name": "payments-secret",
                "var": "S3_BUCKET",
                "bucket": "reports",
                "endpoint": "reports.s3.example.com",
                "confidence": "high",
            }
        ],
    }

    fields = sensitive_workload_fields(workload, "sanitized")

    assert fields["referenced_secrets"] == ["redacted-secret-1"]
    assert fields["runtime"] == {"ready_pods": 1}
    assert fields["dependency_candidates"][0]["source_name"] == "referenced"
    assert fields["dependency_candidates"][0]["value"] == "<redacted>"
    assert fields["dependency_candidates"][0]["var_redacted"] is True
    assert fields["bucket_candidates"][0]["source_name"] == "referenced"
    assert fields["bucket_candidates"][0]["bucket"] == "reports"


def test_sanitize_report_for_persistence_mocks_full_workload_fields():
    report = {
        "cluster": "ctx",
        "namespace": "payments",
        "discovery": {"context": "ctx", "kubeconfig": "/home/user/.kube/config", "empty": ""},
        "helm_releases": ["payments-release"],
        "workloads": [
            {
                "service_id": "ctx:payments:Deployment:payments-api",
                "cluster": "ctx",
                "namespace": "payments",
                "project": "pay",
                "kind": "Deployment",
                "service_name": "payments-api",
                "app_service": "payments",
                "containers": [
                    {"name": "app", "image": "example/pay:1"},
                    {"image": "example/nameless:1"},
                ],
                "release": "payments-release",
                "selector": {"app": "payments"},
                "replicasets": ["payments-api-abc"],
                "statefulsets": ["payments-db"],
                "daemonsets": ["payments-agent"],
                "services": ["payments"],
                "ingresses": ["payments-web"],
                "entrypoints": [{"type": "Ingress", "name": "payments-web", "host": "pay.example.com", "port": 443}],
                "traffic_routes": [
                    {
                        "source": {"type": "External", "name": "pay.example.com"},
                        "hops": [{"type": "Service", "name": "payments"}],
                        "target": {"type": "Container", "names": ["app"]},
                    }
                ],
                "referenced_configmaps": ["payments-config"],
                "referenced_secrets": ["payments-secret"],
                "runtime": {"ready_pods": 1},
                "dependency_candidates": [
                    {
                        "source": "Env",
                        "source_name": "runtime",
                        "var": "API_URL",
                        "key": "api.example.com",
                        "value": "https://api.example.com",
                        "host": "api.example.com",
                    }
                ],
            }
        ],
    }

    mocked = sanitize_report_for_persistence(report, "mocked", "seed")
    workload = mocked["workloads"][0]

    assert mocked["cluster"].startswith("mock-cluster-")
    assert mocked["namespace"].startswith("id-")
    assert set(mocked["discovery"]) == {"context", "kubeconfig"}
    assert mocked["helm_releases"][0].startswith("mock-release-")
    assert workload["service_id"].startswith("mock-service-id-")
    assert workload["cluster"].startswith("mock-cluster-")
    assert workload["namespace"].startswith("id-")
    assert workload["project"].startswith("mock-project-")
    assert workload["app_service"].startswith("mock-app-service-")
    assert workload["service_name"].startswith("id-")
    assert workload["containers"][0]["name"].startswith("mock-container-")
    assert workload["containers"][0]["image"].startswith("mock-image-")
    assert len(workload["containers"]) == 1
    assert workload["release"].startswith("mock-release-")
    assert next(iter(workload["selector"])).startswith("label-")
    assert workload["replicasets"][0].startswith("mock-replicaset-")
    assert workload["statefulsets"][0].startswith("mock-statefulset-")
    assert workload["daemonsets"][0].startswith("mock-daemonset-")
    assert workload["services"][0].startswith("mock-service-")
    assert workload["ingresses"][0].startswith("mock-ingress-")
    assert workload["entrypoints"][0]["name"].startswith("mock-ingress-")
    assert workload["traffic_routes"][0]["target"]["names"][0].startswith("mock-container-")
    assert workload["referenced_configmaps"][0].startswith("mock-configmap-")
    assert workload["referenced_secrets"][0].startswith("mock-secret-")
    assert workload["runtime"] == {"ready_pods": 1}
    assert workload["dependency_candidates"][0]["value"] == "<redacted>"
    assert workload["dependency_candidates"][0]["host"] != "api.example.com"
