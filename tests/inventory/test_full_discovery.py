from argparse import Namespace
from datetime import datetime, timezone

import pytest

from kmap.inventory import full_discovery, full_discovery_namespaces
from kmap.inventory.full_discovery import (
    cluster_kubectl_client,
    discover_cluster_namespace_inventory,
    discover_cluster_namespace_labels,
    discover_cluster_namespaces,
    discover_full_inventory,
    discovered_namespace_rows,
)
from kmap.inventory.full_discovery_client import (
    namespace_inventory_from_items,
    namespace_item_labels,
    namespace_item_name,
)
from kmap.inventory.full_discovery_namespaces import (
    NamespacePersistenceContext,
    inspect_and_persist_namespace,
    persist_inspected_namespace,
)
from kmap.inventory.full_progress import NamespaceInspectionMetrics, NamespaceInspectionTimings
from kmap.inventory.live_namespace import NamespaceInspectionResult
from kmap.inventory.namespaces import InventoryRow


class FakeClient:
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs

    def check_reachable(self):
        return True, ""

    def get_json(self, kind, namespace=None):
        if kind != "namespace":
            return {"items": []}
        return {
            "items": [
                {"metadata": {"name": "worker-dev"}},
                {"metadata": {"name": "api-prod", "labels": {"app.kubernetes.io/name": "api", "empty": ""}}},
            ]
        }

    def cluster_label(self):
        return "context=cluster-a"


def full_args(tmp_path):
    return Namespace(
        cluster="cluster-a",
        config_dir=str(tmp_path / "config"),
        bucket_artifacts_dir=str(tmp_path / "artifacts" / "buckets"),
        output_dir=str(tmp_path / "Inventory"),
        full_reports_dir=str(tmp_path / "reports"),
        fragment_id="team-a",
        kubeconfig="",
        kubectl="kubectl",
        helm="helm",
        request_timeout="15s",
        exec_sleep=0,
        inventory_exec_timeout=5,
        inventory_exec_attempts=1,
        kubectl_qps_sleep=0,
        match_regex="main",
        no_exec=True,
        max_exec_pods_per_workload=1,
        data_mode="sanitized",
        mock_seed="",
        output="lines",
        kmap_tool_config={},
    )


def test_discover_cluster_namespaces_sorts_live_namespace_names(monkeypatch, tmp_path):
    monkeypatch.setattr(full_discovery, "KubectlClient", FakeClient)

    assert discover_cluster_namespaces(full_args(tmp_path)) == ["api-prod", "worker-dev"]


def test_discover_cluster_namespace_labels_reads_live_namespace_metadata(monkeypatch, tmp_path):
    monkeypatch.setattr(full_discovery, "KubectlClient", FakeClient)

    assert discover_cluster_namespace_labels(full_args(tmp_path)) == {
        "api-prod": {"app.kubernetes.io/name": "api", "empty": ""}
    }


def test_discover_cluster_namespace_inventory_fetches_names_and_labels_once(monkeypatch, tmp_path):
    calls = []

    class CountingClient(FakeClient):
        def get_json(self, kind, namespace=None):
            calls.append((kind, namespace))
            return super().get_json(kind, namespace)

    monkeypatch.setattr(full_discovery, "KubectlClient", CountingClient)

    inventory = discover_cluster_namespace_inventory(full_args(tmp_path))

    assert inventory.namespaces == ["api-prod", "worker-dev"]
    assert inventory.labels_by_namespace == {"api-prod": {"app.kubernetes.io/name": "api", "empty": ""}}
    assert calls == [("namespace", "")]


def test_namespace_item_label_helpers_tolerate_malformed_metadata():
    assert namespace_item_name({}) == ""
    assert namespace_item_name({"metadata": {"name": 123}}) == "123"
    assert namespace_item_labels({}) == {}
    assert namespace_item_labels({"metadata": {"labels": "bad"}}) == {}
    assert namespace_item_labels({"metadata": {"labels": {"": "skip", "enabled": True, "revision": 3}}}) == {
        "enabled": "True",
        "revision": "3",
    }


