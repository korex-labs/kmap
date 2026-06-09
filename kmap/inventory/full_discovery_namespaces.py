"""Namespace inspection and persistence for full inventory discovery."""

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from ..kubernetes.client import KubectlClient
from ..logging import eprint, set_active_progress
from ..progress import run_all_progress
from .full_discovery_client import cluster_kubectl_client
from .full_discovery_persistence import remove_stale_full_discovery_reports, write_namespace_report_state
from .full_progress import namespace_timing_summary
from .heuristics import inferred_inventory_row
from .live_namespace import inspect_live_namespace, write_lightweight_report
from .namespaces import InventoryRow


@dataclass(frozen=True)
class NamespacePersistenceContext:
    args: argparse.Namespace
    client: KubectlClient
    namespace: str
    output_dir: Path
    cluster: str
    reports_dir: Path
    inventory_row: InventoryRow | None
    generated_at: datetime
    progress: Any


def inspect_discovered_namespaces(
    args: argparse.Namespace,
    namespaces: list[str],
    *,
    output_dir: Path,
    cluster: str,
    reports_dir: Path,
    inventory_rows: list[InventoryRow],
    generated_at: datetime,
    client_factory: Callable[..., KubectlClient] = cluster_kubectl_client,
) -> list[Path]:
    client = client_factory(
        args,
        exec_timeout=getattr(args, "inventory_exec_timeout", 5),
        exec_attempts=getattr(args, "inventory_exec_attempts", 1),
    )
    remove_stale_full_discovery_reports(reports_dir)
    inventory_by_namespace = {row.namespace: row for row in inventory_rows}
    written_state_files: list[Path] = []
    progress_enabled = getattr(args, "output", "progress") == "progress"
    with run_all_progress(enabled=progress_enabled, total=len(namespaces)) as progress:
        for namespace in namespaces:
            previous_progress = set_active_progress(None)
            try:
                written_state_files.extend(
                    persist_inspected_namespace(
                        NamespacePersistenceContext(
                            args=args,
                            client=client,
                            namespace=namespace,
                            output_dir=output_dir,
                            cluster=cluster,
                            reports_dir=reports_dir,
                            inventory_row=inventory_by_namespace.get(namespace),
                            generated_at=generated_at,
                            progress=progress,
                        )
                    )
                )
            finally:
                set_active_progress(previous_progress)
            progress.advance(f"inspected {namespace}")
        progress.done("full discovery done")
    return written_state_files


def inspect_and_persist_namespace(
    args: argparse.Namespace,
    *,
    client: KubectlClient,
    namespace: str,
    output_dir: Path,
    cluster: str,
    reports_dir: Path,
    inventory_row: InventoryRow | None,
    generated_at: datetime,
    **persistence_options: Any,
) -> list[Path]:
    return persist_inspected_namespace(
        NamespacePersistenceContext(
            args=args,
            client=client,
            namespace=namespace,
            output_dir=output_dir,
            cluster=cluster,
            reports_dir=reports_dir,
            inventory_row=inventory_row,
            generated_at=generated_at,
            progress=persistence_options.get("progress"),
        )
    )


def persist_inspected_namespace(context: NamespacePersistenceContext) -> list[Path]:
    result = inspect_live_namespace(
        context.args,
        client=context.client,
        namespace=context.namespace,
        inventory_row=context.inventory_row,
        progress=context.progress,
    )
    write_lightweight_report(
        context.args,
        namespace=context.namespace,
        report=result.report,
        reports_dir=context.reports_dir,
    )
    state_files = write_namespace_report_state(
        output_dir=context.output_dir,
        cluster=context.cluster,
        generated_at=context.generated_at,
        namespace_row=context.inventory_row
        or inferred_inventory_row(
            cluster=context.cluster,
            namespace=context.namespace,
            configured=None,
            tool_config=getattr(context.args, "kmap_tool_config", {}),
        ),
        report=result.report,
    )
    eprint(namespace_timing_summary(context.namespace, result.report, result.timings, result.metrics))
    return state_files


__all__ = [
    "NamespacePersistenceContext",
    "inspect_and_persist_namespace",
    "inspect_discovered_namespaces",
    "persist_inspected_namespace",
]
