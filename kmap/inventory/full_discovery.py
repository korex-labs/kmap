"""Live cluster inventory discovery."""

import argparse
from datetime import datetime
from pathlib import Path

from ..config import slug_name
from ..io import ensure_dir
from ..kubernetes.client import KubectlClient
from ..logging import eprint
from ..paths import KMAP_TMP_DIR
from .cluster_reports import render_cluster_reports
from .full_discovery_client import (
    cluster_kubectl_client as _cluster_kubectl_client,
)
from .full_discovery_client import (
    discover_cluster_namespaces as _discover_cluster_namespaces,
)
from .full_discovery_inventory import config_inventory_by_namespace, discovered_namespace_rows
from .full_discovery_namespaces import (
    inspect_and_persist_namespace,
    persist_inspected_namespace,
)
from .full_discovery_namespaces import (
    inspect_discovered_namespaces as _inspect_discovered_namespaces,
)
from .full_discovery_persistence import remove_legacy_live_discovery_fragment
from .repositories import enrich_inventory_rows_from_repositories

DEFAULT_FULL_DISCOVERY_REPORTS_DIR = KMAP_TMP_DIR / "inventory-full"


def cluster_kubectl_client(
    args: argparse.Namespace,
    *,
    exec_timeout: int | None = None,
    exec_attempts: int | None = None,
) -> KubectlClient:
    return _cluster_kubectl_client(
        args,
        exec_timeout=exec_timeout,
        exec_attempts=exec_attempts,
        client_class=KubectlClient,
    )


def discover_cluster_namespaces(args: argparse.Namespace) -> list[str]:
    return _discover_cluster_namespaces(args, client_class=KubectlClient)


def inspect_discovered_namespaces(
    args: argparse.Namespace,
    namespaces: list[str],
    *,
    output_dir: Path,
    cluster: str,
    reports_dir: Path,
    inventory_rows: list,
    generated_at: datetime,
) -> list[Path]:
    return _inspect_discovered_namespaces(
        args,
        namespaces,
        output_dir=output_dir,
        cluster=cluster,
        reports_dir=reports_dir,
        inventory_rows=inventory_rows,
        generated_at=generated_at,
        client_factory=cluster_kubectl_client,
    )


def discover_full_inventory(args: argparse.Namespace, *, generated_at: datetime) -> int:
    if not getattr(args, "cluster", ""):
        raise SystemExit("--full live discovery requires --cluster")

    cluster = args.cluster
    output_dir = Path(args.output_dir)
    config_dir = Path(args.config_dir)
    reports_dir = Path(getattr(args, "full_reports_dir", "") or DEFAULT_FULL_DISCOVERY_REPORTS_DIR) / slug_name(cluster)
    ensure_dir(reports_dir)

    namespaces = discover_cluster_namespaces(args)
    if not namespaces:
        eprint(f"[kmap] warning: no namespaces discovered for cluster {cluster}")
        return 0

    inventory_index = config_inventory_by_namespace(config_dir)
    namespace_rows = discovered_namespace_rows(
        cluster,
        namespaces,
        inventory_index,
        tool_config=getattr(args, "kmap_tool_config", {}),
    )
    namespace_rows = enrich_inventory_rows_from_repositories(namespace_rows, getattr(args, "kmap_tool_config", {}))
    state_files = inspect_discovered_namespaces(
        args,
        namespaces,
        output_dir=output_dir,
        cluster=cluster,
        reports_dir=reports_dir,
        inventory_rows=namespace_rows,
        generated_at=generated_at,
    )
    eprint(f"[kmap] wrote cluster namespace state: {len(state_files)} namespaces")
    remove_legacy_live_discovery_fragment(output_dir, cluster)
    for path in render_cluster_reports(
        output_dir=output_dir,
        generated_at=generated_at,
        cluster=cluster,
        tool_config=getattr(args, "kmap_tool_config", {}),
    ):
        if path.suffix == ".html":
            eprint(f"[kmap] wrote cluster inventory: {path}")
    return 0


__all__ = [
    "DEFAULT_FULL_DISCOVERY_REPORTS_DIR",
    "discover_cluster_namespaces",
    "discover_full_inventory",
    "discovered_namespace_rows",
    "inspect_and_persist_namespace",
    "inspect_discovered_namespaces",
    "persist_inspected_namespace",
]
