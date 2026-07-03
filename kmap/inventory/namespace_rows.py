"""Namespace inventory row collection from kmap product configs."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import (
    clean_metadata_string,
    normalize_config_metadata,
    normalize_namespace_config,
)
from .product_config import load_valid_product_config
from .row_payloads import NamespaceRowPayload


@dataclass(frozen=True)
class InventoryRow:
    cluster: str
    product: str
    namespace: str
    repository: str
    owner_team: str
    labels: dict[str, str] = field(default_factory=dict)
    product_title: str = ""
    stage: str = ""
    last_seen_at: str = ""
    repository_id: str = ""
    repository_name: str = ""
    repository_path: str = ""
    repository_group: str = ""
    repository_archived: str = ""


@dataclass(frozen=True)
class InventoryNamespaceContext:
    namespace: str
    namespace_entry: dict[str, Any]
    config: dict[str, Any]
    product_name: str
    product_context: str
    product_owner: str
    product_title: str
    namespace_projects: dict[str, str]
    project_metadata: dict[str, dict[str, Any]]


def inventory_row_from_payload(row: NamespaceRowPayload, *, fallback_cluster: str = "") -> InventoryRow:
    return InventoryRow(
        cluster=row.get("cluster", "") or fallback_cluster,
        product=row.get("product", ""),
        namespace=row.get("namespace", ""),
        repository=row.get("repository", ""),
        owner_team=row.get("owner_team", ""),
        product_title=row.get("product_title", ""),
        stage=row.get("stage", ""),
        last_seen_at=row.get("last_seen_at", ""),
        repository_id=row.get("repository_id", ""),
        repository_name=row.get("repository_name", ""),
        repository_path=row.get("repository_path", ""),
        repository_group=row.get("repository_group", ""),
        repository_archived=row.get("repository_archived", ""),
        labels=row.get("labels", {}) if isinstance(row.get("labels"), dict) else {},
    )


def collect_inventory_rows(config_dir: Path) -> list[InventoryRow]:
    if not config_dir.exists():
        raise SystemExit(f"config directory not found: {config_dir}")
    if not config_dir.is_dir():
        raise SystemExit(f"config path is not a directory: {config_dir}")

    rows: list[InventoryRow] = []
    for config_file in config_files(config_dir):
        config = load_valid_product_config(config_file)
        rows.extend(inventory_rows_for_config(config))
    return sorted(
        rows,
        key=lambda row: (row.product.lower(), row.cluster.lower(), row.namespace.lower(), row.repository.lower()),
    )


def config_files(config_dir: Path) -> list[Path]:
    return [
        path
        for path in sorted(config_dir.glob("*.yaml"))
        if not path.name.startswith("example.") and path.name != "kmap.yaml"
    ]


def inventory_rows_for_config(config: dict[str, Any]) -> list[InventoryRow]:
    product_name = clean_metadata_string(config.get("product"))
    namespaces, namespace_projects, _namespace_metadata = normalize_namespace_config(config, product_name)
    product_metadata, project_metadata = normalize_config_metadata(config)
    product_context = discovery_context(config.get("discovery"))
    product_owner = clean_metadata_string(product_metadata.get("owner_team"))
    product_title = clean_metadata_string(product_metadata.get("title"))

    rows = []
    raw_namespaces = namespace_entries(config)
    for namespace in namespaces:
        namespace_entry = raw_namespaces.get(namespace, {})
        rows.append(
            inventory_row_from_context(
                InventoryNamespaceContext(
                    namespace=namespace,
                    namespace_entry=namespace_entry,
                    config=config,
                    product_name=product_name,
                    product_context=product_context,
                    product_owner=product_owner,
                    product_title=product_title,
                    namespace_projects=namespace_projects,
                    project_metadata=project_metadata,
                )
            )
        )
    return rows


def inventory_row_for_namespace(
    namespace: str,
    namespace_entry: dict[str, Any],
    **inventory_options: Any,
) -> InventoryRow:
    return inventory_row_from_context(
        InventoryNamespaceContext(
            namespace=namespace,
            namespace_entry=namespace_entry,
            config=inventory_options["config"],
            product_name=inventory_options["product_name"],
            product_context=inventory_options["product_context"],
            product_owner=inventory_options["product_owner"],
            product_title=inventory_options["product_title"],
            namespace_projects=inventory_options["namespace_projects"],
            project_metadata=inventory_options["project_metadata"],
        )
    )


def inventory_row_from_context(context: InventoryNamespaceContext) -> InventoryRow:
    project_name = context.namespace_projects.get(context.namespace, "")
    project = context.project_metadata.get(project_name, {})
    return InventoryRow(
        cluster=namespace_cluster(context.namespace_entry, context.product_context),
        product=context.product_name,
        namespace=context.namespace,
        repository=project_repository(project),
        owner_team=clean_metadata_string(project.get("owner_team")) or context.product_owner,
        product_title=context.product_title,
        stage=namespace_stage(context.namespace, context.namespace_entry, context.config),
    )


def namespace_cluster(namespace_entry: dict[str, Any], product_context: str) -> str:
    return discovery_context((namespace_entry or {}).get("discovery")) or product_context or "default"


def namespace_entries(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_namespaces = config.get("namespaces") or config.get("namespace") or {}
    if isinstance(raw_namespaces, list):
        return {
            clean_metadata_string(namespace): {} for namespace in raw_namespaces if clean_metadata_string(namespace)
        }
    if not isinstance(raw_namespaces, dict):
        return {}
    return {clean_metadata_string(key): value for key, value in raw_namespaces.items() if isinstance(value, dict)}


def discovery_context(discovery: Any) -> str:
    if not isinstance(discovery, dict):
        return ""
    return clean_metadata_string(discovery.get("context") or discovery.get("cluster"))


def project_repository(project: dict[str, Any]) -> str:
    resources = project.get("resources") if isinstance(project.get("resources"), dict) else {}
    return clean_metadata_string(resources.get("repo") or project.get("repo"))


def namespace_stage(namespace: str, namespace_entry: dict[str, Any], config: dict[str, Any]) -> str:
    explicit = clean_metadata_string(namespace_entry.get("stage") or namespace_entry.get("env") or config.get("env"))
    if explicit:
        return explicit
    return infer_stage_from_namespace(namespace)


def infer_stage_from_namespace(namespace: str) -> str:
    lowered = f"-{namespace.lower()}-"
    for stage in ("prod", "stage", "staging", "dev", "review", "sandbox", "test", "qa"):
        if f"-{stage}-" in lowered:
            return "stage" if stage == "staging" else stage
    return ""


__all__ = [
    "InventoryNamespaceContext",
    "InventoryRow",
    "collect_inventory_rows",
    "config_files",
    "discovery_context",
    "infer_stage_from_namespace",
    "inventory_row_for_namespace",
    "inventory_row_from_context",
    "inventory_row_from_payload",
    "inventory_rows_for_config",
    "namespace_cluster",
    "namespace_entries",
    "namespace_stage",
    "project_repository",
]
