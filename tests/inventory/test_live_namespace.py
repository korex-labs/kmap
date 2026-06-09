from argparse import Namespace

import pytest

from kmap.inventory import live_namespace
from kmap.inventory.full_progress import NamespaceInspectionTimings
from kmap.inventory.live_kubernetes import LiveNamespaceKubernetes
from kmap.inventory.live_namespace import (
    LightweightWorkloadContext,
    SelectedWorkload,
    inspect_live_namespace,
    lightweight_namespace_payload,
    lightweight_namespace_report,
    lightweight_workload_entries,
    optional_namespace_resources,
)


def full_args():
    return Namespace(
        cluster="cluster-a",
        match_regex="main|master",
        no_exec=True,
        max_exec_pods_per_workload=1,
    )


def test_inspect_live_namespace_collects_runtime_vault_bucket_candidates():
    args = full_args()
    args.no_exec = False
    calls = []

    class RuntimeDiscoveryClient:
        def get_json(self, kind, namespace=None):
            calls.append(("get", kind, namespace))
            if kind == "deploy":
                return {
                    "items": [
                        {
                            "metadata": {"name": "master-portal-api"},
                            "spec": {
                                "selector": {"matchLabels": {"app": "portal-api"}},
                                "template": {
                                    "metadata": {"labels": {"app": "portal-api"}},
                                    "spec": {"containers": [{"name": "app", "image": "example/app:1"}]},
                                },
                            },
                        }
                    ]
                }
            if kind == "pod":
                return {
                    "items": [
                        {
                            "metadata": {"name": "portal-api-abc", "labels": {"app": "portal-api"}},
                            "spec": {"containers": [{"name": "app", "command": ["/vault/vault-env"]}]},
                            "status": {
                                "phase": "Running",
                                "conditions": [{"type": "Ready", "status": "True"}],
                            },
                        }
                    ]
                }
            return {"items": []}

        def exec_capture(self, namespace, pod, container, argv, **kwargs):
            calls.append(("exec", namespace, pod, container, tuple(argv)))
            if argv == ["/vault/vault-env", "env"]:
                return (
                    "S3_ENDPOINT=ceph1.query.consul:7480\n"
                    "S3_PRIVATE_BUCKET=example-kube-web-portal-api-4639-portal-api-web-private\n"
                    "S3_PUBLIC_BUCKET=example-kube-web-portal-api-4639-portal-api-web-public\n"
                )
            return ""

    result = inspect_live_namespace(
        args,
        client=RuntimeDiscoveryClient(),
        namespace="web-portal-api-4639",
        inventory_row=None,
    )

    payload = str(result.report)
    assert "example-kube-web-portal-api-4639-portal-api-web-private" in payload
    assert "example-kube-web-portal-api-4639-portal-api-web-public" in payload
    assert ("get", "pod", "web-portal-api-4639") in calls
    assert ("exec", "web-portal-api-4639", "portal-api-abc", "app", ("env",)) not in calls
    assert (
        "exec",
        "web-portal-api-4639",
        "portal-api-abc",
        "app",
        ("/vault/vault-env", "env"),
    ) in calls
    assert result.metrics.vault_execs == 1


def test_lightweight_namespace_report_skips_optional_resources_when_selected_workloads_do_not_need_them():
    calls = []

    class LeanDiscoveryClient:
        def get_json(self, kind, namespace=None):
            calls.append((kind, namespace))
            if kind == "deploy":
                return {
                    "items": [
                        {
                            "metadata": {"name": "main-api"},
                            "spec": {"template": {"spec": {"containers": [{"name": "api", "image": "example/api:1"}]}}},
                        }
                    ]
                }
            return {"items": []}

    report = lightweight_namespace_report(
        full_args(),
        kubernetes=LiveNamespaceKubernetes(LeanDiscoveryClient()),
        namespace="api-prod",
        inventory_row=None,
    )

    assert report["workloads"][0]["service_name"] == "main-api"
    assert ("deploy", "api-prod") in calls
    assert ("sts", "api-prod") in calls
    assert ("ds", "api-prod") in calls
    assert ("cm", "api-prod") not in calls
    assert ("secret", "api-prod") not in calls
    assert ("pod", "api-prod") not in calls


