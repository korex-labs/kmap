"""Workload project/system naming context helpers."""

from typing import Any, Dict

from ...config import clean_metadata_string, infer_project_from_namespace
from ...naming import canonical_fallback_system_name

APP_SERVICE_ANNOTATION = "app_service"


def resolved_project_name(
    *,
    svc: Dict[str, Any],
    naming: Any,
    product_name: str,
    namespace: str,
    config_namespace_projects: Dict[str, str],
) -> str:
    return (
        clean_metadata_string(config_namespace_projects.get(namespace))
        or clean_metadata_string(svc.get("project"))
        or naming.project
        or infer_project_from_namespace(namespace, product_name)
    )


def configured_system_title_from_project(project: Dict[str, Any], project_meta: Dict[str, Any]) -> str:
    configured_system_title = clean_metadata_string(project_meta.get("system_title"))
    if configured_system_title or not clean_metadata_string(project_meta.get("title")):
        return configured_system_title
    namespace_count = len((project.get("discovery") or {}).get("namespaces") or [])
    if namespace_count == 1 and project_meta.get("title") != project.get("title"):
        return clean_metadata_string(project_meta.get("title"))
    return ""


def resolved_system_name_and_source(
    *,
    svc: Dict[str, Any],
    raw_service_name: str,
    product_name: str,
    project_name: str,
    system_naming_config: Dict[str, Any],
) -> tuple[str, Dict[str, Any]]:
    raw_app_service = clean_metadata_string(svc.get("app_service"))
    app_service_source = dict(svc.get("app_service_source") or {})
    if raw_app_service:
        return raw_app_service, app_service_source

    system_name, fallback_normalization = canonical_fallback_system_name(
        raw_service_name,
        product_name,
        project_name,
        system_naming_config,
    )
    app_service_source = app_service_source or {
        "kind": "fallback",
        "key": APP_SERVICE_ANNOTATION,
        "path": "",
        "fallback_used": True,
    }
    app_service_source.update(fallback_normalization)
    return system_name, app_service_source


__all__ = [
    "APP_SERVICE_ANNOTATION",
    "configured_system_title_from_project",
    "resolved_project_name",
    "resolved_system_name_and_source",
]
