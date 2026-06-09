"""Command entrypoint for config recommendations."""

from pathlib import Path
from typing import Any

from ...config import validate_config_shape
from ...io import load_yaml_config_or_error
from ...logging import eprint
from ...tool_config import recommendation_resource_policy
from .output import print_recommendations, print_validation_failure
from .rules import recommend_config


def config_recommend(args) -> int:
    config_path = Path(args.config_file)
    config = load_recommend_config(config_path)
    if config is None:
        return 1
    errors, warnings = validate_config_shape(config)
    if errors:
        print_validation_failure(config_path, errors, warnings)
        return 1

    resource_policy = recommendation_resource_policy(getattr(args, "kmap_tool_config", {}))
    recommendations = recommend_config(
        config,
        resource_policy=resource_policy,
        include_low=getattr(args, "include_low", False),
        include_optional=getattr(args, "include_optional", False),
    )
    print_recommendations(config_path, recommendations, details=getattr(args, "details", False))
    return 0


def load_recommend_config(config_path: Path) -> dict[str, Any] | None:
    if not config_path.exists():
        eprint(f"[kmap] config validation failed: {config_path}")
        eprint("- config: file not found")
        return None
    if not config_path.is_file():
        eprint(f"[kmap] config validation failed: {config_path}")
        eprint("- config: path is not a file")
        return None
    return load_yaml_config_or_error(config_path)


__all__ = ["config_recommend", "load_recommend_config"]
