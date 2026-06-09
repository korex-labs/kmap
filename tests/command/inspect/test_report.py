from kmap.command.inspect.report import (
    WorkloadReportEntryContext,
    build_workload_report_entry,
    matching_release_name,
    summarize_text_report,
    workload_lineage,
    workload_report_entry,
)


def test_build_workload_report_entry_preserves_report_shape():
    entry = build_workload_report_entry(
        cluster="ctx",
        namespace="payments",
        project="pay",
        kind="Deployment",
        service_name="pay-api",
        service_id="ctx:payments:Deployment:pay-api",
        selector={"app": "pay"},
        app_service="payments-api",
        app_service_source={"kind": "annotation"},
        container_context={
            "inventory": [{"name": "app", "kind": "container", "image": "example/app:1", "ports": []}],
            "referenced_configmaps": {"cfg-b", "cfg-a"},
            "referenced_secrets": {"sec-b", "sec-a"},
        },
        network_context={
            "services": ["svc-b", "svc-a"],
            "ingresses": ["ing-b", "ing-a"],
            "entrypoints": [{"type": "Service", "name": "svc-a"}],
            "traffic_routes": [{"direction": "inbound"}],
        },
        storage_context={"volume_types": ["persistentVolumeClaim"]},
        observability_context={"prometheus_scrapes": ["true"]},
        security_context={"service_account": "pay-api"},
        scheduling_context={"priority_class": "high"},
        runtime_status={"replicas_ready": 1},
        release_names=["pay-api-release", "pay-api"],
        replicasets_by_deployment={"pay-api": ["pay-api-rs"]},
        dependency_candidates=[{"var": "API_URL"}],
    )

    assert entry == {
        "service_id": "ctx:payments:Deployment:pay-api",
        "cluster": "ctx",
        "namespace": "payments",
        "project": "pay",
        "kind": "Deployment",
        "service_name": "pay-api",
        "app_service": "payments-api",
        "app_service_source": {"kind": "annotation"},
        "containers": [{"name": "app", "kind": "container", "image": "example/app:1", "ports": []}],
        "runtime": {"replicas_ready": 1},
        "autoscaling": {},
        "release": "pay-api",
        "selector": {"app": "pay"},
        "replicasets": ["pay-api-rs"],
        "statefulsets": [],
        "daemonsets": [],
        "services": ["svc-a", "svc-b"],
        "ingresses": ["ing-a", "ing-b"],
        "entrypoints": [{"type": "Service", "name": "svc-a"}],
        "traffic_routes": [{"direction": "inbound"}],
        "storage": {"volume_types": ["persistentVolumeClaim"]},
        "observability": {"prometheus_scrapes": ["true"]},
        "security": {"service_account": "pay-api"},
        "scheduling": {"priority_class": "high"},
        "referenced_configmaps": ["cfg-a", "cfg-b"],
        "referenced_secrets": ["sec-a", "sec-b"],
        "dependency_candidates": [{"var": "API_URL"}],
        "bucket_candidates": [],
    }


def test_build_workload_report_entry_sets_statefulset_and_daemonset_fields():
    base = {
        "cluster": "ctx",
        "namespace": "payments",
        "project": "pay",
        "service_id": "sid",
        "selector": {},
        "app_service": "",
        "app_service_source": {},
        "container_context": {"inventory": [], "referenced_configmaps": set(), "referenced_secrets": set()},
        "network_context": {"services": [], "ingresses": [], "entrypoints": [], "traffic_routes": []},
        "storage_context": {},
        "observability_context": {},
        "security_context": {},
        "scheduling_context": {},
        "runtime_status": {},
        "release_names": [],
        "replicasets_by_deployment": {"worker": ["worker-rs"]},
        "dependency_candidates": [],
    }

    stateful = build_workload_report_entry(kind="StatefulSet", service_name="db", **base)
    daemon = build_workload_report_entry(kind="DaemonSet", service_name="agent", **base)

    assert stateful["replicasets"] == []
    assert stateful["statefulsets"] == ["db"]
    assert stateful["daemonsets"] == []
    assert daemon["replicasets"] == []
    assert daemon["statefulsets"] == []
    assert daemon["daemonsets"] == ["agent"]


def test_workload_report_entry_accepts_context_object():
    entry = workload_report_entry(
        WorkloadReportEntryContext(
            cluster="ctx",
            namespace="payments",
            project="pay",
            kind="Deployment",
            service_name="pay-api",
            service_id="ctx:payments:Deployment:pay-api",
            selector={"app": "pay"},
            app_service="payments-api",
            app_service_source={"kind": "annotation"},
            container_context={
                "inventory": [{"name": "app"}],
                "referenced_configmaps": {"cfg"},
                "referenced_secrets": {"secret"},
            },
            network_context={
                "services": ["svc"],
                "ingresses": [],
                "entrypoints": [],
                "traffic_routes": [],
            },
            storage_context={},
            observability_context={},
            security_context={},
            scheduling_context={},
            runtime_status={},
            release_names=["pay-api"],
            replicasets_by_deployment={"pay-api": ["pay-api-rs"]},
            dependency_candidates=[],
            bucket_candidates=[{"bucket": "reports"}],
            autoscaling={"min_replicas": 1},
        )
    )

    assert entry["release"] == "pay-api"
    assert entry["replicasets"] == ["pay-api-rs"]
    assert entry["bucket_candidates"] == [{"bucket": "reports"}]
    assert entry["autoscaling"] == {"min_replicas": 1}


def test_report_release_and_lineage_helpers_keep_existing_selection_rules():
    assert matching_release_name(["", "pay-api-release", "pay"], "pay-api") == "pay"
    assert matching_release_name(["worker"], "pay-api") == ""
    assert workload_lineage("Deployment", "api", {"api": ["api-rs"]}) == {
        "replicasets": ["api-rs"],
        "statefulsets": [],
        "daemonsets": [],
    }
    assert workload_lineage("StatefulSet", "db", {"db": ["db-rs"]}) == {
        "replicasets": [],
        "statefulsets": ["db"],
        "daemonsets": [],
    }
    assert workload_lineage("DaemonSet", "agent", {}) == {
        "replicasets": [],
        "statefulsets": [],
        "daemonsets": ["agent"],
    }


def test_summarize_text_report_contains_workload_and_dependency_details():
    text = summarize_text_report(
        {
            "cluster": "ctx",
            "namespace": "payments",
            "workloads": [
                {
                    "service_id": "svc-1",
                    "cluster": "ctx",
                    "namespace": "payments",
                    "kind": "Deployment",
                    "service_name": "api",
                    "app_service_source": {"kind": "fallback"},
                    "containers": [{"name": "app"}],
                    "dependency_candidates": [
                        {"source": "Env", "source_name": "spec", "var": "API_URL", "key": "api.example"}
                    ],
                    "bucket_candidates": [
                        {
                            "source": "Env",
                            "source_name": "spec",
                            "var": "S3_BUCKET",
                            "bucket": "reports",
                            "endpoint": "",
                            "confidence": "high",
                        }
                    ],
                }
            ],
        }
    )

    assert "ServiceId: svc-1" in text
    assert "var=API_URL key=api.example" in text
    assert "var=S3_BUCKET bucket=reports" in text
