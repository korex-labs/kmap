"""External dependency target construction."""

from typing import Any, Dict, List

from ...config import clean_metadata_string
from ...external.mappings import (
    external_mapping_for_key,
    external_mapping_should_aggregate,
    generated_external_category,
)
from ...identifiers import architecture_id
from ...metadata import merge_database_metadata
from ...naming import display_title_from_discovered_name, endpoint_label
from ..external import append_metadata_value, external_identity_name, external_type_name, external_variable_title
from ..relationships import relation_origin_label
from .external_endpoints import ensure_external_endpoint_container
from .state import DependencyBuildState, ExternalIdentity, RelationContext, TargetResolution


def resolve_external_target(context: RelationContext, state: DependencyBuildState) -> TargetResolution:
    identity = external_identity(context, state.external_mappings)
    target_id = ensure_external_system(
        external_key=identity.external_key,
        external_name=identity.external_name,
        dep_key=context.dep_key,
        source_var=context.source_var,
        mapping=identity.mapping,
        aggregate_mapping=identity.aggregate_mapping,
        external_system_ids_by_key=state.external_system_ids_by_key,
        systems_by_id=state.systems_by_id,
    )
    record_external_metadata_for_identity(context, identity, state.systems_by_id.get(target_id))
    if identity.aggregate_mapping:
        target_id = external_endpoint_target(context, identity.mapping, target_id, state)
    return TargetResolution(
        target_id=target_id,
        category="external",
        boundary_kind="project_to_external",
        mapping=identity.mapping,
    )


def record_external_metadata_for_identity(
    context: RelationContext,
    identity: ExternalIdentity,
    system_entry: Dict[str, Any] | None,
) -> None:
    if not context.source_var or identity.aggregate_mapping:
        return
    record_external_variable_metadata(
        system_entry,
        source_var=context.source_var,
        dep_key=context.dep_key,
        source_origin=context.source_origin,
    )


def external_identity(context: RelationContext, external_mappings: List[Dict[str, Any]]) -> ExternalIdentity:
    mapping = external_mapping_for_key(context.dep_key, external_mappings)
    aggregate_mapping = external_mapping_should_aggregate(mapping, context.dep_key)
    external_name = external_identity_name(context.dep_key, context.source_var, mapping, aggregate_mapping)
    external_key = f"mapped:{mapping['name']}" if aggregate_mapping else external_name
    return ExternalIdentity(
        mapping=mapping,
        aggregate_mapping=aggregate_mapping,
        external_name=external_name,
        external_key=external_key,
    )


def external_endpoint_target(
    context: RelationContext,
    mapping: Dict[str, Any],
    target_system_id: str,
    state: DependencyBuildState,
) -> str:
    endpoint_name = endpoint_label(context.dep_key) or context.dep_key or "external"
    endpoint_container_id = ensure_external_endpoint_container(
        dep_key=context.dep_key,
        endpoint_name=endpoint_name,
        mapping=mapping,
        target_system_id=target_system_id,
        external_endpoint_container_ids_by_key=state.external_endpoint_container_ids_by_key,
        containers_by_id=state.containers_by_id,
    )
    merge_database_metadata(state.containers_by_id[endpoint_container_id], context.database_metadata)
    return endpoint_container_id


def ensure_external_system(
    *,
    external_key: str,
    external_name: str,
    dep_key: str,
    source_var: str,
    mapping: Dict[str, Any] | None,
    aggregate_mapping: bool,
    external_system_ids_by_key: Dict[str, str],
    systems_by_id: Dict[str, Dict[str, Any]],
) -> str:
    target_id = external_system_ids_by_key.get(external_key, "")
    if target_id:
        return target_id

    target_id = architecture_id("ext", external_name)
    external_system_ids_by_key[external_key] = target_id
    systems_by_id.setdefault(
        target_id,
        external_system_entry(
            target_id=target_id,
            external_name=external_name,
            dep_key=dep_key,
            source_var=source_var,
            mapping=mapping,
            aggregate_mapping=aggregate_mapping,
        ),
    )
    return target_id


def external_system_entry(
    *,
    target_id: str,
    external_name: str,
    dep_key: str,
    source_var: str,
    mapping: Dict[str, Any] | None,
    aggregate_mapping: bool,
) -> Dict[str, Any]:
    configured_tag = clean_metadata_string((mapping or {}).get("tag")) or "External System"
    detection_name = " ".join(part for part in (external_name, dep_key) if part)
    external_category = generated_external_category(detection_name, configured_tag)
    external_element_type = external_type_name(external_name, dep_key, mapping, aggregate_mapping, source_var)
    return {
        "id": target_id,
        "kind": "external",
        "element_type": external_element_type,
        "name": external_name,
        "title": external_system_title(
            external_name=external_name,
            source_var=source_var,
            mapping=mapping,
            aggregate_mapping=aggregate_mapping,
            external_element_type=external_element_type,
        ),
        "category": external_category,
        "tags": external_system_tags(external_category, configured_tag),
    }


def external_system_tags(external_category: str, configured_tag: str) -> List[str]:
    tags = ["External"]
    for tag in (external_category, configured_tag):
        if tag not in tags:
            tags.append(tag)
    return tags


def external_system_title(
    *,
    external_name: str,
    source_var: str,
    mapping: Dict[str, Any] | None,
    aggregate_mapping: bool,
    external_element_type: str,
) -> str:
    if source_var and not aggregate_mapping:
        return external_variable_title(source_var)
    title = external_name if mapping else (display_title_from_discovered_name(external_name) or external_name)
    if external_element_type == "Website":
        return external_name.lower()
    return title


def record_external_variable_metadata(
    system_entry: Dict[str, Any] | None, *, source_var: str, dep_key: str, source_origin: str
) -> None:
    if system_entry is None:
        return
    append_metadata_value(system_entry, "source_var", source_var)
    append_metadata_value(system_entry, "endpoint", dep_key)
    append_metadata_value(system_entry, "source_origin", relation_origin_label(source_origin))


__all__ = [
    "ensure_external_system",
    "external_endpoint_target",
    "external_identity",
    "external_system_entry",
    "external_system_tags",
    "external_system_title",
    "record_external_metadata_for_identity",
    "record_external_variable_metadata",
    "resolve_external_target",
]
