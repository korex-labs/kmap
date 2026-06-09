"""Product and project metadata normalization."""

from typing import Any, Dict, Tuple

from .metadata import (
    clean_metadata_resources,
    clean_metadata_string,
    clean_metadata_tags,
    merge_project_metadata,
    normalize_project_metadata_item,
)

PRODUCT_METADATA_FIELDS = ("title", "owner_team", "domain", "description")
PRODUCT_OWNER_ALIASES = ("owner_team", "devops_team", "team")


def normalize_config_metadata(config: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    from .projects import normalize_namespace_config

    product_metadata = normalize_product_metadata(config)
    product_resources = clean_metadata_resources(config.get("resources"))
    if product_resources:
        product_metadata["resources"] = product_resources

    _, namespace_projects, project_metadata = normalize_namespace_config(
        config,
        clean_metadata_string(config.get("product")),
    )
    projects = config.get("projects") or {}
    merge_config_projects(project_metadata, projects)
    inherit_product_resources(project_metadata, namespace_projects, product_resources)

    return product_metadata, project_metadata


def merge_config_projects(project_metadata: Dict[str, Dict[str, Any]], projects: Any) -> None:
    if not isinstance(projects, dict):
        return
    for raw_name, raw_project in projects.items():
        name = clean_metadata_string(raw_name)
        if not name or not isinstance(raw_project, dict):
            continue
        project_metadata[name] = merge_project_metadata(
            project_metadata.get(name, {}),
            normalize_project_metadata_item(raw_project),
        )


def normalize_product_metadata(config: Dict[str, Any]) -> Dict[str, Any]:
    product_metadata = {
        field: clean_metadata_string(config.get(field))
        for field in PRODUCT_METADATA_FIELDS
        if clean_metadata_string(config.get(field))
    }
    if not product_metadata.get("owner_team"):
        product_metadata.update(product_owner_metadata(config))
    product_tags = clean_metadata_tags(config.get("tags"))
    if product_tags:
        product_metadata["tags"] = product_tags
    return product_metadata


def product_owner_metadata(config: Dict[str, Any]) -> Dict[str, str]:
    for alias in PRODUCT_OWNER_ALIASES:
        owner = clean_metadata_string(config.get(alias))
        if owner:
            return {"owner_team": owner}
    return {}


def inherit_product_resources(
    project_metadata: Dict[str, Dict[str, Any]],
    namespace_projects: Dict[str, str],
    product_resources: Dict[str, str],
) -> None:
    if not product_resources:
        return
    for project_name in namespace_projects.values():
        project_metadata[project_name] = merge_project_metadata(
            {"resources": product_resources},
            project_metadata.get(project_name, {}),
        )
    for project_name, project in list(project_metadata.items()):
        project_metadata[project_name] = merge_project_metadata({"resources": product_resources}, project)


__all__ = [
    "PRODUCT_METADATA_FIELDS",
    "PRODUCT_OWNER_ALIASES",
    "inherit_product_resources",
    "merge_config_projects",
    "normalize_config_metadata",
    "normalize_product_metadata",
    "product_owner_metadata",
]
