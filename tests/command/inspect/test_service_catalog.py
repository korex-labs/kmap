from kmap.command.inspect.service_catalog import (
    build_internal_alias_to_service,
    build_service_catalog,
    entrypoint_aliases,
    service_catalog_item,
)


def test_service_catalog_and_internal_aliases_include_service_entrypoints():
    services = [
        {
            "metadata": {"name": "orders"},
            "spec": {
                "clusterIP": "10.0.0.10",
                "ports": [{"port": 8080, "targetPort": 8080}],
            },
        },
        {"metadata": {}, "spec": {"ports": [{"port": 9090}]}},
    ]

    catalog = build_service_catalog(services, "payments")
    aliases = build_internal_alias_to_service(catalog)

    assert len(catalog) == 1
    assert catalog[0]["name"] == "orders"
    assert catalog[0]["namespace"] == "payments"
    assert catalog[0]["cluster_ip"] == "10.0.0.10"
    assert aliases["orders"] == ["orders"]
    assert aliases["orders.payments"] == ["orders"]
    assert aliases["orders.payments.svc"] == ["orders"]
    assert aliases["orders.payments.svc.cluster.local"] == ["orders"]


def test_service_catalog_item_and_entrypoint_aliases_keep_shapes():
    service = {
        "metadata": {"name": "orders"},
        "spec": {
            "clusterIP": "10.0.0.10",
            "ports": [{"port": 8080, "targetPort": 8080}],
        },
    }

    item = service_catalog_item(service, "payments")

    assert item["name"] == "orders"
    assert item["namespace"] == "payments"
    assert item["cluster_ip"] == "10.0.0.10"
    assert entrypoint_aliases({"host": "orders", "endpoint": "orders:8080"}) == ["orders", "orders:8080"]
    assert service_catalog_item({"metadata": {}}, "payments") == {}
