"""Lightweight workload entries for live namespace inventory."""

import argparse
import re
from dataclasses import dataclass, field
from typing import Any

from ..inspection import workload_bucket_candidates, workload_container_context
from ..inspection.workloads import select_workloads
from ..kubernetes import obj_name
from ..logging import ProgressBar
from .full_progress import NamespaceInspectionMetrics, update_progress
from .live_kubernetes import LiveNamespaceKubernetes
from .namespaces import InventoryRow


@dataclass
class SelectedWorkload:
    kind: str
    workload: dict[str, Any]
    container_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LightweightWorkloadContext:
    pods: dict[str, Any]
    kubernetes: LiveNamespaceKubernetes
    inventory_row: InventoryRow | None
    metrics: NamespaceInspectionMetrics
    progress: ProgressBar | None = None


def selected_namespace_workloads(
    args: argparse.Namespace,
    *,
    namespace: str,
    resources: dict[str, dict[str, Any]],
) -> list[SelectedWorkload]:
    selected_workloads, _ = select_workloads(
        deployments=resources["deploy"],
        statefulsets=resources["sts"],
        daemonsets=resources["ds"],
        match_re=re.compile(args.match_regex),
        match_regex=args.match_regex,
        namespace=namespace,
    )
    return [
        SelectedWorkload(kind=kind, workload=workload, container_context=workload_container_context(workload))
        for kind, workload in selected_workloads
    ]


def lightweight_workload_entry(
    args: argparse.Namespace,
    *,
    namespace: str,
    selected: SelectedWorkload,
    configmaps: dict[str, dict[str, Any]],
    secrets: dict[str, dict[str, Any]],
    **workload_options: Any,
) -> dict[str, Any]:
    workload_context = lightweight_workload_context(workload_options)
    referenced_configmaps = selected.container_context["referenced_configmaps"]
    referenced_secrets = selected.container_context["referenced_secrets"]
    update_progress(workload_context.progress, namespace, f"scan {selected.kind}/{obj_name(selected.workload)}")
    runtime_env, vault_env = workload_context.kubernetes.runtime_env_maps(
        namespace=namespace,
        pods=workload_context.pods,
        workload=selected.workload,
        max_exec_pods_per_workload=args.max_exec_pods_per_workload,
        no_exec=args.no_exec,
        metrics=workload_context.metrics.runtime,
    )
    return {
        "cluster": args.cluster,
        "namespace": namespace,
        "project": workload_context.inventory_row.product if workload_context.inventory_row else "",
        "kind": selected.kind,
        "service_name": obj_name(selected.workload),
        "containers": selected.container_context["inventory"],
        "referenced_configmaps": sorted(referenced_configmaps),
        "referenced_secrets": sorted(referenced_secrets),
        "runtime": {},
        "dependency_candidates": [],
        "bucket_candidates": workload_bucket_candidates(
            containers=selected.container_context["containers"],
            referenced_configmaps=referenced_configmaps,
            referenced_secrets=referenced_secrets,
            configmaps=configmaps,
            secrets=secrets,
            runtime_env=runtime_env,
            vault_env=vault_env,
        ),
    }


def lightweight_workload_context(workload_options: dict[str, Any]) -> LightweightWorkloadContext:
    context = workload_options.get("workload_context")
    if isinstance(context, LightweightWorkloadContext):
        return context
    return LightweightWorkloadContext(
        pods=workload_options["pods"],
        kubernetes=workload_options["kubernetes"],
        inventory_row=workload_options.get("inventory_row"),
        metrics=workload_options["metrics"],
        progress=workload_options.get("progress"),
    )


def lightweight_workload_entries(
    args: argparse.Namespace,
    *,
    namespace: str,
    selected_workloads: list[SelectedWorkload],
    configmaps: dict[str, dict[str, Any]],
    secrets: dict[str, dict[str, Any]],
    **workload_options: Any,
) -> list[dict[str, Any]]:
    return [
        lightweight_workload_entry(
            args,
            namespace=namespace,
            selected=selected,
            configmaps=configmaps,
            secrets=secrets,
            **workload_options,
        )
        for selected in selected_workloads
    ]


def referenced_names(workloads: list[SelectedWorkload], key: str) -> set[str]:
    names: set[str] = set()
    for selected in workloads:
        names.update(selected.container_context[key])
    return names


__all__ = [
    "LightweightWorkloadContext",
    "SelectedWorkload",
    "lightweight_workload_context",
    "lightweight_workload_entries",
    "lightweight_workload_entry",
    "referenced_names",
    "selected_namespace_workloads",
]
