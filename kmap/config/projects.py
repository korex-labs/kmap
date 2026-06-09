"""Project and namespace config normalization."""

from typing import Any, Dict, List, Tuple

from .metadata import (
    clean_metadata_resources,
    clean_metadata_string,
    merge_project_metadata,
    normalize_project_metadata_item,
)
from .names import slug_name
from .options import NAMESPACE_ALIAS_IGNORED_TOKENS
from .project_metadata import (
    PRODUCT_METADATA_FIELDS,
    PRODUCT_OWNER_ALIASES,
    merge_config_projects,
    normalize_config_metadata,
    normalize_product_metadata,
    product_owner_metadata,
)


def infer_project_from_namespace(namespace: str, product: str = "") -> str:
    ns = (namespace or "").strip().lower()
    if not ns:
        return "project"
    parts = [p for p in ns.split("-") if p]
    if not parts:
        return "project"

    product_token = slug_name(product).lower() if product else ""

    out_parts = []
    for p in parts:
        if p in NAMESPACE_ALIAS_IGNORED_TOKENS:
            break
        if product_token and p == product_token:
            break
        if p.isdigit():
            break
        out_parts.append(p)

    if not out_parts:
        return parts[0]
    return "-".join(out_parts)


def normalize_namespace_config(
    config: Dict[str, Any], product_name: str = ""
) -> Tuple[List[str], Dict[str, str], Dict[str, Dict[str, Any]]]:
    raw_namespaces = config.get("namespaces") or config.get("namespace") or []
    namespaces: List[str] = []
    namespace_projects: Dict[str, str] = {}
    project_metadata: Dict[str, Dict[str, Any]] = {}

    def add_namespace(raw_namespace: Any) -> str:
        return add_clean_namespace(namespaces, raw_namespace)

    if isinstance(raw_namespaces, list):
        for raw_namespace in raw_namespaces:
            add_namespace(raw_namespace)
    elif isinstance(raw_namespaces, dict):
        record_namespace_mapping_entries(
            raw_namespaces=raw_namespaces,
            add_namespace=add_namespace,
            product_name=product_name,
            namespace_projects=namespace_projects,
            project_metadata=project_metadata,
        )

    raw_namespace_projects = config.get("namespace_projects") or config.get("namespace_project") or {}
    record_explicit_namespace_projects(raw_namespace_projects, add_namespace, namespace_projects)

    return namespaces, namespace_projects, project_metadata


def add_clean_namespace(namespaces: List[str], raw_namespace: Any) -> str:
    namespace = clean_metadata_string(raw_namespace)
    if namespace and namespace not in namespaces:
        namespaces.append(namespace)
    return namespace


def record_namespace_mapping_entries(
    *,
    raw_namespaces: Dict[Any, Any],
    add_namespace: Any,
    product_name: str,
    namespace_projects: Dict[str, str],
    project_metadata: Dict[str, Dict[str, Any]],
) -> None:
    for raw_namespace, raw_entry in raw_namespaces.items():
        namespace = add_namespace(raw_namespace)
        if not namespace:
            continue
        record_namespace_config_entry(
            namespace=namespace,
            raw_entry=raw_entry,
            product_name=product_name,
            namespace_projects=namespace_projects,
            project_metadata=project_metadata,
        )


def record_explicit_namespace_projects(
    raw_namespace_projects: Any, add_namespace: Any, namespace_projects: Dict[str, str]
) -> None:
    if not isinstance(raw_namespace_projects, dict):
        return
    for raw_namespace, raw_project in raw_namespace_projects.items():
        namespace = add_namespace(raw_namespace)
        project_name = clean_metadata_string(raw_project)
        if namespace and project_name:
            namespace_projects[namespace] = project_name


def record_namespace_config_entry(
    *,
    namespace: str,
    raw_entry: Any,
    product_name: str,
    namespace_projects: Dict[str, str],
    project_metadata: Dict[str, Dict[str, Any]],
) -> None:
    if isinstance(raw_entry, str):
        project_name = clean_metadata_string(raw_entry)
        if project_name:
            namespace_projects[namespace] = project_name
        return
    if not isinstance(raw_entry, dict):
        return

    project_name, raw_project = namespace_project_name_and_metadata(raw_entry, namespace, product_name)
    namespace_projects[namespace] = project_name

    item = namespace_project_metadata(raw_project, raw_entry)
    if item:
        project_metadata[project_name] = merge_project_metadata(project_metadata.get(project_name, {}), item)


def namespace_project_metadata(raw_project: Dict[str, Any], raw_entry: Dict[str, Any]) -> Dict[str, Any]:
    item = normalize_project_metadata_item(raw_project)
    resources = clean_metadata_resources(raw_entry.get("resources"))
    if resources:
        return merge_project_metadata(item, {"resources": resources})
    return item


def namespace_project_name_and_metadata(
    raw_entry: Dict[str, Any],
    namespace: str,
    product_name: str,
) -> Tuple[str, Dict[str, Any]]:
    raw_project = raw_entry.get("project") or {}
    if isinstance(raw_project, str):
        return clean_metadata_string(raw_project) or infer_project_from_namespace(namespace, product_name), {}
    if not isinstance(raw_project, dict):
        return infer_project_from_namespace(namespace, product_name), {}

    project_name = (
        clean_metadata_string(raw_project.get("name"))
        or clean_metadata_string(raw_project.get("project"))
        or clean_metadata_string(raw_project.get("id"))
    )
    if not project_name and clean_metadata_string(raw_project.get("title")):
        project_name = slug_name(raw_project.get("title")).lower()
    return project_name or infer_project_from_namespace(namespace, product_name), raw_project


__all__ = [
    "PRODUCT_METADATA_FIELDS",
    "PRODUCT_OWNER_ALIASES",
    "add_clean_namespace",
    "infer_project_from_namespace",
    "merge_config_projects",
    "namespace_project_metadata",
    "namespace_project_name_and_metadata",
    "normalize_config_metadata",
    "normalize_namespace_config",
    "normalize_product_metadata",
    "product_owner_metadata",
    "record_explicit_namespace_projects",
    "record_namespace_config_entry",
    "record_namespace_mapping_entries",
]
