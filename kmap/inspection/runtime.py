"""Shared runtime environment collection helpers."""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from ..kubernetes import KubectlClient, obj_name


@dataclass(frozen=True)
class RuntimeEnvCollectionContext:
    client: KubectlClient
    namespace: str
    pods: List[Dict[str, Any]]
    max_exec_pods_per_workload: int
    no_exec: bool
    collect_env: bool = True
    collect_vault: bool = True
    vault_wrapped_only: bool = False
    metrics: Dict[str, Any] | None = None


def parse_env_block(raw: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in (raw or "").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            out[key] = value.strip()
    return out


def collect_runtime_env_maps(
    *,
    client: KubectlClient,
    namespace: str,
    pods: List[Dict[str, Any]],
    max_exec_pods_per_workload: int,
    no_exec: bool,
    **collection_options: Any,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    return runtime_env_maps(
        RuntimeEnvCollectionContext(
            client=client,
            namespace=namespace,
            pods=pods,
            max_exec_pods_per_workload=max_exec_pods_per_workload,
            no_exec=no_exec,
            collect_env=collection_options.get("collect_env", True),
            collect_vault=collection_options.get("collect_vault", True),
            vault_wrapped_only=collection_options.get("vault_wrapped_only", False),
            metrics=collection_options.get("metrics"),
        )
    )


def runtime_env_maps(context: RuntimeEnvCollectionContext) -> Tuple[Dict[str, str], Dict[str, str]]:
    runtime_env: Dict[str, str] = {}
    vault_env: Dict[str, str] = {}
    if context.no_exec:
        return runtime_env, vault_env

    for pod_obj in select_runtime_pods(context.pods, context.max_exec_pods_per_workload):
        pod_name = obj_name(pod_obj)
        for container in pod_runtime_containers(pod_obj):
            container_name = container.get("name")
            if context.collect_env:
                runtime_env.update(
                    exec_env_map(context.client, context.namespace, pod_name, container_name, context.metrics)
                )
            if context.collect_vault and (not context.vault_wrapped_only or container_uses_vault_env(container)):
                vault_env.update(
                    exec_vault_env_map(context.client, context.namespace, pod_name, container_name, context.metrics)
                )

    return runtime_env, vault_env


def exec_env_map(
    client: KubectlClient,
    namespace: str,
    pod_name: str,
    container_name: str,
    metrics: Dict[str, Any] | None,
) -> Dict[str, str]:
    increment_metric(metrics, "env_execs")
    start = time.perf_counter()
    raw_env = client.exec_capture(namespace, pod_name, container_name, ["env"])
    increment_metric(metrics, "env_exec_seconds", time.perf_counter() - start)
    return parse_env_block(raw_env)


def exec_vault_env_map(
    client: KubectlClient,
    namespace: str,
    pod_name: str,
    container_name: str,
    metrics: Dict[str, Any] | None,
) -> Dict[str, str]:
    increment_metric(metrics, "vault_execs")
    start = time.perf_counter()
    raw_vault = client.exec_capture(
        namespace,
        pod_name,
        container_name,
        ["/vault/vault-env", "env"],
        report_failure=False,
    )
    increment_metric(metrics, "vault_exec_seconds", time.perf_counter() - start)
    return parse_env_block(raw_vault)


def pod_runtime_containers(pod: Dict[str, Any]) -> List[Dict[str, Any]]:
    pod_spec = pod.get("spec") or {}
    return [
        container
        for container in pod_spec.get("containers") or []
        if isinstance(container, dict) and container.get("name")
    ]


def increment_metric(metrics: Dict[str, Any] | None, name: str, value: float | int = 1) -> None:
    if metrics is not None:
        metrics[name] = metrics.get(name, 0) + value


def container_uses_vault_env(container: Dict[str, Any]) -> bool:
    command = [str(part) for part in container.get("command") or []]
    args = [str(part) for part in container.get("args") or []]
    env_names = [str(item.get("name") or "") for item in container.get("env") or [] if isinstance(item, dict)]
    return any("vault-env" in value or value.startswith("VAULT_") for value in [*command, *args, *env_names])


def select_runtime_pods(pods: List[Dict[str, Any]], max_pods: int) -> List[Dict[str, Any]]:
    return sorted(pods or [], key=runtime_pod_sort_key)[: max(1, max_pods)]


def runtime_pod_sort_key(pod: Dict[str, Any]) -> Tuple[int, int, int, str]:
    metadata = pod.get("metadata") or {}
    status = pod.get("status") or {}
    phase = str(status.get("phase") or "")
    deleting = bool(metadata.get("deletionTimestamp"))
    ready = pod_is_ready(pod)
    return (1 if deleting else 0, 0 if phase == "Running" else 1, 0 if ready else 1, str(metadata.get("name") or ""))


def pod_is_ready(pod: Dict[str, Any]) -> bool:
    conditions = (pod.get("status") or {}).get("conditions") or []
    return any(
        condition.get("type") == "Ready" and condition.get("status") == "True"
        for condition in conditions
        if isinstance(condition, dict)
    )


__all__ = [
    "RuntimeEnvCollectionContext",
    "collect_runtime_env_maps",
    "container_uses_vault_env",
    "exec_env_map",
    "exec_vault_env_map",
    "increment_metric",
    "parse_env_block",
    "pod_is_ready",
    "pod_runtime_containers",
    "runtime_env_maps",
    "runtime_pod_sort_key",
    "select_runtime_pods",
]