def test_namespace_inventory_from_items_keeps_names_and_valid_labels_together():
    inventory = namespace_inventory_from_items(
        [
            {"metadata": {"name": "worker-dev"}},
            {"metadata": {"name": "api-prod", "labels": {"team": "platform"}}},
            {"metadata": {"labels": {"ignored": "missing-name"}}},
            {"metadata": {"name": "", "labels": {"ignored": "blank-name"}}},
        ]
    )

    assert inventory.namespaces == ["api-prod", "worker-dev"]
    assert inventory.labels_by_namespace == {"api-prod": {"team": "platform"}}


def test_discover_cluster_namespace_labels_skips_namespaces_without_valid_labels(monkeypatch, tmp_path):
    class MalformedLabelClient(FakeClient):
        def get_json(self, kind, namespace=None):
            if kind != "namespace":
                return {"items": []}
            return {
                "items": [
                    {"metadata": {"name": "missing-labels"}},
                    {"metadata": {"name": "bad-labels", "labels": "bad"}},
                    {"metadata": {"name": "good-labels", "labels": {"team": "platform"}}},
                    {"metadata": {"labels": {"ignored": "missing-name"}}},
                    "bad-item",
                ]
            }

    monkeypatch.setattr(full_discovery, "KubectlClient", MalformedLabelClient)

    assert discover_cluster_namespace_labels(full_args(tmp_path)) == {"good-labels": {"team": "platform"}}


def test_discover_cluster_namespaces_fails_when_cluster_unreachable(monkeypatch, tmp_path):
    class UnreachableClient(FakeClient):
        def check_reachable(self):
            return False, "vpn down"

    monkeypatch.setattr(full_discovery, "KubectlClient", UnreachableClient)

    with pytest.raises(SystemExit, match="Kubernetes discovery preflight failed"):
        discover_cluster_namespaces(full_args(tmp_path))


def test_cluster_kubectl_client_builds_discovery_and_inspection_clients(monkeypatch, tmp_path):
    calls = []

    class RecordingClient(FakeClient):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            calls.append(kwargs)

    monkeypatch.setattr(full_discovery, "KubectlClient", RecordingClient)
    args = full_args(tmp_path)

    cluster_kubectl_client(args)
    cluster_kubectl_client(args, exec_timeout=4, exec_attempts=2)

    assert calls == [
        {
            "kubectl": "kubectl",
            "helm": "helm",
            "context": "cluster-a",
            "kubeconfig": "",
            "request_timeout": "15s",
            "qps_sleep": 0,
            "exec_sleep": 0,
        },
        {
            "kubectl": "kubectl",
            "helm": "helm",
            "context": "cluster-a",
            "kubeconfig": "",
            "request_timeout": "15s",
            "qps_sleep": 0,
            "exec_sleep": 0,
            "exec_timeout": 4,
            "exec_attempts": 2,
        },
    ]


def test_discovered_namespace_rows_enriches_known_namespaces_and_keeps_unknowns():
    rows = discovered_namespace_rows(
        "cluster-a",
        ["api-prod", "unknown-review"],
        {
            "api-prod": InventoryRow(
                cluster="configured-cluster",
                product="demo",
                product_title="Demo",
                namespace="api-prod",
                repository="https://git.example/api",
                owner_team="Ops",
                stage="prod",
            )
        },
        labels_by_namespace={"api-prod": {"app": "api"}},
    )

    assert rows[0] == InventoryRow(
        cluster="cluster-a",
        product="demo",
        product_title="Demo",
        namespace="api-prod",
        repository="https://git.example/api",
        owner_team="Ops",
        labels={"app": "api"},
        stage="prod",
    )
    assert rows[1].namespace == "unknown-review"
    assert rows[1].stage == "review"


