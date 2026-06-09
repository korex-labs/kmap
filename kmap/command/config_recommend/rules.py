"""Pure config recommendation rules."""

from typing import Any

from ...tool_config import DEFAULT_RESOURCE_RECOMMENDATIONS
from .common import PRIORITY_ORDER, has_config_value, sorted_recommendations
from .models import ConfigRecommendation
from .namespace_rules import (
    PROJECT_FIELDS,
    collect_project_missing,
    collect_resource_missing,
    effective_namespace_resources,
    namespace_recommendations,
    normalized_namespace_entries,
    project_config,
    project_field_recommendation,
    project_field_recommendations,
    project_missing_buckets,
    resource_missing_buckets,
    resource_recommendation,
    resource_recommendations,
)
from .product_rules import PRODUCT_RECOMMENDATIONS, product_recommendations


def recommend_config(
    config: dict[str, Any],
    *,
    resource_policy: dict[str, list[str]] | None = None,
    include_low: bool = False,
    include_optional: bool = False,
) -> list[ConfigRecommendation]:
    resource_policy = resource_policy or DEFAULT_RESOURCE_RECOMMENDATIONS
    recommendations = product_recommendations(config, include_low=include_low)
    recommendations.extend(
        namespace_recommendations(
            config,
            resource_policy=resource_policy,
            include_low=include_low,
            include_optional=include_optional,
        )
    )
    return sorted_recommendations(recommendations)


__all__ = [
    "PRIORITY_ORDER",
    "PRODUCT_RECOMMENDATIONS",
    "PROJECT_FIELDS",
    "collect_project_missing",
    "collect_resource_missing",
    "effective_namespace_resources",
    "has_config_value",
    "namespace_recommendations",
    "normalized_namespace_entries",
    "product_recommendations",
    "project_config",
    "project_field_recommendation",
    "project_field_recommendations",
    "project_missing_buckets",
    "recommend_config",
    "resource_missing_buckets",
    "resource_recommendation",
    "resource_recommendations",
    "sorted_recommendations",
]
