"""Resource helpers for live namespace inspection."""

import argparse
import time
from typing import Any

from ..logging import ProgressBar
from .full_progress import NamespaceInspectionTimings, update_progress
from .live_kubernetes import LiveNamespaceKubernetes
from .live_namespace_workloads import SelectedWorkload


def optional_namespace_resources(
    args: argparse.Namespace,
    *,
    kubernetes: LiveNamespaceKubernetes,
    namespace: str,
    selected_workloads: list[SelectedWorkload],
    referenced_configmaps: set[str],
    referenced_secrets: set[str],
    timings: NamespaceInspectionTimings,
    progress: ProgressBar | None = None,
) -> dict[str, dict[str, Any]]:
    return {
        "cm": fetch_optional_namespace_resource(
            kubernetes,
            namespace=namespace,
            kind="cm",
            needed=bool(referenced_configmaps),
            timings=timings,
            timing_key="configmaps",
            progress=progress,
            progress_phase="fetch configmaps",
        ),
        "secret": fetch_optional_namespace_resource(
            kubernetes,
            namespace=namespace,
            kind="secret",
            needed=bool(referenced_secrets),
            timings=timings,
            timing_key="secrets",
            progress=progress,
            progress_phase="fetch secrets",
        ),
        "pod": fetch_optional_namespace_resource(
            kubernetes,
            namespace=namespace,
            kind="pod",
            needed=bool(selected_workloads) and not getattr(args, "no_exec", False),
            timings=timings,
            timing_key="pods",
            progress=progress,
            progress_phase="fetch pods",
        ),
    }


def fetch_optional_namespace_resource(
    kubernetes: LiveNamespaceKubernetes,
    *,
    namespace: str,
    kind: str,
    needed: bool,
    timings: NamespaceInspectionTimings,
    timing_key: str,
    progress: ProgressBar | None = None,
    progress_phase: str = "",
) -> dict[str, Any]:
    if not needed:
        timings.record(timing_key, 0.0)
        return {"items": []}
    update_progress(progress, namespace, progress_phase)
    start = time.perf_counter()
    resource = kubernetes.namespace_resource(namespace, kind)
    timings.record(timing_key, time.perf_counter() - start)
    return resource


def lightweight_namespace_payload(
    args: argparse.Namespace,
    *,
    namespace: str,
    workloads: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "cluster": args.cluster,
        "namespace": namespace,
        "discovery": {
            "mode": "full-inventory",
            "scope": "workloads-configmaps-secrets",
        },
        "helm_releases": [],
        "workloads": workloads,
    }


__all__ = ["fetch_optional_namespace_resource", "lightweight_namespace_payload", "optional_namespace_resources"]
