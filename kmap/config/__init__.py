"""Product config normalization and validation."""

from .core import (
    apply_config_overrides,
    apply_namespace_config_overrides,
    apply_scalar_config_overrides,
    attach_config_metadata,
    attach_empty_config_metadata,
    load_product_config,
    namespace_project_args,
    scalar_config_default_values,
    validate_config,
)
from .discovery import normalize_discovery_config, resolve_discovery_target
from .metadata import (
    clean_metadata_resources,
    clean_metadata_string,
    clean_metadata_tags,
    merge_project_metadata,
    normalize_project_metadata_item,
)
from .names import slug_name
from .options import (
    clean_bool,
    clean_int,
    normalize_dependency_hotspots_config,
    normalize_system_naming_config,
)
from .projects import (
    infer_project_from_namespace,
    normalize_config_metadata,
    normalize_namespace_config,
)
from .validation import LIKEC4_EXTERNAL_ELEMENT_TYPES, validate_config_shape, validate_url_like

__all__ = [
    "LIKEC4_EXTERNAL_ELEMENT_TYPES",
    "apply_config_overrides",
    "apply_namespace_config_overrides",
    "apply_scalar_config_overrides",
    "attach_config_metadata",
    "attach_empty_config_metadata",
    "clean_bool",
    "clean_int",
    "clean_metadata_resources",
    "clean_metadata_string",
    "clean_metadata_tags",
    "infer_project_from_namespace",
    "load_product_config",
    "merge_project_metadata",
    "namespace_project_args",
    "normalize_config_metadata",
    "normalize_dependency_hotspots_config",
    "normalize_discovery_config",
    "normalize_namespace_config",
    "normalize_project_metadata_item",
    "normalize_system_naming_config",
    "resolve_discovery_target",
    "scalar_config_default_values",
    "slug_name",
    "validate_config",
    "validate_config_shape",
    "validate_url_like",
]
