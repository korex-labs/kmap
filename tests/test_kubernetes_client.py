import subprocess

from kmap.kubernetes import client as kubernetes_client
from kmap.kubernetes.client import (
    KubectlClient,
    completed_process_output,
    request_timeout_seconds,
    retryable_exec_failure,
)


def test_kubectl_client_builds_base_command_with_context_and_kubeconfig():
    client = KubectlClient(kubectl="kubectlx", kubeconfig="/tmp/kubeconfig", context="ctx")

    assert client.base() == ["kubectlx", "--kubeconfig", "/tmp/kubeconfig", "--context", "ctx"]


def test_kubectl_client_expands_kubeconfig_home(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))

    client = KubectlClient(kubeconfig="~/.kube/config")

    assert client.kubeconfig == str(tmp_path / ".kube" / "config")


def test_kubectl_client_uses_default_kubeconfig_when_unspecified(monkeypatch):
    monkeypatch.setattr(kubernetes_client, "default_kubeconfig_path", lambda: "/home/me/.kube/config")

    client = KubectlClient(kubectl="kubectlx")

    assert client.base() == ["kubectlx", "--kubeconfig", "/home/me/.kube/config"]


def test_kubectl_client_cluster_label_describes_target():
    client = KubectlClient(kubeconfig="/tmp/kubeconfig", context="ctx")

    assert client.cluster_label() == "context=ctx, kubeconfig=/tmp/kubeconfig"


def test_kubectl_client_check_reachable_uses_version(monkeypatch):
    calls = []

    def fake_run_cmd(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout="{}", stderr="")

    monkeypatch.setattr(kubernetes_client, "run_cmd", fake_run_cmd)
    client = KubectlClient(kubectl="kubectlx", kubeconfig="/tmp/kubeconfig", context="ctx", request_timeout="3s")

    assert client.check_reachable() == (True, "")
    assert calls == [
        (
            [
                "kubectlx",
                "--kubeconfig",
                "/tmp/kubeconfig",
                "--context",
                "ctx",
                "--request-timeout=3s",
                "version",
                "--output=json",
            ],
            {"check": False, "timeout": 10, "progress_failure": False, "progress": False},
        )
    ]


def test_kubectl_client_check_reachable_reports_failure(monkeypatch):
    def fake_run_cmd(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Unable to connect")

    monkeypatch.setattr(kubernetes_client, "run_cmd", fake_run_cmd)
    client = KubectlClient(kubectl="kubectlx", kubeconfig="")

    assert client.check_reachable() == (False, "Unable to connect")


def test_kubectl_client_check_reachable_reports_exception(monkeypatch):
    def fail_run_cmd(cmd, **kwargs):
        raise RuntimeError("kubectl missing")

    monkeypatch.setattr(kubernetes_client, "run_cmd", fail_run_cmd)
    client = KubectlClient(kubectl="kubectlx", kubeconfig="")

    assert client.check_reachable() == (False, "kubectl missing")


def test_completed_process_output_prefers_stderr_then_stdout_then_exit_code():
    assert completed_process_output(subprocess.CompletedProcess(["cmd"], 1, stdout="out", stderr="err")) == "err"
    assert completed_process_output(subprocess.CompletedProcess(["cmd"], 1, stdout="out", stderr="")) == "out"
    assert completed_process_output(subprocess.CompletedProcess(["cmd"], 3, stdout="", stderr="")) == "exit code 3"


def test_kubectl_client_current_context_returns_stdout_or_unknown(monkeypatch):
    calls = []

    def fake_run_cmd(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout="dev-cluster\n", stderr="")

    monkeypatch.setattr(kubernetes_client, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kubernetes_client, "default_kubeconfig_path", lambda: "")

    client = KubectlClient(kubectl="kubectlx")

    assert client.current_context() == "dev-cluster"
    assert calls == [(["kubectlx", "config", "current-context"], {"timeout": 20})]


def test_kubectl_client_current_context_handles_empty_or_failed_command(monkeypatch):
    monkeypatch.setattr(kubernetes_client, "default_kubeconfig_path", lambda: "")
    client = KubectlClient(kubectl="kubectlx")

    monkeypatch.setattr(
        kubernetes_client,
        "run_cmd",
        lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 0, stdout="\n", stderr=""),
    )
    assert client.current_context() == "unknown-context"

    def fail_run_cmd(cmd, **kwargs):
        raise RuntimeError("kubectl unavailable")

    monkeypatch.setattr(kubernetes_client, "run_cmd", fail_run_cmd)
    assert client.current_context() == "unknown-context"


