"""Cluster inventory aggregation from fragments and namespace state."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import slug_name
from ..io import load_required_json_file
from .cluster_fragments import CLUSTER_INVENTORY_SCHEMA_VERSION
from .cluster_inventory_rows import (
    merge_bucket_rows,
    merge_namespace_rows,
    repositories_for_cluster_namespaces,
    rows_with_last_seen,
    sorted_bucket_rows,
    sorted_namespace_rows,
)
from .cluster_state import load_namespace_state


@dataclass(frozen=True)
class ClusterInventory:
    cluster: str
    fragments: list[str]
    states: list[str]
    last_seen_at: str
    namespaces: list[dict[str, Any]]
    repositories: list[dict[str, Any]]
    buckets: list[dict[str, str]]


def load_cluster_inventories(output_dir: Path) -> list[ClusterInventory]:
    return [load_cluster_inventory(cluster_dir) for cluster_dir in cluster_dirs(output_dir)]


def cluster_dirs(output_dir: Path, *, cluster: str = "") -> list[Path]:
    clusters_dir = output_dir / "clusters"
    if not clusters_dir.exists():
        return []
    if cluster:
        cluster_dir = clusters_dir / slug_name(cluster).lower()
        return [cluster_dir] if cluster_dir.exists() else []
    return sorted(path for path in clusters_dir.iterdir() if path.is_dir())


def load_cluster_inventory(cluster_dir: Path) -> ClusterInventory:
    fragment_files = sorted((cluster_dir / "fragments").glob("*.json"))
    state_files = sorted((cluster_dir / "state" / "namespaces").glob("*.json"))
    namespace_rows: dict[str, dict[str, str]] = {}
    bucket_rows: dict[tuple[str, str, str, str, str], dict[str, str]] = {}
    cluster_name, fragments, fragment_seen = load_cluster_fragments(
        fragment_files,
        namespace_rows=namespace_rows,
        bucket_rows=bucket_rows,
        fallback_cluster=cluster_dir.name,
    )
    state_cluster_name, states, state_seen = load_cluster_namespace_states(
        state_files,
        namespace_rows=namespace_rows,
        bucket_rows=bucket_rows,
        fallback_cluster=cluster_dir.name,
    )
    namespaces = sorted_namespace_rows(namespace_rows)
    buckets = sorted_bucket_rows(bucket_rows)
    return ClusterInventory(
        cluster=cluster_inventory_name(cluster_name, state_cluster_name, fallback_cluster=cluster_dir.name),
        fragments=unique_sorted(fragments),
        states=unique_sorted(states),
        last_seen_at=latest_seen_at(fragment_seen, state_seen),
        namespaces=namespaces,
        repositories=repositories_for_cluster_namespaces(namespaces),
        buckets=buckets,
    )


def load_cluster_fragments(
    fragment_files: list[Path],
    *,
    namespace_rows: dict[str, dict[str, str]],
    bucket_rows: dict[tuple[str, str, str, str, str], dict[str, str]],
    fallback_cluster: str,
) -> tuple[str, list[str], list[str]]:
    cluster_name = ""
    fragments: list[str] = []
    last_seen_values: list[str] = []
    for fragment_file in fragment_files:
        payload = load_cluster_fragment(fragment_file)
        cluster_name = cluster_name or str(payload.get("cluster") or fallback_cluster)
        last_seen_at = str(payload.get("generated_at") or "")
        if last_seen_at:
            last_seen_values.append(last_seen_at)
        fragments.append(str(payload.get("fragment_id") or fragment_file.stem))
        merge_namespace_rows(namespace_rows, rows_with_last_seen(payload.get("namespaces") or [], last_seen_at))
        merge_bucket_rows(bucket_rows, rows_with_last_seen(payload.get("buckets") or [], last_seen_at))
    return cluster_name, fragments, last_seen_values


def load_cluster_namespace_states(
    state_files: list[Path],
    *,
    namespace_rows: dict[str, dict[str, str]],
    bucket_rows: dict[tuple[str, str, str, str, str], dict[str, str]],
    fallback_cluster: str,
) -> tuple[str, list[str], list[str]]:
    cluster_name = ""
    states = []
    last_seen_values: list[str] = []
    for state_file in state_files:
        payload = load_namespace_state(state_file)
        cluster_name = cluster_name or str(payload.get("cluster") or fallback_cluster)
        last_seen_at = str(payload.get("last_seen_at") or "")
        if last_seen_at:
            last_seen_values.append(last_seen_at)
        states.append(str(payload.get("namespace_name") or state_file.stem))
        merge_namespace_rows(namespace_rows, rows_with_last_seen([payload.get("namespace") or {}], last_seen_at))
        merge_bucket_rows(bucket_rows, rows_with_last_seen(payload.get("buckets") or [], last_seen_at))
    return cluster_name, states, last_seen_values


def cluster_inventory_name(fragment_cluster: str, state_cluster: str, *, fallback_cluster: str) -> str:
    return fragment_cluster or state_cluster or fallback_cluster


def latest_seen_at(*seen_groups: list[str]) -> str:
    return max((seen_at for group in seen_groups for seen_at in group), default="")


def unique_sorted(values: list[str]) -> list[str]:
    return sorted(set(values))


def load_cluster_fragment(fragment_file: Path) -> dict[str, Any]:
    payload = load_required_json_file(fragment_file)
    if int(payload.get("schema_version") or 0) != CLUSTER_INVENTORY_SCHEMA_VERSION:
        raise SystemExit(f"Unsupported cluster inventory schema version in {fragment_file}")
    return payload


def cluster_inventory_payload(inventory: ClusterInventory, *, generated_at: datetime) -> dict[str, Any]:
    return {
        "schema_version": CLUSTER_INVENTORY_SCHEMA_VERSION,
        "cluster": inventory.cluster,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "fragments": inventory.fragments,
        "states": inventory.states,
        "last_seen_at": inventory.last_seen_at,
        "namespaces": inventory.namespaces,
        "repositories": inventory.repositories,
        "buckets": inventory.buckets,
    }


__all__ = [
    "ClusterInventory",
    "cluster_dirs",
    "cluster_inventory_name",
    "cluster_inventory_payload",
    "latest_seen_at",
    "load_cluster_fragment",
    "load_cluster_fragments",
    "load_cluster_inventories",
    "load_cluster_inventory",
    "load_cluster_namespace_states",
    "merge_bucket_rows",
    "merge_namespace_rows",
    "repositories_for_cluster_namespaces",
    "rows_with_last_seen",
    "sorted_bucket_rows",
    "sorted_namespace_rows",
    "unique_sorted",
]
