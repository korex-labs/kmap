import json
from argparse import Namespace

from kmap.command import inspect as command_inspect_module
from kmap.command.inspect import namespace_context as namespace_context_module


def _inspect_args(tmp_path, **overrides):
    values = {
        "kubectl": "kubectl",
        "helm": "helm",
        "context": "",
        "kubeconfig": "",
        "namespace": "payments",
        "out_dir": str(tmp_path),
        "request_timeout": "15s",
        "kubectl_qps_sleep": 0,
        "exec_sleep": 0,
        "match_regex": "main",
        "no_exec": True,
        "max_exec_pods_per_workload": 1,
        "format": "json",
        "data_mode": "raw",
        "mock_seed": "",
        "project": "pay",
    }
    values.update(overrides)
    return Namespace(**values)


def test_inspect_namespace_writes_json_report_without_kubectl(monkeypatch, tmp_path):
    class FakeClient:
        def __init__(self, **kwargs):
            self.namespace = kwargs["namespace"]

        def current_context(self):
            return "ctx"

        def get_json(self, kind):
            if kind == "deploy":
                return {
                    "items": [
                        {
                            "metadata": {"name": "api-main"},
                            "spec": {
                                "selector": {"matchLabels": {"app": "api"}},
                                "template": {
                                    "metadata": {"labels": {"app": "api"}},
                                    "spec": {
                                        "containers": [
                                            {
                                                "name": "app",
                                                "image": "example/api:1",
                                                "env": [{"name": "API_URL", "value": "https://api.example.com"}],
                                            }
                                        ]
                                    },
                                },
                            },
                        }
                    ]
                }
            if kind == "svc":
                return {
                    "items": [
                        {
                            "metadata": {"name": "api"},
                            "spec": {"selector": {"app": "api"}, "ports": [{"port": 80}]},
                        }
                    ]
                }
            return {"items": []}

        def helm_list(self, namespace):
            return [{"name": "api-main"}]

        def exec_capture(self, namespace, pod, container, argv, **kwargs):
            return ""

    monkeypatch.setattr(namespace_context_module, "KubectlClient", FakeClient)

    rc = command_inspect_module.inspect_namespace(_inspect_args(tmp_path))

    assert rc == 0
    report = (tmp_path / "payments.report.json").read_text(encoding="utf-8")
    assert '"service_name": "api-main"' in report
    assert '"key": "api.example.com"' in report
    assert '"traffic_routes"' in report


def test_inspect_namespace_handles_missing_ingress_and_writes_text(monkeypatch, tmp_path):
    class FakeClient:
        def __init__(self, **kwargs):
            self.namespace = kwargs["namespace"]

        def current_context(self):
            return "ctx"

        def get_json(self, kind):
            if kind == "ingress":
                raise RuntimeError("ingress api unavailable")
            return {"items": []}

        def helm_list(self, namespace):
            return []

    monkeypatch.setattr(namespace_context_module, "KubectlClient", FakeClient)

    rc = command_inspect_module.inspect_namespace(_inspect_args(tmp_path, format="text"))

    assert rc == 0
    assert (tmp_path / "payments.report.txt").is_file()
    assert not (tmp_path / "payments.report.json").exists()