def test_discovered_namespace_rows_uses_configured_heuristics_for_unknown_namespaces():
    rows = discovered_namespace_rows(
        "cluster-a",
        ["payment-api-prod-1234", "payment-api-review-1234"],
        {},
        tool_config={
            "inventory": {
                "namespace_heuristics": {
                    "project_id_suffix": {
                        "enabled": True,
                        "pattern": r"[-](?P<project_id>\d+)$",
                        "repository_format": "repository:{project_id}",
                    },
                    "strip_project_id_suffix": True,
                    "stage_tokens": ["prod", "review"],
                }
            }
        },
    )

    assert {row.product for row in rows} == {""}
    assert {row.repository for row in rows} == {"repository:1234"}
    assert [row.stage for row in rows] == ["prod", "review"]


def test_discovered_namespace_rows_reuses_configured_repository_family_metadata():
    rows = discovered_namespace_rows(
        "cluster-a",
        ["payment-api-prod-1234", "payment-api-review-1234"],
        {
            "payment-api-prod-1234": InventoryRow(
                cluster="cluster-a",
                product="payments",
                product_title="Payments",
                namespace="payment-api-prod-1234",
                repository="https://git.example/payments/payment-api",
                owner_team="Platform Team",
                stage="prod",
            )
        },
        tool_config={
            "inventory": {
                "namespace_heuristics": {
                    "project_id_suffix": {
                        "enabled": True,
                        "pattern": r"[-](?P<project_id>\d+)$",
                    },
                    "strip_project_id_suffix": True,
                    "stage_tokens": ["prod", "review"],
                }
            }
        },
    )

    assert rows[0].namespace == "payment-api-prod-1234"
    assert rows[1] == InventoryRow(
        cluster="cluster-a",
        product="payments",
        product_title="Payments",
        namespace="payment-api-review-1234",
        repository="https://git.example/payments/payment-api",
        owner_team="Platform Team",
        stage="review",
    )


def test_discover_full_inventory_inspects_namespaces_and_writes_cluster_pages(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "demo.yaml").write_text(
        """
product: demo
title: Demo
env: prod
owner_team: Ops
discovery:
  context: cluster-a
namespaces:
  api-prod:
    resources:
      repo: https://git.example/api
""",
        encoding="utf-8",
    )

    class DiscoveryClient(FakeClient):
        def get_json(self, kind, namespace=None):
            if kind == "namespace":
                return {"items": [{"metadata": {"name": "api-prod", "labels": {"app": "api"}}}]}
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
            if kind == "cm":
                return {
                    "items": [
                        {
                            "metadata": {"name": "api-config"},
                            "data": {"S3_BUCKET_NAME": "demo-bucket"},
                        }
                    ]
                }
            return {"items": []}

    monkeypatch.setattr(full_discovery, "KubectlClient", DiscoveryClient)

    assert discover_full_inventory(full_args(tmp_path), generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc)) == 0

    state_file = tmp_path / "Inventory" / "clusters" / "cluster-a" / "state" / "namespaces" / "api-prod.json"
    report = tmp_path / "reports" / "cluster-a" / "api-prod.report.json"
    assert state_file.exists()
    assert '"namespace": "api-prod"' in state_file.read_text(encoding="utf-8")
    assert '"labels": {' in state_file.read_text(encoding="utf-8")
    assert '"app": "api"' in state_file.read_text(encoding="utf-8")
    assert '"bucket": "demo-bucket"' in state_file.read_text(encoding="utf-8")
    assert '"bucket": "demo-bucket"' in report.read_text(encoding="utf-8")
    assert (tmp_path / "Inventory" / "clusters" / "cluster-a" / "inventory.json").exists()
    namespaces_html = (tmp_path / "Inventory" / "clusters" / "cluster-a" / "namespaces.html").read_text(
        encoding="utf-8"
    )
    assert '<span class="chip namespace-label">app=api</span>' in namespaces_html


