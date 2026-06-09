from kmap.inventory.live_kubernetes import LiveNamespaceKubernetes, runtime_env_collection_options


def test_live_namespace_kubernetes_fetches_workload_resources():
    calls = []

    class FakeClient:
        def get_json(self, kind, namespace=None):
            calls.append((kind, namespace))
            return {"items": [{"kind": kind}]}

    resources = LiveNamespaceKubernetes(FakeClient()).workload_resources("payments")

    assert list(resources) == ["deploy", "sts", "ds"]
    assert calls == [("deploy", "payments"), ("sts", "payments"), ("ds", "payments")]


def test_live_namespace_kubernetes_fetches_namespace_resource():
    class FakeClient:
        def get_json(self, kind, namespace=None):
            return {"items": [{"kind": kind, "namespace": namespace}]}

    assert LiveNamespaceKubernetes(FakeClient()).namespace_resource("payments", "cm") == {
        "items": [{"kind": "cm", "namespace": "payments"}]
    }


def test_live_namespace_kubernetes_collects_vault_runtime_env_for_matching_pods():
    calls = []

    class FakeClient:
        def exec_capture(self, namespace, pod, container, argv, **kwargs):
            calls.append((namespace, pod, container, tuple(argv), kwargs))
            return "S3_BUCKET=reports\n"

    pods = {
        "items": [
            {
                "metadata": {"name": "api-abc", "labels": {"app": "api"}},
                "spec": {"containers": [{"name": "app", "command": ["/vault/vault-env"]}]},
                "status": {"phase": "Running", "conditions": [{"type": "Ready", "status": "True"}]},
            }
        ]
    }
    workload = {
        "metadata": {"name": "api"},
        "spec": {"selector": {"matchLabels": {"app": "api"}}},
    }
    metrics = {}

    runtime_env, vault_env = LiveNamespaceKubernetes(FakeClient()).runtime_env_maps(
        namespace="payments",
        pods=pods,
        workload=workload,
        max_exec_pods_per_workload=1,
        no_exec=False,
        metrics=metrics,
    )

    assert runtime_env == {}
    assert vault_env == {"S3_BUCKET": "reports"}
    assert calls == [("payments", "api-abc", "app", ("/vault/vault-env", "env"), {"report_failure": False})]
    assert metrics["vault_execs"] == 1


def test_runtime_env_collection_options_collects_only_vault_wrapped_env():
    metrics = {}

    assert runtime_env_collection_options(metrics) == {
        "collect_env": False,
        "collect_vault": True,
        "vault_wrapped_only": True,
        "metrics": metrics,
    }
