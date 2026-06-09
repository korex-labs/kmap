"""Live namespace inspection for full inventory discovery."""

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import slug_name
from ..inspection.sanitization import sanitize_report_for_persistence
from ..io import dump_json
from ..kubernetes import item_map
from ..kubernetes.client import KubectlClient
from ..logging import ProgressBar
from .full_progress import NamespaceInspectionMetrics, NamespaceInspectionTimings, update_progress
from .live_kubernetes import LiveNamespaceKubernetes
from .live_namespace_resources import (
    fetch_optional_namespace_resource,
    lightweight_namespace_payload,
    optional_namespace_resources,
)
from .live_namespace_workloads import (
    LightweightWorkloadContext,
    SelectedWorkload,
    lightweight_workload_context,
    lightweight_workload_entry,
    referenced_names,
    selected_namespace_workloads,
)
from .namespaces import InventoryRow


@dataclass
class NamespaceInspectionResult:
    report: dict[str, Any]
    timings: NamespaceInspectionTimings
    metrics: NamespaceInspectionMetrics


def inspect_live_namespace(
    args: argparse.Namespace,
    *,
    client: KubectlClient,
    namespace: str,
    inventory_row: InventoryRow | None,
    progress: ProgressBar | None = None,
) -> NamespaceInspectionResult:
    timings = NamespaceInspectionTimings()
    metrics = NamespaceInspectionMetrics()
    report = lightweight_namespace_report(
        args,
        kubernetes=LiveNamespaceKubernetes(client),
        namespace=namespace,
        inventory_row=inventory_row,
        timings=timings,
        metrics=metrics,
        progress=progress,
    )
    return NamespaceInspectionResult(report=report, timings=timings, metrics=metrics)


def lightweight_namespace_report(
    args: argparse.Namespace,
    *,
    kubernetes: LiveNamespaceKubernetes,
    namespace: str,
    inventory_row: InventoryRow | None,
    timings: NamespaceInspectionTimings | None = None,
    metrics: NamespaceInspectionMetrics | None = None,
    progress: ProgressBar | None = None,
) -> dict[str, Any]:
    timings = timings or NamespaceInspectionTimings()
    metrics = metrics or NamespaceInspectionMetrics()
    total_start = time.perf_counter()
    resources: dict[str, dict[str, Any]] = {}
    phase_start = time.perf_counter()
    update_progress(progress, namespace, "fetch workloads")
    resources.update(kubernetes.workload_resources(namespace))
    timings.record("workloads", time.perf_counter() - phase_start)

    selected_workloads = selected_namespace_workloads(args, namespace=namespace, resources=resources)
    referenced_configmaps = referenced_names(selected_workloads, "referenced_configmaps")
    referenced_secrets = referenced_names(selected_workloads, "referenced_secrets")
    resources.update(
        optional_namespace_resources(
            args,
            kubernetes=kubernetes,
            namespace=namespace,
            selected_workloads=selected_workloads,
            referenced_configmaps=referenced_configmaps,
            referenced_secrets=referenced_secrets,
            timings=timings,
            progress=progress,
        )
    )

    configmaps = item_map(resources["cm"])
    secrets = item_map(resources["secret"])
    update_progress(progress, namespace, "inspect workloads")
    workloads = lightweight_workload_entries(
        args,
        namespace=namespace,
        selected_workloads=selected_workloads,
        configmaps=configmaps,
        secrets=secrets,
        pods=resources.get("pod", {}),
        kubernetes=kubernetes,
        inventory_row=inventory_row,
        metrics=metrics,
        progress=progress,
    )
    timings.record("total", time.perf_counter() - total_start)
    metrics.workloads = len(workloads)
    return lightweight_namespace_payload(args, namespace=namespace, workloads=workloads)


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


def write_lightweight_report(
    args: argparse.Namespace,
    *,
    namespace: str,
    report: dict[str, Any],
    reports_dir: Path,
) -> None:
    persisted = sanitize_report_for_persistence(
        report,
        data_mode=getattr(args, "data_mode", "sanitized"),
        mock_seed=getattr(args, "mock_seed", ""),
    )
    dump_json(reports_dir / f"{slug_name(namespace)}.report.json", persisted)


__all__ = [
    "LightweightWorkloadContext",
    "NamespaceInspectionResult",
    "SelectedWorkload",
    "fetch_optional_namespace_resource",
    "inspect_live_namespace",
    "lightweight_namespace_payload",
    "lightweight_namespace_report",
    "lightweight_workload_context",
    "lightweight_workload_entries",
    "lightweight_workload_entry",
    "optional_namespace_resources",
    "referenced_names",
    "selected_namespace_workloads",
    "write_lightweight_report",
]
