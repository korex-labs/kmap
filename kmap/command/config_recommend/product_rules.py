"""Product-level config recommendation rules."""

from typing import Any

from .models import ConfigRecommendation

PRODUCT_RECOMMENDATIONS = (
    (
        "high",
        "owner_team",
        "Set the DevOps team responsible for operating this product.",
        "owner_team: DevOps Team Name",
    ),
    ("medium", "domain", "Group the product under a business or platform domain.", "domain: Payments"),
    (
        "medium",
        "description",
        "Add a short product description for generated documentation.",
        "description: Short product architecture description.",
    ),
    ("low", "tags", "Add searchable product tags.", "tags:\n  - generated\n  - payments"),
    (
        "medium",
        "discovery",
        "Pin the default Kubernetes context for repeatable local runs.",
        "discovery:\n  context: product-prod\n  kubeconfig: ~/.kube/config",
    ),
    (
        "medium",
        "external_mappings",
        "Group known external dependencies into stable architecture elements.",
        "external_mappings:\n  - name: External API\n    element_type: External_API\n    match:\n      - api.example.com",
    ),
    (
        "low",
        "system_naming",
        "Document fallback naming for workloads without app_service annotations.",
        "system_naming:\n  fallback:\n    enabled: true",
    ),
    (
        "low",
        "dependency_hotspots",
        "Highlight highly referenced dependencies in generated views.",
        "dependency_hotspots:\n  enabled: true\n  metric: incoming_distinct_source_container_count",
    ),
    ("low", "render", "Make the intended renderer explicit.", "render: both"),
)


def product_recommendations(config: dict[str, Any], *, include_low: bool = False) -> list[ConfigRecommendation]:
    from .common import has_config_value

    recommendations = []
    for priority, field, reason, snippet in PRODUCT_RECOMMENDATIONS:
        if priority == "low" and not include_low:
            continue
        if not has_config_value(config, field):
            recommendations.append(ConfigRecommendation(priority, field, reason, snippet))
    return recommendations


__all__ = ["PRODUCT_RECOMMENDATIONS", "product_recommendations"]