def test_kubectl_client_get_json_uses_namespace_and_decodes_output(monkeypatch):
    calls = []
    sleeps = []

    def fake_run_cmd(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout='{"items": [{"metadata": {"name": "api"}}]}', stderr="")

    monkeypatch.setattr(kubernetes_client, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kubernetes_client.time, "sleep", sleeps.append)
    monkeypatch.setattr(kubernetes_client, "default_kubeconfig_path", lambda: "")
    client = KubectlClient(kubectl="kubectlx", namespace="default", request_timeout="3s", qps_sleep=0.25)

    assert client.get_json("pods") == {"items": [{"metadata": {"name": "api"}}]}
    assert calls == [
        (["kubectlx", "--request-timeout=3s", "get", "pods", "-n", "default", "-o", "json"], {"timeout": 10})
    ]
    assert sleeps == [0.25]


def test_kubectl_client_get_json_returns_empty_items_on_command_failure(monkeypatch):
    def fail_run_cmd(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["kubectl"], stderr="nope")

    monkeypatch.setattr(kubernetes_client, "run_cmd", fail_run_cmd)

    client = KubectlClient(qps_sleep=0)

    assert client.get_json("pods") == {"items": []}


def test_kubectl_client_helm_list_returns_empty_when_helm_missing(monkeypatch):
    monkeypatch.setattr(kubernetes_client.shutil, "which", lambda name: None)

    client = KubectlClient(helm="helmx", kubeconfig="")

    assert client.helm_list("payments") == []


def test_kubectl_client_helm_list_uses_context_and_decodes_output(monkeypatch):
    calls = []

    def fake_run_cmd(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout='[{"name": "api"}]', stderr="")

    monkeypatch.setattr(kubernetes_client.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(kubernetes_client, "run_cmd", fake_run_cmd)
    client = KubectlClient(helm="helmx", kubeconfig="/tmp/kubeconfig", context="ctx")

    assert client.helm_list("payments") == [{"name": "api"}]
    assert calls == [
        (
            [
                "helmx",
                "--kubeconfig",
                "/tmp/kubeconfig",
                "--kube-context",
                "ctx",
                "list",
                "-n",
                "payments",
                "-o",
                "json",
            ],
            {"timeout": 20},
        )
    ]


def test_kubectl_client_helm_list_returns_empty_on_failure(monkeypatch):
    def fail_run_cmd(cmd):
        raise RuntimeError("helm failed")

    monkeypatch.setattr(kubernetes_client.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(kubernetes_client, "run_cmd", fail_run_cmd)
    client = KubectlClient(helm="helmx", kubeconfig="")

    assert client.helm_list("payments") == []


def test_kubectl_client_get_json_returns_empty_items_on_timeout(monkeypatch):
    def timeout_run_cmd(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["kubectl"], timeout=20)

    monkeypatch.setattr(kubernetes_client, "run_cmd", timeout_run_cmd)

    client = KubectlClient(qps_sleep=0)

    assert client.get_json("pods") == {"items": []}


def test_request_timeout_seconds_parses_kubernetes_timeout_values():
    assert request_timeout_seconds("500ms") == 1
    assert request_timeout_seconds("3s") == 3
    assert request_timeout_seconds("2m") == 120
    assert request_timeout_seconds("7") == 7
    assert request_timeout_seconds("bad") == 15


def test_kubectl_exec_places_namespace_after_exec_target(monkeypatch):
    calls = []

    def fake_run_cmd(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="A=B\n", stderr="")

    monkeypatch.setattr(kubernetes_client, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kubernetes_client, "default_kubeconfig_path", lambda: "")
    client = KubectlClient(kubectl="kubectlx", context="ctx")

    assert client.exec_capture("payments", "api-pod", "app", ["env"]) == "A=B"
    assert calls[0] == ["kubectlx", "--context", "ctx", "exec", "api-pod", "-c", "app", "-n", "payments", "--", "env"]


def test_kubectl_exec_retries_failed_exit_before_returning_output(monkeypatch):
    calls = []
    sleeps = []

    def fake_run_cmd(cmd, **kwargs):
        calls.append(cmd)
        if len(calls) == 1:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="pod not ready")
        return subprocess.CompletedProcess(cmd, 0, stdout="A=B\n", stderr="")

    monkeypatch.setattr(kubernetes_client, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kubernetes_client.time, "sleep", sleeps.append)
    client = KubectlClient(exec_sleep=0)

    assert client.exec_capture("payments", "api-pod", "app", ["env"]) == "A=B"
    assert len(calls) == 2
    assert sleeps == [0, 1.0, 0]


def test_kubectl_exec_retries_exceptions_up_to_limit(monkeypatch):
    calls = []
    failed = []
    sleeps = []

    def fake_run_cmd(cmd, **kwargs):
        calls.append(cmd)
        assert kwargs["progress_failure"] is False
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=20)

    monkeypatch.setattr(kubernetes_client, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kubernetes_client, "progress_command_failed", failed.append)
    monkeypatch.setattr(kubernetes_client.time, "sleep", sleeps.append)
    client = KubectlClient(exec_sleep=0)

    assert client.exec_capture("payments", "api-pod", "app", ["env"]) == ""
    assert len(calls) == 3
    assert failed == [calls[0]]
    assert sleeps == [1.0, 1.0]


