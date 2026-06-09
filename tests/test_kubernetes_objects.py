import re

from kmap.kubernetes.objects import (
    annotations_of,
    app_service_source,
    configmap_data,
    container_inventory,
    container_port_labels,
    decode_secret_data,
    find_related_workloads,
    first_present_value,
    item_map,
    labels_of,
    obj_name,
    pod_labels_from_template,
    pod_template_annotations_of,
    selector_of_workload,
    service_selector,
    workload_app_service,
    workload_runtime_status,
    workload_service_id,
)


def test_obj_name_reads_metadata_name():
    assert obj_name({"metadata": {"name": "api"}}) == "api"
    assert labels_of({"metadata": {"labels": {"app": "api"}}}) == {"app": "api"}
    assert annotations_of({"metadata": {"annotations": {"team": "platform"}}}) == {"team": "platform"}
    assert pod_template_annotations_of({"spec": {"template": {"metadata": {"annotations": {"checksum": "abc"}}}}}) == {
        "checksum": "abc"
    }


def test_workload_app_service_prefers_workload_annotation_over_template():
    workload = {
        "metadata": {"annotations": {"app_service": "billing"}},
        "spec": {"template": {"metadata": {"annotations": {"app_service": "template"}}}},
    }

    value, source = workload_app_service(workload)

    assert value == "billing"
    assert source["path"] == "metadata.annotations.app_service"
    assert source["fallback_used"] is False


def test_workload_app_service_reads_template_annotation_and_fallback_source():
    value, source = workload_app_service(
        {"spec": {"template": {"metadata": {"annotations": {"app_service": "template-app"}}}}}
    )

    assert value == "template-app"
    assert source == app_service_source("spec.template.metadata.annotations.app_service")
    assert workload_app_service({}) == ("", app_service_source("", fallback_used=True))


def test_container_inventory_formats_named_ports_and_skips_empty_names():
    assert container_inventory(
        [
            {
                "name": "api",
                "image": "example/api:1",
                "ports": [{"name": "http", "containerPort": 8080, "protocol": "TCP"}],
            },
            {"name": "", "image": "ignored"},
        ],
        "container",
    ) == [
        {
            "name": "api",
            "kind": "container",
            "image": "example/api:1",
            "ports": ["http:8080/TCP"],
        }
    ]


def test_container_port_labels_formats_defaults_and_skips_missing_ports():
    assert container_port_labels(
        {
            "ports": [
                {"containerPort": 8080},
                {"name": "admin", "containerPort": 9090, "protocol": "UDP"},
                {"name": "missing"},
            ]
        }
    ) == ["8080/TCP", "admin:9090/UDP"]


def test_configmap_secret_object_maps_and_workload_id_helpers():
    assert configmap_data({"data": {"PORT": 8080}}) == {"PORT": "8080"}
    assert decode_secret_data({"data": {"TOKEN": "dmFsdWU="}}) == {"TOKEN": "value"}
    assert decode_secret_data({"data": {"TOKEN": "not-base64"}}) == {}
    assert item_map({"items": [{"metadata": {"name": "api"}}, {"metadata": {}}]}) == {
        "api": {"metadata": {"name": "api"}}
    }
    assert workload_service_id("ctx", "ns", "Deployment", "api$main") == "ctx:ns:Deployment:api_main"


def test_selector_and_related_workload_helpers():
    workload = {
        "spec": {
            "selector": {"matchLabels": {"app": "api", "empty": ""}},
            "template": {"metadata": {"labels": {"app": "api"}}},
        }
    }

    assert selector_of_workload(workload) == {"app": "api"}
    assert pod_labels_from_template(workload) == {"app": "api"}
    assert service_selector({"spec": {"selector": {"app": "api"}}}) == {"app": "api"}
    related = find_related_workloads({"items": [{"metadata": {"name": "api-1"}}]}, re.compile(r"api"))

    assert [item["metadata"]["name"] for item in related] == ["api-1"]


def test_workload_runtime_status_prefers_workload_fields_and_falls_back_to_daemonset_fields():
    assert (
        first_present_value({"replicas": 0}, {"desiredNumberScheduled": 3}, "replicas", "desiredNumberScheduled") == 0
    )
    assert workload_runtime_status(
        {"spec": {"replicas": 0}, "status": {"readyReplicas": 0, "availableReplicas": 1}},
        [{"metadata": {"name": "api-1"}}],
    ) == {
        "running_pods": 1,
        "replicas_desired": 0,
        "replicas_ready": 0,
        "replicas_available": 1,
    }
    assert workload_runtime_status(
        {"status": {"desiredNumberScheduled": 2, "numberReady": 1, "numberAvailable": 1}},
        [],
    ) == {
        "running_pods": 0,
        "replicas_desired": 2,
        "replicas_ready": 1,
        "replicas_available": 1,
    }
