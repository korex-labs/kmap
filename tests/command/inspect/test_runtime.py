from kmap.inspection.runtime import (
    RuntimeEnvCollectionContext,
    collect_runtime_env_maps,
    container_uses_vault_env,
    exec_env_map,
    exec_vault_env_map,
    pod_is_ready,
    pod_runtime_containers,
    runtime_env_maps,
    select_runtime_pods,
)


def test_collect_runtime_env_maps_runs_env_and_vault_env_for_selected_pods():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def exec_capture(self, namespace, pod, container, argv, **kwargs):
            self.calls.append((namespace, pod, container, tuple(argv)))
            if argv == ["env"]:
                return f"RUNTIME_URL=https://{pod}-{container}.example.com\n"
            return f"VAULT_URL=https://vault-{pod}-{container}.example.com\n"

    client = FakeClient()
    metrics = {}
    runtime_env, vault_env = collect_runtime_env_maps(
        client=client,
        namespace="payments",
        pods=[
            {"metadata": {"name": "pod-a"}, "spec": {"containers": [{"name": "app"}, {"name": "sidecar"}]}},
            {"metadata": {"name": "pod-b"}, "spec": {"containers": [{"name": "app"}]}},
        ],
        max_exec_pods_per_workload=1,
        no_exec=False,
        metrics=metrics,
    )

    assert runtime_env == {"RUNTIME_URL": "https://pod-a-sidecar.example.com"}
    assert vault_env == {"VAULT_URL": "https://vault-pod-a-sidecar.example.com"}
    assert client.calls == [
        ("payments", "pod-a", "app", ("env",)),
        ("payments", "pod-a", "app", ("/vault/vault-env", "env")),
        ("payments", "pod-a", "sidecar", ("env",)),
        ("payments", "pod-a", "sidecar", ("/vault/vault-env", "env")),
    ]
    assert metrics["env_execs"] == 2
    assert metrics["vault_execs"] == 2
    assert metrics["env_exec_seconds"] >= 0
    assert metrics["vault_exec_seconds"] >= 0


def test_runtime_env_maps_accepts_context_object():
    class FakeClient:
        def exec_capture(self, namespace, pod, container, argv, **kwargs):
            assert namespace == "payments"
            assert pod == "pod-a"
            assert container == "app"
            assert argv == ["env"]
            return "RUNTIME_URL=https://runtime.example.com\n"

    assert runtime_env_maps(
        RuntimeEnvCollectionContext(
            client=FakeClient(),
            namespace="payments",
            pods=[{"metadata": {"name": "pod-a"}, "spec": {"containers": [{"name": "app"}]}}],
            max_exec_pods_per_workload=1,
            no_exec=False,
            collect_vault=False,
        )
    ) == ({"RUNTIME_URL": "https://runtime.example.com"}, {})


def test_collect_runtime_env_maps_skips_exec_when_disabled():
    class FakeClient:
        def exec_capture(self, namespace, pod, container, argv):
            raise AssertionError("exec_capture should not be called")

    assert collect_runtime_env_maps(
        client=FakeClient(),
        namespace="payments",
        pods=[{"metadata": {"name": "pod-a"}, "spec": {"containers": [{"name": "app"}]}}],
        max_exec_pods_per_workload=1,
        no_exec=True,
    ) == ({}, {})


def test_collect_runtime_env_maps_runs_vault_env_as_quiet_best_effort():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def exec_capture(self, namespace, pod, container, argv, **kwargs):
            self.calls.append((namespace, pod, container, tuple(argv), kwargs))
            return ""

    client = FakeClient()

    assert collect_runtime_env_maps(
        client=client,
        namespace="payments",
        pods=[{"metadata": {"name": "pod-a"}, "spec": {"containers": [{"name": "app"}]}}],
        max_exec_pods_per_workload=1,
        no_exec=False,
    ) == ({}, {})
    assert client.calls == [
        ("payments", "pod-a", "app", ("env",), {}),
        ("payments", "pod-a", "app", ("/vault/vault-env", "env"), {"report_failure": False}),
    ]


