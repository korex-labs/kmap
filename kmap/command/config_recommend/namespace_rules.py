"""Namespace and resource config recommendation rules."""

from typing import Any

from ...config import clean_metadata_resources
from ...tool_config import DEFAULT_RESOURCE_RECOMMENDATIONS
from .common import has_config_value
from .models import ConfigRecommendation

PROJECT_FIELDS = (
    ("medium", "title", "Give the project a human-readable display name.", "title: Project Title"),
    ("medium", "element_type", "Set the LikeC4 element type instead of relying on inference.", "element_type: API"),
    (
        "medium",
        "domain_team",
        "Set the developer/domain team responsible for this project's repository.",
        "domain_team: Developer Team Name",
    ),
    (
        "medium",
        "description",
        "Explain the project's role in generated docs.",
        "description: Short project description.",
    ),
    ("low", "tags", "Add project-level tags for filtering and review.", "tags:\n  - backend"),
)


def namespace_recommendations(
    config: dict[str, Any],
    *,
    resource_policy: dict[str, list[str]] | None = None,
    include_low: bool = False,
    include_optional: bool = False,
) -> list[ConfigRecommendation]:
    raw_namespaces = normalized_namespace_entries(config)
    if raw_namespaces is None:
        return []

    resource_policy = resource_policy or DEFAULT_RESOURCE_RECOMMENDATIONS
    project_missing = project_missing_buckets()
    required_resource_missing = resource_missing_buckets(resource_policy.get("required", []))
    optional_resource_missing = resource_missing_buckets(resource_policy.get("optional", []))
    product_resources = clean_metadata_resources(config.get("resources"))
    for namespace, entry in raw_namespaces.items():
        entry = entry if isinstance(entry, dict) else {}
        collect_project_missing(namespace, entry, project_missing)
        resources = effective_namespace_resources(product_resources, entry)
        collect_resource_missing(namespace, resources, required_resource_missing)
        collect_resource_missing(namespace, resources, optional_resource_missing)

    recommendations = project_field_recommendations(project_missing, include_low=include_low)
    recommendations.extend(resource_recommendations(required_resource_missing, priority="high", required=True))
    if include_optional:
        recommendations.extend(resource_recommendations(optional_resource_missing, priority="low", required=False))
    return recommendations


def normalized_namespace_entries(config: dict[str, Any]) -> dict[str, Any] | None:
    raw_namespaces = config.get("namespaces") or config.get("namespace") or {}
    if isinstance(raw_namespaces, list):
        return {namespace: {} for namespace in raw_namespaces}
    if isinstance(raw_namespaces, dict):
        return raw_namespaces
    return None


def project_missing_buckets() -> dict[str, list[str]]:
    return {field: [] for _priority, field, _reason, _snippet in PROJECT_FIELDS}


def resource_missing_buckets(fields: list[str]) -> dict[str, list[str]]:
    return {key: [] for key in fields}


def collect_project_missing(namespace: str, entry: dict[str, Any], missing_by_field: dict[str, list[str]]) -> None:
    project = project_config(entry)
    for _priority, field, _reason, _snippet in PROJECT_FIELDS:
        if not has_config_value(project, field):
            missing_by_field[field].append(f"namespaces.{namespace}.project.{field}")


def collect_resource_missing(
    namespace: str,
    resources: dict[str, str],
    missing_by_field: dict[str, list[str]],
) -> None:
    for field in missing_by_field:
        if not has_config_value(resources, field):
            missing_by_field[field].append(f"namespaces.{namespace}.resources.{field}")


def project_field_recommendations(
    missing_by_field: dict[str, list[str]], *, include_low: bool = False
) -> list[ConfigRecommendation]:
    reasons = {field: (priority, reason, snippet) for priority, field, reason, snippet in PROJECT_FIELDS}
    recommendations = []
    for field, paths in missing_by_field.items():
        if not paths:
            continue
        priority, reason, snippet = reasons[field]
        if priority == "low" and not include_low:
            continue
        recommendations.append(project_field_recommendation(field, paths, priority, reason, snippet))
    return recommendations


def project_field_recommendation(
    field: str,
    paths: list[str],
    priority: str,
    reason: str,
    snippet: str,
) -> ConfigRecommendation:
    return ConfigRecommendation(
        priority,
        f"namespaces.*.project.{field}",
        f"{len(paths)} namespaces missing project.{field}. {reason}",
        snippet,
        tuple(paths),
    )


def resource_recommendations(
    missing_by_field: dict[str, list[str]],
    *,
    priority: str,
    required: bool,
) -> list[ConfigRecommendation]:
    recommendations = []
    label = "required" if required else "optional"
    for field, paths in missing_by_field.items():
        if not paths:
            continue
        recommendations.append(resource_recommendation(field, paths, priority, label))
    return recommendations


def resource_recommendation(
    field: str,
    paths: list[str],
    priority: str,
    label: str,
) -> ConfigRecommendation:
    return ConfigRecommendation(
        priority,
        f"namespaces.*.resources.{field}",
        (
            f"{len(paths)} namespaces missing {label} resource '{field}' after product-level inheritance. "
            "Set it on the product if it is shared, or on each namespace when project-specific."
        ),
        f"resources:\n  {field}: https://example.com/{field}",
        tuple(paths),
    )


def effective_namespace_resources(product_resources: dict[str, str], entry: dict[str, Any]) -> dict[str, str]:
    resources = dict(product_resources)
    resources.update(clean_metadata_resources(entry.get("resources")))
    return resources


def project_config(entry: dict[str, Any]) -> dict[str, Any]:
    project = entry.get("project")
    if isinstance(project, dict):
        return project
    if isinstance(project, str) and project.strip():
        return {"title": project}
    return {}


__all__ = [
    "PROJECT_FIELDS",
    "collect_project_missing",
    "collect_resource_missing",
    "effective_namespace_resources",
    "namespace_recommendations",
    "normalized_namespace_entries",
    "project_config",
    "project_field_recommendation",
    "project_field_recommendations",
    "project_missing_buckets",
    "resource_missing_buckets",
    "resource_recommendation",
    "resource_recommendations",
]