def test_inspect_namespace_reuses_previous_runtime_candidates_when_exec_finds_none(monkeypatch, tmp_path):
    previous_report = {
        "cluster": "ctx",
        "namespace": "payments",
        "workloads": [
            {
                "cluster": "ctx",
                "namespace": "payments",
                "kind": "Deployment",
                "service_name": "api-main",
                "dependency_candidates": [
                    {
                        "source": "Env",
                        "source_name": "runtime",
                        "var": "API_URL",
                        "key": "api.example.com",
                        "value": "<redacted>",
                        "value_redacted": True,
                    },
                    {
                        "source": "ConfigMap",
                        "source_name": "app-config",
                        "var": "STATIC_URL",
                        "key": "static.example.com",
                    },
                ],
            }
        ],
    }
    (tmp_path / "payments.report.json").write_text(json.dumps(previous_report), encoding="utf-8")

    class FakeClient:
        def __init__(self, **kwargs):
            self.namespace = kwargs["namespace"]

        def current_context(self):
            return "ctx"

        def get_json(self, kind):
            if kind == "deploy":
                return {
                    "items": [
                        {
                            "metadata": {"name": "api-main"},
                            "spec": {
                                "selector": {"matchLabels": {"app": "api"}},
                                "template": {
                                    "metadata": {"labels": {"app": "api"}},
                                    "spec": {"containers": [{"name": "app", "image": "example/api:1"}]},
                                },
                            },
                        }
                    ]
                }
            if kind == "pod":
                return {
                    "items": [
                        {
                            "metadata": {"name": "api-pod", "labels": {"app": "api"}},
                            "spec": {"containers": [{"name": "app"}]},
                            "status": {"phase": "Running"},
                        }
                    ]
                }
            return {"items": []}

        def helm_list(self, namespace):
            return []

        def exec_capture(self, namespace, pod, container, argv, **kwargs):
            return ""

    monkeypatch.setattr(namespace_context_module, "KubectlClient", FakeClient)

    rc = command_inspect_module.inspect_namespace(_inspect_args(tmp_path, no_exec=False))

    assert rc == 0
    report = json.loads((tmp_path / "payments.report.json").read_text(encoding="utf-8"))
    candidates = report["workloads"][0]["dependency_candidates"]
    assert candidates == [
        {
            "source": "Env",
            "source_name": "runtime",
            "var": "API_URL",
            "key": "api.example.com",
            "value": "<redacted>",
            "value_redacted": True,
            "cache": True,
            "cache_source": "previous_report",
        }
    ]


def test_inspect_namespaces_resolves_targets_and_report_stems(monkeypatch, tmp_path):
    calls = []

    def fake_inspect_namespace(args):
        calls.append(args)
        return 0

    monkeypatch.setattr(command_inspect_module, "inspect_namespace", fake_inspect_namespace)

    rc = command_inspect_module.inspect_namespaces(
        Namespace(
            namespace=["payments-prod, reports-prod"],
            namespace_project=["payments-prod=payments"],
            project="fallback",
            product="demo",
            discovery_config={
                "context": "default-context",
                "namespaces": {"reports-prod": {"context": "reports-context", "kubeconfig": "/tmp/reports.kubeconfig"}},
            },
            kubeconfig="",
            kubectl="kubectl",
            helm="helm",
            out_dir=str(tmp_path),
            request_timeout="15s",
            exec_sleep=0,
            kubectl_qps_sleep=0,
            match_regex="main",
            no_exec=True,
            max_exec_pods_per_workload=1,
            format="json",
            data_mode="raw",
            mock_seed="",
        )
    )

    assert rc == 0
    assert [call.namespace for call in calls] == ["payments-prod", "reports-prod"]
    assert [call.project for call in calls] == ["payments", "fallback"]
    assert calls[0].context == "default-context"
    assert calls[0].report_stem == "default-context__payments-prod"
    assert calls[1].context == "reports-context"
    assert calls[1].kubeconfig == "/tmp/reports.kubeconfig"
    assert calls[1].report_stem.startswith("reports-context-")
    assert calls[1].report_stem.endswith("__reports-prod")


def test_inspect_namespaces_stops_on_first_failure(monkeypatch, tmp_path):
    calls = []

    def fake_inspect_namespace(args):
        calls.append(args.namespace)
        return 7 if args.namespace == "reports-prod" else 0

    monkeypatch.setattr(command_inspect_module, "inspect_namespace", fake_inspect_namespace)

    rc = command_inspect_module.inspect_namespaces(
        Namespace(
            namespace=["payments-prod", "reports-prod", "ignored-prod"],
            namespace_project=[],
            project="",
            product="demo",
            discovery_config={},
            kubeconfig="",
            kubectl="kubectl",
            helm="helm",
            out_dir=str(tmp_path),
            request_timeout="15s",
            exec_sleep=0,
            kubectl_qps_sleep=0,
            match_regex="main",
            no_exec=True,
            max_exec_pods_per_workload=1,
            format="json",
            data_mode="raw",
            mock_seed="",
        )
    )

    assert rc == 7
    assert calls == ["payments-prod", "reports-prod"]