def test_collect_runtime_env_maps_can_collect_vault_only_for_wrapped_containers():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def exec_capture(self, namespace, pod, container, argv, **kwargs):
            self.calls.append((namespace, pod, container, tuple(argv), kwargs))
            return "S3_BUCKET=reports\n"

    client = FakeClient()

    assert collect_runtime_env_maps(
        client=client,
        namespace="payments",
        pods=[
            {
                "metadata": {"name": "pod-a"},
                "spec": {
                    "containers": [
                        {"name": "app", "command": ["/vault/vault-env"]},
                        {"name": "sidecar", "command": ["/bin/app"]},
                    ]
                },
            }
        ],
        max_exec_pods_per_workload=1,
        no_exec=False,
        collect_env=False,
        collect_vault=True,
        vault_wrapped_only=True,
    ) == ({}, {"S3_BUCKET": "reports"})
    assert client.calls == [("payments", "pod-a", "app", ("/vault/vault-env", "env"), {"report_failure": False})]


def test_exec_env_helpers_parse_output_and_update_metrics():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def exec_capture(self, namespace, pod, container, argv, **kwargs):
            self.calls.append((namespace, pod, container, tuple(argv), kwargs))
            return "A=1\nB=2\n"

    metrics = {}
    client = FakeClient()

    assert exec_env_map(client, "payments", "pod-a", "app", metrics) == {"A": "1", "B": "2"}
    assert exec_vault_env_map(client, "payments", "pod-a", "app", metrics) == {"A": "1", "B": "2"}
    assert client.calls == [
        ("payments", "pod-a", "app", ("env",), {}),
        ("payments", "pod-a", "app", ("/vault/vault-env", "env"), {"report_failure": False}),
    ]
    assert metrics["env_execs"] == 1
    assert metrics["vault_execs"] == 1
    assert metrics["env_exec_seconds"] >= 0
    assert metrics["vault_exec_seconds"] >= 0


def test_container_uses_vault_env_checks_command_args_and_env_names():
    assert container_uses_vault_env({"command": ["/vault/vault-env"]})
    assert container_uses_vault_env({"args": ["vault-env"]})
    assert container_uses_vault_env({"env": [{"name": "VAULT_ADDR"}]})
    assert not container_uses_vault_env({"command": ["/app"], "env": [{"name": "APP_ENV"}]})


def test_pod_runtime_containers_keeps_named_container_dicts_only():
    app = {"name": "app"}
    sidecar = {"name": "sidecar"}

    assert pod_runtime_containers({"spec": {"containers": [app, {}, "bad", sidecar]}}) == [app, sidecar]
    assert pod_runtime_containers({}) == []


def test_select_runtime_pods_prefers_running_ready_non_deleting_pods():
    pods = [
        {
            "metadata": {"name": "terminating", "deletionTimestamp": "2026-05-13T10:00:00Z"},
            "status": {"phase": "Running", "conditions": [{"type": "Ready", "status": "True"}]},
        },
        {
            "metadata": {"name": "pending"},
            "status": {"phase": "Pending", "conditions": [{"type": "Ready", "status": "False"}]},
        },
        {
            "metadata": {"name": "ready-b"},
            "status": {"phase": "Running", "conditions": [{"type": "Ready", "status": "True"}]},
        },
        {
            "metadata": {"name": "ready-a"},
            "status": {"phase": "Running", "conditions": [{"type": "Ready", "status": "True"}]},
        },
        {
            "metadata": {"name": "not-ready"},
            "status": {"phase": "Running", "conditions": [{"type": "Ready", "status": "False"}]},
        },
        {
            "metadata": {"name": "deleting", "deletionTimestamp": "2026-05-13T10:00:00Z"},
            "status": {"phase": "Running", "conditions": [{"type": "Ready", "status": "True"}]},
        },
    ]

    assert [pod["metadata"]["name"] for pod in select_runtime_pods(pods, 3)] == [
        "ready-a",
        "ready-b",
        "not-ready",
    ]


def test_pod_is_ready_checks_ready_condition():
    assert pod_is_ready({"status": {"conditions": [{"type": "Ready", "status": "True"}]}})
    assert not pod_is_ready({"status": {"conditions": [{"type": "Ready", "status": "False"}]}})
    assert not pod_is_ready({"status": {"conditions": [{"type": "Initialized", "status": "True"}]}})