def test_discover_full_inventory_flushes_namespace_state_before_later_namespace_fails(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    class PartialDiscoveryClient(FakeClient):
        def get_json(self, kind, namespace=None):
            if kind == "namespace":
                return {"items": [{"metadata": {"name": "api-prod"}}, {"metadata": {"name": "broken-prod"}}]}
            if namespace == "broken-prod":
                raise RuntimeError("boom")
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
                                                "env": [{"name": "S3_BUCKET_NAME", "value": "demo-bucket"}],
                                            }
                                        ]
                                    }
                                }
                            },
                        }
                    ]
                }
            return {"items": []}

    monkeypatch.setattr(full_discovery, "KubectlClient", PartialDiscoveryClient)

    with pytest.raises(RuntimeError, match="boom"):
        discover_full_inventory(full_args(tmp_path), generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc))

    state_file = tmp_path / "Inventory" / "clusters" / "cluster-a" / "state" / "namespaces" / "api-prod.json"
    assert state_file.exists()
    assert '"bucket": "demo-bucket"' in state_file.read_text(encoding="utf-8")
    assert not (tmp_path / "Inventory" / "clusters" / "cluster-a" / "namespaces.html").exists()


def test_discover_full_inventory_does_not_persist_raw_secret_values(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    class SecretDiscoveryClient(FakeClient):
        def get_json(self, kind, namespace=None):
            if kind == "namespace":
                return {"items": [{"metadata": {"name": "api-prod"}}]}
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
                                                "envFrom": [{"secretRef": {"name": "api-secret"}}],
                                            }
                                        ]
                                    }
                                }
                            },
                        }
                    ]
                }
            if kind == "secret":
                return {
                    "items": [
                        {
                            "metadata": {"name": "api-secret"},
                            "data": {
                                "S3_BUCKET_NAME": "cmVwb3J0cw==",
                                "S3_ACCESS_KEY": "ZG8tbm90LXB1Ymxpc2gtYWNjZXNzLWtleQ==",
                                "API_TOKEN": "ZG8tbm90LXB1Ymxpc2gtdG9rZW4=",
                                "DB_PASSWORD": "ZG8tbm90LXB1Ymxpc2gtcGFzc3dvcmQ=",
                            },
                        }
                    ]
                }
            return {"items": []}

    monkeypatch.setattr(full_discovery, "KubectlClient", SecretDiscoveryClient)

    assert discover_full_inventory(full_args(tmp_path), generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc)) == 0

    state_payload = (
        tmp_path / "Inventory" / "clusters" / "cluster-a" / "state" / "namespaces" / "api-prod.json"
    ).read_text(encoding="utf-8")
    report_payload = (tmp_path / "reports" / "cluster-a" / "api-prod.report.json").read_text(encoding="utf-8")
    persisted = state_payload + report_payload

    assert "reports" in persisted
    assert "do-not-publish-access-key" not in persisted
    assert "do-not-publish-token" not in persisted
    assert "do-not-publish-password" not in persisted
    assert "API_TOKEN" not in persisted
    assert "DB_PASSWORD" not in persisted


def test_discover_full_inventory_uses_inventory_exec_defaults_for_live_client(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    client_kwargs = []
    args = full_args(tmp_path)
    args.inventory_exec_timeout = 4
    args.inventory_exec_attempts = 1

    class InspectClient(FakeClient):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            client_kwargs.append(kwargs)

        def get_json(self, kind, namespace=None):
            if kind == "namespace":
                return {"items": [{"metadata": {"name": "api-prod"}}]}
            return {"items": []}

    monkeypatch.setattr(full_discovery, "KubectlClient", InspectClient)

    assert discover_full_inventory(args, generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc)) == 0

    assert client_kwargs[-1]["exec_timeout"] == 4
    assert client_kwargs[-1]["exec_attempts"] == 1


