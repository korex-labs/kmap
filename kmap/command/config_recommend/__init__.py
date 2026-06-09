"""Recommend product config improvements."""

from .core import config_recommend, load_recommend_config
from .models import ConfigRecommendation
from .output import print_recommendation_details, print_recommendations, print_validation_failure
from .rules import (
    effective_namespace_resources,
    has_config_value,
    namespace_recommendations,
    normalized_namespace_entries,
    product_recommendations,
    project_config,
    project_field_recommendation,
    project_missing_buckets,
    recommend_config,
    resource_missing_buckets,
    resource_recommendation,
)

__all__ = [
    "ConfigRecommendation",
    "config_recommend",
    "effective_namespace_resources",
    "has_config_value",
    "load_recommend_config",
    "namespace_recommendations",
    "normalized_namespace_entries",
    "print_recommendation_details",
    "print_recommendations",
    "print_validation_failure",
    "product_recommendations",
    "project_config",
    "project_field_recommendation",
    "project_missing_buckets",
    "recommend_config",
    "resource_missing_buckets",
    "resource_recommendation",
]