def test_kubectl_exec_can_suppress_final_failure_reporting(monkeypatch):
    calls = []
    failed = []
    sleeps = []

    def fake_run_cmd(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="pod not ready")

    monkeypatch.setattr(kubernetes_client, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kubernetes_client, "progress_command_failed", failed.append)
    monkeypatch.setattr(kubernetes_client.time, "sleep", sleeps.append)
    client = KubectlClient(exec_sleep=0)

    assert client.exec_capture("payments", "api-pod", "app", ["/vault/vault-env", "env"], report_failure=False) == ""
    assert len(calls) == 3
    assert failed == []


def test_kubectl_exec_does_not_retry_non_retryable_command_failures(monkeypatch):
    calls = []
    failed = []
    sleeps = []

    def fake_run_cmd(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 127, stdout="", stderr="stat /vault/vault-env: no such file")

    monkeypatch.setattr(kubernetes_client, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kubernetes_client, "progress_command_failed", failed.append)
    monkeypatch.setattr(kubernetes_client.time, "sleep", sleeps.append)
    client = KubectlClient(exec_sleep=0)

    assert client.exec_capture("payments", "api-pod", "app", ["/vault/vault-env", "env"]) == ""
    assert len(calls) == 1
    assert calls[0][1]["progress"] is False
    assert failed == []
    assert sleeps == [0]


def test_kubectl_exec_capture_once_returns_single_attempt_output(monkeypatch):
    calls = []

    def fake_run_cmd(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout="ready\n", stderr="")

    monkeypatch.setattr(kubernetes_client, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kubernetes_client.time, "sleep", lambda value: None)
    client = KubectlClient(exec_sleep=0)

    assert client.exec_capture_once(["kubectl", "exec", "pod"]) == "ready"
    assert calls[0][1]["check"] is False


def test_kubectl_exec_uses_configured_attempts_and_timeout(monkeypatch):
    calls = []
    sleeps = []

    def fake_run_cmd(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="pod not ready")

    monkeypatch.setattr(kubernetes_client, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(kubernetes_client, "progress_command_failed", lambda cmd: None)
    monkeypatch.setattr(kubernetes_client.time, "sleep", sleeps.append)
    client = KubectlClient(exec_sleep=0, exec_attempts=1, exec_timeout=5)

    assert client.exec_capture("payments", "api-pod", "app", ["env"]) == ""
    assert len(calls) == 1
    assert calls[0][1]["timeout"] == 5
    assert sleeps == [0]


def test_retryable_exec_failure_classifies_deterministic_command_errors():
    assert not retryable_exec_failure(126, "")
    assert not retryable_exec_failure(127, "executable file not found")
    assert not retryable_exec_failure(1, "stat /vault/vault-env: no such file or directory")
    assert not retryable_exec_failure(1, "not found in $PATH")
    assert retryable_exec_failure(1, "pod not ready")
