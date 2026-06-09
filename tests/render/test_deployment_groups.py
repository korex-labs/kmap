from kmap.render.deployment_groups import merged_instance_runtime, pod_groups


def test_pod_groups_keep_container_instances_under_workload_name():
    groups = pod_groups(
        [
            {"id": "inst-api-app", "name": "api", "node_kind": "k8s_pod"},
            {"id": "inst-api-sidecar", "name": "api", "node_kind": "k8s_pod"},
            {"id": "inst-worker", "name": "worker", "node_kind": "k8s_pod"},
        ]
    )

    assert [group["title"] for group in groups] == ["api", "worker"]
    assert [instance["id"] for instance in groups[0]["instances"]] == ["inst-api-app", "inst-api-sidecar"]
    assert groups[0]["node_kinds"] == ["k8s_pod"]


def test_merged_instance_runtime_deduplicates_list_and_scalar_values():
    runtime = merged_instance_runtime(
        [
            {"runtime": {"services": ["api-svc", "api-svc"], "replicas_desired": [2]}},
            {"runtime": {"services": ["api-svc", "metrics-svc"], "replicas_desired": 2}},
        ]
    )

    assert runtime == {
        "replicas_desired": ["2"],
        "services": ["api-svc", "metrics-svc"],
    }