def test_lightweight_namespace_report_updates_progress_during_namespace_phases():
    progress_messages = []
    args = full_args()
    args.no_exec = False

    class RecordingProgress:
        def update(self, message):
            progress_messages.append(message)

    class ProgressDiscoveryClient:
        def get_json(self, kind, namespace=None):
            if kind == "deploy":
                return {
                    "items": [
                        {
                            "metadata": {"name": "main-api"},
                            "spec": {
                                "template": {
                                    "spec": {
                                        "containers": [
                                            {
                                                "name": "api",
                                                "image": "example/api:1",
                                                "envFrom": [{"configMapRef": {"name": "api-config"}}],
                                            }
                                        ]
                                    }
                                }
                            },
                        }
                    ]
                }
            return {"items": []}

    report = lightweight_namespace_report(
        args,
        kubernetes=LiveNamespaceKubernetes(ProgressDiscoveryClient()),
        namespace="api-prod",
        inventory_row=None,
        progress=RecordingProgress(),
    )

    assert report["workloads"][0]["service_name"] == "main-api"
    assert progress_messages == [
        "api-prod: fetch workloads",
        "api-prod: fetch configmaps",
        "api-prod: fetch pods",
        "api-prod: inspect workloads",
        "api-prod: scan Deployment/main-api",
    ]


def test_lightweight_namespace_payload_keeps_generated_report_shape():
    assert lightweight_namespace_payload(
        full_args(),
        namespace="api-prod",
        workloads=[{"service_name": "main-api"}],
    ) == {
        "cluster": "cluster-a",
        "namespace": "api-prod",
        "discovery": {
            "mode": "full-inventory",
            "scope": "workloads-configmaps-secrets",
        },
        "helm_releases": [],
        "workloads": [{"service_name": "main-api"}],
    }


def test_optional_namespace_resources_fetches_only_needed_resources():
    calls = []

    class OptionalDiscoveryClient:
        def get_json(self, kind, namespace=None):
            calls.append((kind, namespace))
            return {"items": [{"kind": kind}]}

    timings = NamespaceInspectionTimings()
    resources = optional_namespace_resources(
        full_args(),
        kubernetes=LiveNamespaceKubernetes(OptionalDiscoveryClient()),
        namespace="api-prod",
        selected_workloads=[SelectedWorkload(kind="Deployment", workload={})],
        referenced_configmaps={"api-config"},
        referenced_secrets=set(),
        timings=timings,
    )

    assert resources == {
        "cm": {"items": [{"kind": "cm"}]},
        "secret": {"items": []},
        "pod": {"items": []},
    }
    assert calls == [("cm", "api-prod")]
    assert timings.secrets == pytest.approx(0.0)
    assert timings.pods == pytest.approx(0.0)


def test_lightweight_workload_entries_delegates_in_selected_order(monkeypatch):
    calls = []

    def fake_lightweight_workload_entry(args, **kwargs):
        calls.append(kwargs)
        return {"service_name": kwargs["selected"].workload["metadata"]["name"]}

    monkeypatch.setattr(live_namespace, "lightweight_workload_entry", fake_lightweight_workload_entry)
    selected = [
        SelectedWorkload(kind="Deployment", workload={"metadata": {"name": "main-api"}}),
        SelectedWorkload(kind="StatefulSet", workload={"metadata": {"name": "main-worker"}}),
    ]

    rows = lightweight_workload_entries(
        full_args(),
        namespace="api-prod",
        selected_workloads=selected,
        configmaps={},
        secrets={},
        pods={},
        kubernetes=object(),
        inventory_row=None,
        metrics=object(),
        progress=None,
    )

    assert rows == [{"service_name": "main-api"}, {"service_name": "main-worker"}]
    assert [call["selected"].kind for call in calls] == ["Deployment", "StatefulSet"]
    assert {call["namespace"] for call in calls} == {"api-prod"}


def test_lightweight_workload_entries_accepts_context_object():
    class RuntimeKubernetes:
        def runtime_env_maps(self, **kwargs):
            return {}, {"S3_BUCKET": "reports"}

    selected = [
        SelectedWorkload(
            kind="Deployment",
            workload={"metadata": {"name": "main-api"}},
            container_context={
                "containers": [{"name": "app"}],
                "inventory": [{"name": "app"}],
                "referenced_configmaps": set(),
                "referenced_secrets": set(),
            },
        )
    ]

    rows = lightweight_workload_entries(
        full_args(),
        namespace="api-prod",
        selected_workloads=selected,
        configmaps={},
        secrets={},
        workload_context=LightweightWorkloadContext(
            pods={},
            kubernetes=RuntimeKubernetes(),
            inventory_row=None,
            metrics=live_namespace.NamespaceInspectionMetrics(),
        ),
    )

    assert rows[0]["bucket_candidates"][0]["bucket"] == "reports"
