"""Shared config recommendation helpers."""

from .models import ConfigRecommendation

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def sorted_recommendations(recommendations: list[ConfigRecommendation]) -> list[ConfigRecommendation]:
    return sorted(
        recommendations,
        key=lambda recommendation: (
            PRIORITY_ORDER.get(recommendation.priority, 99),
            recommendation.path,
        ),
    )


def has_config_value(config: dict[str, object], field: str) -> bool:
    value = config.get(field)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


__all__ = ["PRIORITY_ORDER", "has_config_value", "sorted_recommendations"]
