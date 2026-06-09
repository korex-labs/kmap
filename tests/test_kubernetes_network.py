from kmap.kubernetes.network import (
    backend_service_name,
    backend_service_port,
    ingress_entrypoints,
    ingress_http_paths,
    ingress_routes,
    ingress_services,
    service_entrypoints,
    service_entrypoints_for_aliases,
    service_matches_workload,
    workload_pods,
)
from kmap.kubernetes.objects import workload_runtime_status


def test_backend_service_helpers_read_name_and_named_or_numeric_port():
    assert backend_service_name({"service": {"name": "api-svc"}}) == "api-svc"
    assert backend_service_port({"service": {"port": {"number": 8080}}}) == 8080
    assert backend_service_port({"service": {"port": {"name": "http"}}}) == "http"
    assert backend_service_name({}) == ""
    assert backend_service_port({}) is None


def test_service_entrypoints_for_aliases_keeps_no_port_shape():
    assert service_entrypoints_for_aliases("api-svc", [], ["api-svc", "10.0.0.1"]) == [
        {
            "type": "Service",
            "name": "api-svc",
            "endpoint": "api-svc",
            "host": "api-svc",
            "port": None,
            "protocol": None,
            "targetPort": None,
        },
        {
            "type": "Service",
            "name": "api-svc",
            "endpoint": "10.0.0.1",
            "host": "10.0.0.1",
            "port": None,
            "protocol": None,
            "targetPort": None,
        },
    ]


def test_network_helpers_ignore_missing_selectors_and_empty_ingress_hosts():
    workload = {"spec": {"template": {"metadata": {"labels": {"app": "api"}}}}}

    assert service_matches_workload({"spec": {}}, workload) is False
    assert (
        workload_pods({"items": [{"metadata": {"labels": {"app": "api"}}, "status": {"phase": "Running"}}]}, {}) == []
    )
    assert ingress_entrypoints(
        {
            "metadata": {"name": "api-ing"},
            "spec": {"rules": [{"host": ""}, {"host": " API.EXAMPLE "}]},
        }
    ) == [
        {
            "type": "Ingress",
            "name": "api-ing",
            "endpoint": "api.example",
            "host": "api.example",
            "port": 443,
            "protocol": "HTTPS",
            "targetPort": None,
        }
    ]


def test_service_entrypoints_include_aliases_without_cluster_ip():
    endpoints = service_entrypoints(
        {
            "metadata": {"name": "api-svc"},
            "spec": {"clusterIP": None, "ports": [{"port": 80}]},
        },
        "payments",
    )

    assert [entry["endpoint"] for entry in endpoints] == [
        "api-svc:80",
        "api-svc.payments:80",
        "api-svc.payments.svc:80",
        "api-svc.payments.svc.cluster.local:80",
    ]
    assert {entry["protocol"] for entry in endpoints} == {"TCP"}


def test_service_and_ingress_matching_helpers():
    workload = {
        "metadata": {"name": "api"},
        "spec": {
            "selector": {"matchLabels": {"app": "api"}},
            "template": {"metadata": {"labels": {"app": "api"}}},
            "replicas": 2,
        },
        "status": {"readyReplicas": 1, "availableReplicas": 1},
    }
    service = {
        "metadata": {"name": "api-svc"},
        "spec": {
            "selector": {"app": "api"},
            "clusterIP": "10.0.0.1",
            "ports": [{"port": 80, "targetPort": 8080, "protocol": "TCP"}],
        },
    }
    ingress = {
        "metadata": {"name": "api-ing"},
        "spec": {
            "defaultBackend": {"service": {"name": "api-svc"}},
            "rules": [
                {
                    "host": "API.EXAMPLE",
                    "http": {
                        "paths": [
                            {"backend": {"service": {"name": "api-svc"}}},
                            {
                                "path": "/admin",
                                "backend": {"service": {"name": "admin-svc", "port": {"name": "http"}}},
                            },
                        ]
                    },
                }
            ],
        },
    }
    pods = {
        "items": [
            {"metadata": {"labels": {"app": "api"}}, "status": {"phase": "Running"}},
            {"metadata": {"labels": {"app": "api"}}, "status": {"phase": "Pending"}},
        ]
    }

    assert service_matches_workload(service, workload) is True
    assert len(workload_pods(pods, workload)) == 1
    assert workload_runtime_status(workload, workload_pods(pods, workload)) == {
        "running_pods": 1,
        "replicas_desired": 2,
        "replicas_ready": 1,
        "replicas_available": 1,
    }
    assert [path.get("path") for _host, path in ingress_http_paths(ingress["spec"])] == [None, "/admin"]
    assert ingress_services(ingress) == ["api-svc", "api-svc", "admin-svc"]
    assert ingress_routes(ingress) == [
        {"ingress": "api-ing", "host": "", "path": "/", "service": "api-svc", "service_port": None},
        {"ingress": "api-ing", "host": "api.example", "path": "/", "service": "api-svc", "service_port": None},
        {"ingress": "api-ing", "host": "api.example", "path": "/admin", "service": "admin-svc", "service_port": "http"},
    ]
    assert ingress_entrypoints(ingress) == [
        {
            "type": "Ingress",
            "name": "api-ing",
            "endpoint": "api.example",
            "host": "api.example",
            "port": 443,
            "protocol": "HTTPS",
            "targetPort": None,
        }
    ]
    endpoints = service_entrypoints(service, "payments")
    assert {
        "type": "Service",
        "name": "api-svc",
        "endpoint": "api-svc.payments.svc.cluster.local:80",
        "host": "api-svc.payments.svc.cluster.local",
        "port": 80,
        "protocol": "TCP",
        "targetPort": 8080,
    } in endpoints
