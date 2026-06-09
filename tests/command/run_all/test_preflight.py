from argparse import Namespace
from types import SimpleNamespace

from kmap.command.run_all.preflight import distinct_discovery_targets, first_failure_line, preflight_run_all_targets


def test_distinct_discovery_targets_deduplicates_same_cluster():
    targets = [
        SimpleNamespace(discovery={"context": "shared", "kubeconfig": "/clusters/a.yaml"}),
        SimpleNamespace(discovery={"context": "shared", "kubeconfig": "/clusters/a.yaml"}),
        SimpleNamespace(discovery={"context": "other", "kubeconfig": "/clusters/a.yaml"}),
    ]

    assert distinct_discovery_targets(targets) == [
        {"context": "shared", "kubeconfig": "/clusters/a.yaml"},
        {"context": "other", "kubeconfig": "/clusters/a.yaml"},
    ]


def test_first_failure_line_uses_first_non_empty_line():
    assert first_failure_line("\n  first\nsecond") == "first"


def test_preflight_skips_when_disabled(monkeypatch):
    calls = []

    class FakeKubectlClient:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr("kmap.command.run_all.preflight.KubectlClient", FakeKubectlClient)

    rc = preflight_run_all_targets(Namespace(cluster_preflight=False), [SimpleNamespace(discovery={})])

    assert rc == 0
    assert calls == []


def test_preflight_checks_each_cluster_once(monkeypatch):
    checked = []

    class FakeKubectlClient:
        def __init__(self, **kwargs):
            self.context = kwargs["context"]

        def check_reachable(self):
            checked.append(self.context)
            return True, ""

        def cluster_label(self):
            return f"context={self.context}"

    monkeypatch.setattr("kmap.command.run_all.preflight.KubectlClient", FakeKubectlClient)
    args = Namespace(
        cluster_preflight=True,
        kubectl="kubectl",
        helm="helm",
        kubeconfig="",
        request_timeout="15s",
    )
    targets = [
        SimpleNamespace(discovery={"context": "shared"}),
        SimpleNamespace(discovery={"context": "shared"}),
        SimpleNamespace(discovery={"context": "other"}),
    ]

    assert preflight_run_all_targets(args, targets) == 0
    assert checked == ["shared", "other"]


def test_preflight_failure_stops_with_useful_message(monkeypatch, capsys):
    class FakeKubectlClient:
        def __init__(self, **kwargs):
            self.context = kwargs["context"]

        def check_reachable(self):
            return False, "Unable to connect to the server\nextra noise"

        def cluster_label(self):
            return f"context={self.context}"

    monkeypatch.setattr("kmap.command.run_all.preflight.KubectlClient", FakeKubectlClient)
    args = Namespace(
        cluster_preflight=True,
        kubectl="kubectl",
        helm="helm",
        kubeconfig="",
        request_timeout="15s",
    )

    rc = preflight_run_all_targets(args, [SimpleNamespace(discovery={"context": "missing-vpn"})])

    assert rc == 1
    captured = capsys.readouterr()
    assert "Kubernetes preflight failed" in captured.err
    assert "Check VPN/DNS" in captured.err
    assert "context=missing-vpn: Unable to connect to the server" in captured.err
