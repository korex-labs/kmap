"""Kubernetes access adapter for live inventory discovery."""

from dataclasses import dataclass
from typing import Any

from ..inspection import collect_runtime_env_maps
from ..kubernetes import workload_pods
from ..kubernetes.client import KubectlClient

WORKLOAD_DISCOVERY_KINDS = ("deploy", "sts", "ds")


@dataclass
class LiveNamespaceKubernetes:
    client: KubectlClient

    def workload_resources(self, namespace: str) -> dict[str, dict[str, Any]]:
        return {kind: self.client.get_json(kind, namespace=namespace) for kind in WORKLOAD_DISCOVERY_KINDS}

    def namespace_resource(self, namespace: str, kind: str) -> dict[str, Any]:
        return self.client.get_json(kind, namespace=namespace)

    def runtime_env_maps(
        self,
        *,
        namespace: str,
        pods: dict[str, Any],
        workload: dict[str, Any],
        max_exec_pods_per_workload: int,
        no_exec: bool,
        metrics: dict[str, Any],
    ) -> tuple[dict[str, str], dict[str, str]]:
        return collect_runtime_env_maps(
            client=self.client,
            namespace=namespace,
            pods=workload_pods(pods, workload),
            max_exec_pods_per_workload=max_exec_pods_per_workload,
            no_exec=no_exec,
            **runtime_env_collection_options(metrics),
        )


def runtime_env_collection_options(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "collect_env": False,
        "collect_vault": True,
        "vault_wrapped_only": True,
        "metrics": metrics,
    }
