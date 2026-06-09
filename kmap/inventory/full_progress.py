"""Progress and timing helpers for full inventory discovery."""

from dataclasses import dataclass, field
from typing import Any

from ..logging import ProgressBar


@dataclass
class NamespaceInspectionTimings:
    workloads: float = 0.0
    configmaps: float = 0.0
    secrets: float = 0.0
    pods: float = 0.0
    total: float = 0.0

    def record(self, name: str, elapsed: float) -> None:
        if hasattr(self, name):
            setattr(self, name, elapsed)


@dataclass
class NamespaceInspectionMetrics:
    runtime: dict[str, Any] = field(default_factory=dict)
    workloads: int = 0

    @property
    def vault_exec_seconds(self) -> float:
        return float(self.runtime.get("vault_exec_seconds", 0.0))

    @property
    def vault_execs(self) -> int:
        return int(self.runtime.get("vault_execs", 0))


def update_progress(progress: ProgressBar | None, namespace: str, phase: str) -> None:
    if progress is None:
        return
    progress.update(f"{namespace}: {phase}")


def namespace_timing_summary(
    namespace: str,
    report: dict[str, Any],
    timings: NamespaceInspectionTimings,
    metrics: NamespaceInspectionMetrics,
) -> str:
    parts = [
        f"[kmap] inspected {namespace}:",
        f"total={format_seconds(timings.total)}",
        f"workloads={format_seconds(timings.workloads)}",
        f"configmaps={format_seconds(timings.configmaps)}",
        f"secrets={format_seconds(timings.secrets)}",
        f"pods={format_seconds(timings.pods)}",
        f"vault_exec={format_seconds(metrics.vault_exec_seconds)}",
        f"execs={metrics.vault_execs}",
        f"selected={metrics.workloads}",
        f"buckets={bucket_candidate_count(report)}",
    ]
    return " ".join(parts)


def bucket_candidate_count(report: dict[str, Any]) -> int:
    return sum(len(workload.get("bucket_candidates") or []) for workload in report.get("workloads") or [])


def format_seconds(value: float) -> str:
    return f"{value:.1f}s"