def test_discover_full_inventory_propagates_known_repository_family_to_html_and_buckets(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "demo.yaml").write_text(
        """
product: demo
title: Demo Payments
env: prod
owner_team: Platform Team
discovery:
  context: cluster-a
namespaces:
  payment-api-prod-1234:
    resources:
      repo: https://git.example/backend/payment-api
""",
        encoding="utf-8",
    )
    args = full_args(tmp_path)
    args.kmap_tool_config = {
        "inventory": {
            "namespace_heuristics": {
                "project_id_suffix": {
                    "enabled": True,
                    "pattern": r"[-](?P<project_id>\d+)$",
                },
                "strip_project_id_suffix": True,
                "stage_tokens": ["prod", "review"],
            }
        }
    }

    class FamilyDiscoveryClient(FakeClient):
        def get_json(self, kind, namespace=None):
            if kind == "namespace":
                return {
                    "items": [
                        {"metadata": {"name": "payment-api-prod-1234"}},
                        {"metadata": {"name": "payment-api-review-1234"}},
                    ]
                }
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
                                                "env": [
                                                    {
                                                        "name": "S3_BUCKET_NAME",
                                                        "value": f"{namespace}-bucket",
                                                    }
                                                ],
                                            }
                                        ]
                                    }
                                }
                            },
                        }
                    ]
                }
            return {"items": []}

    monkeypatch.setattr(full_discovery, "KubectlClient", FamilyDiscoveryClient)

    assert discover_full_inventory(args, generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc)) == 0

    review_state = (
        tmp_path / "Inventory" / "clusters" / "cluster-a" / "state" / "namespaces" / "payment-api-review-1234.json"
    ).read_text(encoding="utf-8")
    buckets_html = (tmp_path / "Inventory" / "clusters" / "cluster-a" / "buckets.html").read_text(encoding="utf-8")
    namespaces_html = (tmp_path / "Inventory" / "clusters" / "cluster-a" / "namespaces.html").read_text(
        encoding="utf-8"
    )

    assert '"product": "demo"' in review_state
    assert '"repository": "https://git.example/backend/payment-api"' in review_state
    assert '"owner_team": "Platform Team"' in review_state
    assert "Demo Payments" in namespaces_html
    assert "payment-api-review-1234" in namespaces_html
    assert "backend/payment-api" in buckets_html
    assert "Platform Team" in buckets_html


def test_discover_full_inventory_logs_html_outputs_without_state_file_paths(monkeypatch, tmp_path, capsys):
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    class EmptyDiscoveryClient(FakeClient):
        def get_json(self, kind, namespace=None):
            if kind == "namespace":
                return {"items": [{"metadata": {"name": "api-prod"}}]}
            return {"items": []}

    monkeypatch.setattr(full_discovery, "KubectlClient", EmptyDiscoveryClient)

    assert discover_full_inventory(full_args(tmp_path), generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc)) == 0

    err = capsys.readouterr().err
    assert "wrote cluster namespace state: 1 namespaces" in err
    assert "namespaces.html" in err
    assert "buckets.html" in err
    assert "clusters.html" in err
    assert "api-prod.json" not in err


