"""Naming, IDs, aliases, display labels, and type inference."""

from ..config import infer_project_from_namespace, slug_name
from ..external.mappings import external_dependency_tag, generated_external_category, normalized_likec4_external_type
from ..identifiers import architecture_id, architecture_id_part, ident, q, short_hash
from .aliases import (
    alias_variants,
    namespace_alias_variants,
    service_name_alias_variants,
    service_reference_variants,
    short_service_name_variants,
)
from .context import (
    NamingContext,
    container_subsystem_name,
    naming_context_from_args,
    should_model_workload,
)
from .display import (
    clip_text,
    container_description,
    container_display_qualifier,
    dependency_display_name,
    dependency_heat_tag,
    display_container_name,
    display_system_name,
    display_title_from_discovered_name,
    display_title_from_discovered_name_with_context,
    endpoint_label,
    external_description,
    humanize_slug,
    is_url,
    short_label,
    should_collapse_container_title_to_app,
    slug_parts,
    view_key_suffix,
)
from .fallback import (
    apply_fallback_system_rewrites,
    canonical_fallback_system_name,
)
from .release import (
    matches_release_name,
    normalize_release_name,
)
from .types import (
    generated_system_category,
    normalized_likec4_internal_system_type,
)

__all__ = [
    "NamingContext",
    "alias_variants",
    "apply_fallback_system_rewrites",
    "architecture_id",
    "architecture_id_part",
    "canonical_fallback_system_name",
    "clip_text",
    "container_description",
    "container_display_qualifier",
    "container_subsystem_name",
    "dependency_display_name",
    "dependency_heat_tag",
    "display_container_name",
    "display_system_name",
    "display_title_from_discovered_name",
    "display_title_from_discovered_name_with_context",
    "endpoint_label",
    "external_dependency_tag",
    "external_description",
    "generated_external_category",
    "generated_system_category",
    "humanize_slug",
    "ident",
    "infer_project_from_namespace",
    "is_url",
    "matches_release_name",
    "namespace_alias_variants",
    "naming_context_from_args",
    "normalize_release_name",
    "normalized_likec4_external_type",
    "normalized_likec4_internal_system_type",
    "q",
    "service_name_alias_variants",
    "service_reference_variants",
    "short_hash",
    "short_label",
    "short_service_name_variants",
    "should_collapse_container_title_to_app",
    "should_model_workload",
    "slug_name",
    "slug_parts",
    "view_key_suffix",
]
