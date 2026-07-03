"""Kubernetes client helpers for full inventory discovery."""

import argparse
from dataclasses import dataclass
from typing import Any

from ..kubernetes.client import KubectlClient


@dataclass(frozen=True)
class ClusterNamespaceInventory:
    namespaces: list[str]
    labels_by_namespace: dict[str, dict[str, str]]


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
    return discover_cluster_namespace_inventory(args, client_class=client_class).namespaces


def discover_cluster_namespace_labels(
    args: argparse.Namespace, *, client_class: type[KubectlClient] = KubectlClient
) -> dict[str, dict[str, str]]:
    return discover_cluster_namespace_inventory(args, client_class=client_class).labels_by_namespace


def discover_cluster_namespace_inventory(
    args: argparse.Namespace, *, client_class: type[KubectlClient] = KubectlClient
) -> ClusterNamespaceInventory:
    return namespace_inventory_from_items(discover_cluster_namespace_items(args, client_class=client_class))


def discover_cluster_namespace_items(
    args: argparse.Namespace, *, client_class: type[KubectlClient] = KubectlClient
) -> list[dict[str, Any]]:
    client = cluster_kubectl_client(args, client_class=client_class)
    ok, message = client.check_reachable()
    if not ok:
        raise SystemExit(
            "Kubernetes discovery preflight failed. "
            "Check VPN/DNS, kubeconfig path, and selected context before retrying.\n"
            f"- {client.cluster_label()}: {message}"
        )
    namespaces = client.get_json("namespace", namespace="")
    return [item for item in namespaces.get("items") or [] if isinstance(item, dict)]


def namespace_item_name(item: dict[str, Any]) -> str:
    return str((item.get("metadata") or {}).get("name") or "")


def namespace_item_labels(item: dict[str, Any]) -> dict[str, str]:
    labels = (item.get("metadata") or {}).get("labels") or {}
    if not isinstance(labels, dict):
        return {}
    return {str(key): str(value or "") for key, value in labels.items() if str(key)}


def namespace_inventory_from_items(items: list[dict[str, Any]]) -> ClusterNamespaceInventory:
    namespaces: list[str] = []
    labels_by_namespace: dict[str, dict[str, str]] = {}
    for item in items:
        name = namespace_item_name(item)
        if not name:
            continue
        namespaces.append(name)
        labels = namespace_item_labels(item)
        if labels:
            labels_by_namespace[name] = labels
    return ClusterNamespaceInventory(
        namespaces=sorted(namespaces),
        labels_by_namespace=labels_by_namespace,
    )


__all__ = [
    "ClusterNamespaceInventory",
    "cluster_kubectl_client",
    "discover_cluster_namespace_inventory",
    "discover_cluster_namespace_items",
    "discover_cluster_namespace_labels",
    "discover_cluster_namespaces",
    "namespace_inventory_from_items",
    "namespace_item_labels",
    "namespace_item_name",
]
