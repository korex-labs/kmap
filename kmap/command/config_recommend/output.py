"""Output helpers for config recommendations."""

from pathlib import Path

from ...logging import eprint
from .models import ConfigRecommendation

DETAIL_LIMIT = 3


def print_validation_failure(config_path: Path, errors: list[str], warnings: list[str]) -> None:
    eprint(f"[kmap] config validation failed: {config_path}")
    for error in errors:
        eprint(f"- {error}")
    if warnings:
        eprint("[kmap] warnings:")
        for warning in warnings:
            eprint(f"- {warning}")


def print_recommendations(
    config_path: Path, recommendations: list[ConfigRecommendation], *, details: bool = False
) -> None:
    if not recommendations:
        print(f"[kmap] config recommendations: {config_path}")
        print("No recommendations. Looks good.")
        return

    print(f"[kmap] config recommendations: {config_path}")
    for index, recommendation in enumerate(recommendations, start=1):
        print(f"{index}. [{recommendation.priority}] {recommendation.path}")
        print(f"   {recommendation.reason}")
        print_recommendation_details(recommendation, details=details)
        if recommendation.snippet:
            print("   Example:")
            for line in recommendation.snippet.splitlines():
                print(f"     {line}")


def print_recommendation_details(recommendation: ConfigRecommendation, *, details: bool) -> None:
    if not recommendation.details:
        return
    visible = recommendation.details if details else recommendation.details[:DETAIL_LIMIT]
    print("   Affected paths:")
    for path in visible:
        print(f"     - {path}")
    hidden_count = len(recommendation.details) - len(visible)
    if hidden_count > 0:
        print(f"     ... +{hidden_count} more; use --details to list all")


__all__ = [
    "DETAIL_LIMIT",
    "print_recommendation_details",
    "print_recommendations",
    "print_validation_failure",
]
