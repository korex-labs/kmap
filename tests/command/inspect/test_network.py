from kmap.command.inspect.network import (
    matched_ingress_names,
    matched_service_names,
    named_objects,
    workload_network_context,
)


def test_workload_network_context_collects_services_ingresses_and_routes():
    workload = {
        "metadata": {"name": "pay-api"},
        "spec": {
            "selector": {"matchLabels": {"app": "pay"}},
            "template": {
                "metadata": {"labels": {"app": "pay"}},
                "spec": {"containers": [{"name": "app"}]},
            },
        },
    }
    service = {
        "metadata": {"name": "pay-svc"},
        "spec": {
            "selector": {"app": "pay"},
            "ports": [{"name": "http", "port": 80, "targetPort": 8080, "protocol": "TCP"}],
        },
    }
    ingress = {
        "metadata": {"name": "pay-ing"},
        "spec": {
            "rules": [
                {
                    "host": "pay.example.com",
                    "http": {
                        "paths": [
                            {
                                "path": "/pay",
                                "backend": {
                                    "service": {
                                        "name": "pay-svc",
                                        "port": {"number": 80},
                                    }
                                },
                            }
                        ]
                    },
                }
            ]
        },
    }

    context = workload_network_context(workload, "payments", [service], [ingress])

    assert context["services"] == ["pay-svc"]
    assert context["ingresses"] == ["pay-ing"]
    assert [entrypoint["type"] for entrypoint in context["entrypoints"]].count("Service") == 4
    assert context["entrypoints"][-1]["type"] == "Ingress"
    assert context["traffic_routes"] == [
        {
            "direction": "inbound",
            "source": {"type": "ServiceClient", "name": "pay-svc"},
            "hops": [
                {
                    "type": "Service",
                    "name": "pay-svc",
                    "port": 80,
                    "protocol": "TCP",
                    "target_port": 8080,
                },
                {"type": "Workload", "name": "pay-api"},
            ],
            "target": {"type": "Container", "names": ["app"]},
        },
        {
            "direction": "inbound",
            "source": {"type": "External", "name": "pay.example.com", "path": "/pay"},
            "hops": [
                {"type": "Ingress", "name": "pay-ing", "host": "pay.example.com", "path": "/pay"},
                {"type": "Service", "name": "pay-svc", "port": 80},
                {"type": "Workload", "name": "pay-api"},
            ],
            "target": {"type": "Container", "names": ["app"]},
        },
    ]


def test_network_matching_helpers_keep_input_order():
    workload = {
        "spec": {
            "selector": {"matchLabels": {"app": "pay"}},
            "template": {"metadata": {"labels": {"app": "pay"}}},
        }
    }
    services = [
        {"metadata": {"name": "ignored"}, "spec": {"selector": {"app": "other"}}},
        {"metadata": {"name": "pay-svc"}, "spec": {"selector": {"app": "pay"}}},
        {"metadata": {"name": "pay-admin"}, "spec": {"selector": {"app": "pay"}}},
    ]
    ingresses = [
        {"metadata": {"name": "admin-ing"}, "spec": {"defaultBackend": {"service": {"name": "pay-admin"}}}},
        {"metadata": {"name": "ignored-ing"}, "spec": {"defaultBackend": {"service": {"name": "ignored"}}}},
        {"metadata": {"name": "pay-ing"}, "spec": {"defaultBackend": {"service": {"name": "pay-svc"}}}},
    ]

    matched_services = matched_service_names(workload, services)

    assert matched_services == ["pay-svc", "pay-admin"]
    assert matched_ingress_names(matched_services, ingresses) == ["admin-ing", "pay-ing"]


def test_named_objects_filters_by_name_without_reordering():
    objects = [
        {"metadata": {"name": "first"}},
        {"metadata": {"name": "second"}},
        {"metadata": {"name": "third"}},
    ]

    assert [obj["metadata"]["name"] for obj in named_objects(objects, ["third", "first"])] == ["first", "third"]
