"""kmap tool-level config loading and CLI default resolution."""

import argparse
import os
from pathlib import Path
from typing import Any

from .io import load_required_yaml_file
from .paths import SCHEMAS_ROOT
from .tool_config_validation import RECOMMENDATION_RESOURCE_KEYS, validate_tool_config

DEFAULT_KMAP_CONFIG_FILE = SCHEMAS_ROOT / "kmap.yaml"
VIEW_DEFAULTS = {
    "likec4_image": "likec4/likec4",
    "structurizr_image": "structurizr/structurizr",
    "structurizr_args": "local",
}
VIEW_ENV_VARS = {
    "likec4_image": "KMAP_VIEW_LIKEC4_IMAGE",
    "structurizr_image": "KMAP_VIEW_STRUCTURIZR_IMAGE",
    "structurizr_args": "KMAP_VIEW_STRUCTURIZR_ARGS",
}
DEFAULT_RESOURCE_RECOMMENDATIONS = {
    "required": ["repo"],
    "optional": ["tasks", "logs", "monitoring", "chat"],
}


def apply_tool_config_overrides(args: argparse.Namespace) -> argparse.Namespace:
    config = load_tool_config(getattr(args, "kmap_config", None))
    args.kmap_tool_config = config
    if getattr(args, "command", "") == "view":
        apply_view_tool_config(args, config)
    return args


def load_tool_config(path_override: str | None = None) -> dict[str, Any]:
    explicit_path = bool(path_override) or "KMAP_CONFIG" in os.environ
    config_path = Path(path_override or os.environ.get("KMAP_CONFIG") or DEFAULT_KMAP_CONFIG_FILE)
    if not config_path.exists():
        if explicit_path:
            raise SystemExit(f"kmap config file not found: {config_path}")
        return {}
    if not config_path.is_file():
        raise SystemExit(f"kmap config path is not a file: {config_path}")

    config = load_required_yaml_file(config_path)
    errors = validate_tool_config(config)
    if errors:
        raise SystemExit("Invalid kmap config:\n" + "\n".join(f"- {error}" for error in errors))
    return config


def recommendation_resource_policy(config: dict[str, Any]) -> dict[str, list[str]]:
    resources = ((config or {}).get("recommendations") or {}).get("resources") or {}
    return {
        key: clean_string_list(resources.get(key), DEFAULT_RESOURCE_RECOMMENDATIONS[key])
        for key in RECOMMENDATION_RESOURCE_KEYS
    }


def clean_string_list(value: Any, default: list[str]) -> list[str]:
    if value is None:
        return list(default)
    return [str(item).strip() for item in value if str(item).strip()]


def resolve_view_config_value(field: str, current: Any, view: dict[str, Any]) -> str:
    if current not in {None, ""}:
        return str(current)
    env_value = os.environ.get(VIEW_ENV_VARS[field])
    if env_value not in {None, ""}:
        return env_value
    config_value = view.get(field)
    if config_value not in {None, ""}:
        return str(config_value)
    return VIEW_DEFAULTS[field]


def apply_view_tool_config(args: argparse.Namespace, config: dict[str, Any]) -> None:
    view = config.get("view") if isinstance(config.get("view"), dict) else {}
    for field in VIEW_DEFAULTS:
        setattr(args, field, resolve_view_config_value(field, getattr(args, field, None), view))


__all__ = [
    "DEFAULT_KMAP_CONFIG_FILE",
    "DEFAULT_RESOURCE_RECOMMENDATIONS",
    "VIEW_DEFAULTS",
    "apply_tool_config_overrides",
    "load_tool_config",
    "recommendation_resource_policy",
    "resolve_view_config_value",
    "validate_tool_config",
]
