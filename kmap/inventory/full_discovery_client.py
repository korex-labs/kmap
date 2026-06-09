"""Kubernetes client helpers for full inventory discovery."""

import argparse
from typing import Any

from ..kubernetes.client import KubectlClient


def cluster_kubectl_client(
    args: argparse.Namespace,
    *,
    exec_timeout: int | None = None,
    exec_attempts: int | None = None,
    client_class: type[KubectlClient] = KubectlClient,
) -> KubectlClient:
    kwargs: dict[str, Any] = {
        "kubectl": args.kubectl,
        "helm": args.helm,
        "context": args.cluster,
        "kubeconfig": getattr(args, "kubeconfig", ""),
        "request_timeout": args.request_timeout,
        "qps_sleep": args.kubectl_qps_sleep,
        "exec_sleep": args.exec_sleep,
    }
    if exec_timeout is not None:
        kwargs["exec_timeout"] = exec_timeout
    if exec_attempts is not None:
        kwargs["exec_attempts"] = exec_attempts
    return client_class(**kwargs)


def discover_cluster_namespaces(
    args: argparse.Namespace, *, client_class: type[KubectlClient] = KubectlClient
) -> list[str]:
    client = cluster_kubectl_client(args, client_class=client_class)
    ok, message = client.check_reachable()
    if not ok:
        raise SystemExit(
            "Kubernetes discovery preflight failed. "
            "Check VPN/DNS, kubeconfig path, and selected context before retrying.\n"
            f"- {client.cluster_label()}: {message}"
        )
    namespaces = client.get_json("namespace", namespace="")
    return sorted(
        str(item.get("metadata", {}).get("name") or "")
        for item in namespaces.get("items") or []
        if str(item.get("metadata", {}).get("name") or "")
    )


__all__ = ["cluster_kubectl_client", "discover_cluster_namespaces"]
