"""Config application and validation entrypoints."""

import argparse
import os
from pathlib import Path

from ..io import load_yaml_config_or_error, load_yaml_file
from ..logging import eprint
from .discovery import normalize_discovery_config
from .metadata import clean_metadata_string
from .options import normalize_dependency_hotspots_config, normalize_system_naming_config
from .projects import normalize_config_metadata, normalize_namespace_config
from .validation import validate_config_shape


def attach_empty_config_metadata(args: argparse.Namespace) -> argparse.Namespace:
    if not hasattr(args, "product_metadata"):
        args.product_metadata = {}
    if not hasattr(args, "project_metadata"):
        args.project_metadata = {}
    if not hasattr(args, "config_namespaces"):
        args.config_namespaces = []
    if not hasattr(args, "config_namespace_projects"):
        args.config_namespace_projects = {}
    if not hasattr(args, "system_naming_config"):
        args.system_naming_config = normalize_system_naming_config({})
    if not hasattr(args, "dependency_hotspots_config"):
        args.dependency_hotspots_config = normalize_dependency_hotspots_config({})
    if not hasattr(args, "discovery_config"):
        args.discovery_config = normalize_discovery_config({})
    return args


def apply_config_overrides(args: argparse.Namespace) -> argparse.Namespace:
    config_path = getattr(args, "config", None)
    if not config_path:
        return attach_empty_config_metadata(args)

    config = load_product_config(config_path)
    attach_config_metadata(args, config)
    apply_scalar_config_overrides(args, config)
    apply_namespace_config_overrides(args)

    return args


def attach_config_metadata(args: argparse.Namespace, config: dict) -> None:
    args.product_metadata, args.project_metadata = normalize_config_metadata(config)
    args.system_naming_config = normalize_system_naming_config(config)
    args.dependency_hotspots_config = normalize_dependency_hotspots_config(config)
    args.discovery_config = normalize_discovery_config(config)
    args.config_namespaces, args.config_namespace_projects, _ = normalize_namespace_config(
        config,
        clean_metadata_string(config.get("product")),
    )


def apply_namespace_config_overrides(args: argparse.Namespace) -> None:
    namespace_values = getattr(args, "namespace", None)
    if hasattr(args, "namespace") and not namespace_values and args.config_namespaces:
        args.namespace = args.config_namespaces

    namespace_project_values = getattr(args, "namespace_project", None)
    if hasattr(args, "namespace_project") and not namespace_project_values and args.config_namespace_projects:
        args.namespace_project = namespace_project_args(args.config_namespace_projects)


def namespace_project_args(namespace_projects: dict) -> list[str]:
    return [f"{k}={v}" for k, v in namespace_projects.items() if str(k).strip() and str(v).strip()]


def load_product_config(config_path: str) -> dict:
    config_file = Path(config_path)
    if not config_file.exists():
        raise SystemExit(f"Config file not found: {config_path}")
    if not config_file.is_file():
        raise SystemExit(f"Config path is not a file: {config_path}")

    config = load_yaml_file(config_file, {})
    if not isinstance(config, dict):
        raise SystemExit(f"Invalid config file format: {config_path}")
    return config


def scalar_config_default_values() -> dict:
    return {
        "org": os.environ.get("KMAP_ORG", "org"),
        "product": os.environ.get("KMAP_PRODUCT", "product"),
        "project": os.environ.get("KMAP_PROJECT", ""),
        "env": os.environ.get("KMAP_ENV", "prod"),
        "data_mode": os.environ.get("KMAP_DATA_MODE", "sanitized"),
        "mock_seed": os.environ.get("KMAP_MOCK_SEED", ""),
        "render": os.environ.get("KMAP_RENDER", "both"),
    }


def apply_scalar_config_overrides(args: argparse.Namespace, config: dict) -> None:
    default_values = scalar_config_default_values()
    for field in default_values:
        if _should_apply_scalar_config_override(args, config, field, default_values[field]):
            setattr(args, field, config.get(field))


def _should_apply_scalar_config_override(
    args: argparse.Namespace,
    config: dict,
    field: str,
    default_value: str,
) -> bool:
    if not hasattr(args, field):
        return False
    current = getattr(args, field)
    configured = config.get(field)
    return current in {None, "", default_value} and configured not in {None, ""}


def validate_config(args: argparse.Namespace) -> int:
    config_path = Path(args.config_file)
    if not config_path.exists():
        eprint(f"[kmap] config validation failed: {config_path}")
        eprint("- config: file not found")
        return 1
    config = load_yaml_config_or_error(config_path)
    errors, warnings = validate_config_shape(config)
    if errors:
        eprint(f"[kmap] config validation failed: {config_path}")
        for error in errors:
            eprint(f"- {error}")
        if warnings:
            eprint("[kmap] warnings:")
            for warning in warnings:
                eprint(f"- {warning}")
        return 1
    eprint(f"[kmap] config ok: {config_path}")
    for warning in warnings:
        eprint(f"[kmap] warning: {warning}")
    return 0


__all__ = [
    "apply_config_overrides",
    "apply_namespace_config_overrides",
    "apply_scalar_config_overrides",
    "attach_config_metadata",
    "attach_empty_config_metadata",
    "load_product_config",
    "namespace_project_args",
    "scalar_config_default_values",
    "validate_config",
]