def test_inspect_and_persist_namespace_writes_report_state_and_timing_summary(monkeypatch, tmp_path, capsys):
    calls = []

    def fake_inspect_live_namespace(args, *, client, namespace, inventory_row, progress):
        calls.append(("inspect", client, namespace, inventory_row, progress))
        return NamespaceInspectionResult(
            report={"namespace": namespace, "workloads": []},
            timings=NamespaceInspectionTimings(),
            metrics=NamespaceInspectionMetrics(),
        )

    def fake_write_lightweight_report(args, *, namespace, report, reports_dir):
        calls.append(("report", namespace, report, reports_dir))

    def fake_write_namespace_report_state(**kwargs):
        calls.append(("state", kwargs))
        return [tmp_path / "Inventory" / "clusters" / "cluster-a" / "state" / "namespaces" / "api-prod.json"]

    monkeypatch.setattr(full_discovery_namespaces, "inspect_live_namespace", fake_inspect_live_namespace)
    monkeypatch.setattr(full_discovery_namespaces, "write_lightweight_report", fake_write_lightweight_report)
    monkeypatch.setattr(full_discovery_namespaces, "write_namespace_report_state", fake_write_namespace_report_state)

    state_files = inspect_and_persist_namespace(
        full_args(tmp_path),
        client=object(),
        namespace="api-prod",
        output_dir=tmp_path / "Inventory",
        cluster="cluster-a",
        reports_dir=tmp_path / "reports",
        inventory_row=None,
        generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
        progress=object(),
    )

    assert state_files == [tmp_path / "Inventory" / "clusters" / "cluster-a" / "state" / "namespaces" / "api-prod.json"]
    assert calls[0][0] == "inspect"
    assert calls[1] == ("report", "api-prod", {"namespace": "api-prod", "workloads": []}, tmp_path / "reports")
    assert calls[2][0] == "state"
    assert calls[2][1]["namespace_row"].namespace == "api-prod"
    assert calls[2][1]["report"] == {"namespace": "api-prod", "workloads": []}
    assert "api-prod:" in capsys.readouterr().err


def test_persist_inspected_namespace_accepts_context_object(monkeypatch, tmp_path):
    def fake_inspect_live_namespace(args, *, client, namespace, inventory_row, progress):
        return NamespaceInspectionResult(
            report={"namespace": namespace, "workloads": []},
            timings=NamespaceInspectionTimings(),
            metrics=NamespaceInspectionMetrics(),
        )

    monkeypatch.setattr(full_discovery_namespaces, "inspect_live_namespace", fake_inspect_live_namespace)
    monkeypatch.setattr(full_discovery_namespaces, "write_lightweight_report", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        full_discovery_namespaces,
        "write_namespace_report_state",
        lambda **kwargs: [tmp_path / "state.json"],
    )

    assert persist_inspected_namespace(
        NamespacePersistenceContext(
            args=full_args(tmp_path),
            client=object(),
            namespace="api-prod",
            output_dir=tmp_path / "Inventory",
            cluster="cluster-a",
            reports_dir=tmp_path / "reports",
            inventory_row=None,
            generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
            progress=object(),
        )
    ) == [tmp_path / "state.json"]


def test_discover_full_inventory_removes_legacy_live_discovery_fragment(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    legacy_file = tmp_path / "Inventory" / "clusters" / "cluster-a" / "fragments" / "live-discovery.json"
    legacy_file.parent.mkdir(parents=True)
    legacy_file.write_text('{"schema_version": 1}', encoding="utf-8")

    class EmptyDiscoveryClient(FakeClient):
        def get_json(self, kind, namespace=None):
            if kind == "namespace":
                return {"items": [{"metadata": {"name": "api-prod"}}]}
            return {"items": []}

    monkeypatch.setattr(full_discovery, "KubectlClient", EmptyDiscoveryClient)

    assert discover_full_inventory(full_args(tmp_path), generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc)) == 0
    assert not legacy_file.exists()


def test_inspect_discovered_namespaces_removes_stale_reports(monkeypatch, tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    stale_report = reports_dir / "stale.report.json"
    stale_report.write_text('{"namespace": "stale", "workloads": []}', encoding="utf-8")
    monkeypatch.setattr(full_discovery, "KubectlClient", FakeClient)

    full_discovery.inspect_discovered_namespaces(
        full_args(tmp_path),
        ["api-prod"],
        output_dir=tmp_path / "Inventory",
        cluster="cluster-a",
        reports_dir=reports_dir,
        inventory_rows=[
            InventoryRow(
                cluster="cluster-a",
                product="demo",
                namespace="api-prod",
                repository="",
                owner_team="",
            )
        ],
        generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
    )

    assert not stale_report.exists()
    assert (reports_dir / "api-prod.report.json").exists()
    assert (tmp_path / "Inventory" / "clusters" / "cluster-a" / "state" / "namespaces" / "api-prod.json").exists()
