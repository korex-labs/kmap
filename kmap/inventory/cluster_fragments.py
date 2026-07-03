"""Cluster-scoped inventory fragment generation."""

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import slug_name, validate_config_shape
from ..io import dump_json, ensure_dir, load_required_json_file, load_yaml_config_or_error
from ..logging import eprint
from .buckets import (
    BUCKET_REPORT_SCHEMA_VERSION,
    bucket_row_dict,
    bucket_rows_from_artifact,
)
from .namespaces import InventoryRow, config_files, inventory_rows_for_config

CLUSTER_INVENTORY_SCHEMA_VERSION = 1


def render_cluster_fragments(
    *,
    config_dir: Path,
    bucket_artifacts_dir: Path,
    output_dir: Path,
    generated_at: datetime,
    cluster: str = "",
) -> list[Path]:
    written: list[Path] = []
    for config_file in config_files(config_dir):
        config = load_valid_product_config(config_file)
        namespace_rows = inventory_rows_for_config(config)
        bucket_rows = bucket_rows_for_config_fragment(
            bucket_artifacts_dir=bucket_artifacts_dir,
            config_file=config_file,
            namespace_rows=namespace_rows,
        )
        for cluster_name in fragment_clusters(namespace_rows, bucket_rows, cluster=cluster):
            fragment = cluster_fragment_payload(
                cluster=cluster_name,
                fragment_id=config_file.stem,
                generated_at=generated_at,
                namespace_rows=[row for row in namespace_rows if row.cluster == cluster_name],
                bucket_rows=[row for row in bucket_rows if row.cluster == cluster_name],
            )
            output_file = write_cluster_fragment(output_dir, cluster_name, config_file.stem, fragment)
            written.append(output_file)
            eprint(f"[kmap] wrote cluster inventory fragment: {output_file}")
    return written


def fragment_clusters(namespace_rows: list[InventoryRow], bucket_rows: list[Any], *, cluster: str = "") -> list[str]:
    clusters = sorted({row.cluster for row in namespace_rows} | {row.cluster for row in bucket_rows})
    if cluster:
        return [cluster_name for cluster_name in clusters if cluster_name == cluster]
    return clusters


def write_cluster_fragment(output_dir: Path, cluster: str, fragment_id: str, fragment: dict[str, Any]) -> Path:
    output_file = cluster_fragment_path(output_dir, cluster, fragment_id)
    ensure_dir(output_file.parent)
    dump_json(output_file, fragment)
    return output_file


def load_valid_product_config(config_file: Path) -> dict[str, Any]:
    config = load_yaml_config_or_error(config_file)
    errors, _warnings = validate_config_shape(config)
    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise SystemExit(f"Invalid product config: {config_file}\n{joined}")
    return config


def bucket_rows_for_config_fragment(
    *,
    bucket_artifacts_dir: Path,
    config_file: Path,
    namespace_rows: list[InventoryRow],
):
    artifact_file = bucket_artifacts_dir / f"{config_file.stem}.json"
    if not artifact_file.exists():
        return []
    payload = load_required_json_file(artifact_file)
    if int(payload.get("schema_version") or 0) != BUCKET_REPORT_SCHEMA_VERSION:
        raise SystemExit(f"Unsupported bucket report schema version in {artifact_file.name}")
    inventory = {(row.cluster, row.namespace): row for row in namespace_rows}
    inventory.update({("", row.namespace): row for row in namespace_rows})
    return bucket_rows_from_artifact(payload, inventory, fallback_report_key=config_file.stem)


def cluster_fragment_payload(
    *,
    cluster: str,
    fragment_id: str,
    generated_at: datetime,
    namespace_rows: list[InventoryRow],
    bucket_rows,
) -> dict[str, Any]:
    repositories = repositories_for_namespaces(namespace_rows)
    return {
        "schema_version": CLUSTER_INVENTORY_SCHEMA_VERSION,
        "cluster": cluster,
        "fragment_id": fragment_id,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "namespaces": [namespace_row_dict(row) for row in sorted_namespaces(namespace_rows)],
        "repositories": repositories,
        "buckets": [bucket_row_dict(row) for row in bucket_rows],
    }


def sorted_namespaces(rows: list[InventoryRow]) -> list[InventoryRow]:
    return sorted(rows, key=lambda row: (row.product.lower(), row.namespace.lower(), row.repository.lower()))


def namespace_row_dict(row: InventoryRow) -> dict[str, Any]:
    payload = {
        "cluster": row.cluster,
        "namespace": row.namespace,
        "stage": row.stage,
        "labels": row.labels,
        "product": row.product,
        "product_title": row.product_title,
        "repository": row.repository,
        "repository_id": row.repository_id,
        "repository_name": row.repository_name,
        "repository_path": row.repository_path,
        "repository_group": row.repository_group,
        "repository_archived": row.repository_archived,
        "owner_team": row.owner_team,
    }
    if row.last_seen_at:
        payload["last_seen_at"] = row.last_seen_at
    return payload


def repositories_for_namespaces(rows: list[InventoryRow]) -> list[dict[str, Any]]:
    namespaces_by_repo: dict[str, list[str]] = defaultdict(list)
    metadata_by_repo: dict[str, InventoryRow] = {}
    for row in rows:
        if not row.repository:
            continue
        namespaces_by_repo[row.repository].append(row.namespace)
        metadata_by_repo.setdefault(row.repository, row)
    return [
        {
            "repository": repository,
            "namespaces": sorted(namespaces),
            "product": metadata_by_repo[repository].product,
            "product_title": metadata_by_repo[repository].product_title,
            "owner_team": metadata_by_repo[repository].owner_team,
            "repository_id": metadata_by_repo[repository].repository_id,
            "repository_name": metadata_by_repo[repository].repository_name,
            "repository_path": metadata_by_repo[repository].repository_path,
            "repository_group": metadata_by_repo[repository].repository_group,
            "repository_archived": metadata_by_repo[repository].repository_archived,
        }
        for repository, namespaces in sorted(namespaces_by_repo.items(), key=lambda item: item[0].lower())
    ]


def cluster_fragment_path(output_dir: Path, cluster: str, fragment_id: str) -> Path:
    return (
        output_dir
        / "clusters"
        / slug_name(cluster or "default").lower()
        / "fragments"
        / f"{slug_name(fragment_id)}.json"
    )


__all__ = [
    "CLUSTER_INVENTORY_SCHEMA_VERSION",
    "cluster_fragment_path",
    "cluster_fragment_payload",
    "namespace_row_dict",
    "render_cluster_fragments",
]
