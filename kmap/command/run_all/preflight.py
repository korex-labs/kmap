"""Cluster reachability checks for run-all."""

import argparse

from ...kubernetes.client import KubectlClient
from ...logging import eprint
from .discovery import discovery_target_identity


def preflight_run_all_targets(args: argparse.Namespace, targets: list) -> int:
    if not getattr(args, "cluster_preflight", False):
        return 0

    failures = preflight_failures(args, distinct_discovery_targets(targets))
    if not failures:
        return 0

    print_preflight_failures(failures)
    return 1


def preflight_failures(args: argparse.Namespace, discovery_targets: list[dict]) -> list[tuple[str, str]]:
    failures = []
    for target in discovery_targets:
        client = preflight_client(args, target)
        reachable, message = client.check_reachable()
        if not reachable:
            failures.append((client.cluster_label(), first_failure_line(message)))
    return failures


def preflight_client(args: argparse.Namespace, target: dict) -> KubectlClient:
    return KubectlClient(
        kubectl=getattr(args, "kubectl", "kubectl"),
        helm=getattr(args, "helm", "helm"),
        context=target.get("context") or None,
        kubeconfig=target.get("kubeconfig") or getattr(args, "kubeconfig", "") or None,
        request_timeout=getattr(args, "request_timeout", "15s"),
        qps_sleep=0,
        exec_sleep=0,
    )


def print_preflight_failures(failures: list[tuple[str, str]]) -> None:
    eprint("[kmap] Kubernetes preflight failed; run-all stopped before namespace inspection.")
    eprint("[kmap] Check VPN/DNS, kubeconfig path, and selected context before retrying.")
    for label, message in failures:
        detail = f": {message}" if message else ""
        eprint(f"- {label}{detail}")


def distinct_discovery_targets(targets: list) -> list[dict]:
    seen = set()
    out = []
    for target in targets:
        discovery = getattr(target, "discovery", {}) or {}
        identity = discovery_target_identity(discovery) or "__default__"
        if identity in seen:
            continue
        seen.add(identity)
        out.append(discovery)
    return out


def first_failure_line(message: str) -> str:
    for raw_line in (message or "").splitlines():
        line = raw_line.strip()
        if line:
            return line
    return ""


__all__ = [
    "distinct_discovery_targets",
    "first_failure_line",
    "preflight_client",
    "preflight_failures",
    "preflight_run_all_targets",
    "print_preflight_failures",
]
