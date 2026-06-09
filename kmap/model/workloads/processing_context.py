"""Workload processing context builders."""

from ...config import clean_metadata_string
from ...identifiers import architecture_id
from ...naming import (
    display_title_from_discovered_name_with_context,
    generated_system_category,
    normalized_likec4_internal_system_type,
)
from ..projects import project_entry
from .context import (
    configured_system_title_from_project,
    resolved_project_name,
    resolved_system_name_and_source,
)
from .processing_state import ModelIndexes, WorkloadContext, WorkloadInputs


def workload_context(inputs: WorkloadInputs, indexes: ModelIndexes, service_id: str) -> WorkloadContext:
    namespace = clean_metadata_string(inputs.svc.get("namespace"))
    project_name = resolved_project_name(
        svc=inputs.svc,
        naming=inputs.naming,
        product_name=inputs.product_name,
        namespace=namespace,
        config_namespace_projects=inputs.config_namespace_projects,
    )
    project_id = architecture_id("prj", inputs.product_name, project_name)
    project_meta = dict(inputs.project_metadata.get(project_name, {}))
    project = indexes.projects_by_id.setdefault(
        project_id,
        project_entry(
            project_id=project_id,
            product_id=inputs.product_id,
            project_name=project_name,
            product_metadata=inputs.product_metadata,
            project_meta=project_meta,
        ),
    )
    raw_service_name = clean_metadata_string(inputs.svc.get("service_name")) or "workload"
    system_name, system_name_source = resolved_system_name_and_source(
        svc=inputs.svc,
        raw_service_name=raw_service_name,
        product_name=inputs.product_name,
        project_name=project_name,
        system_naming_config=inputs.system_naming_config,
    )
    system_category = generated_system_category(system_name, project_name)
    configured_system_title = configured_system_title_from_project(project, project_meta)
    system_title = configured_system_title or display_title_from_discovered_name_with_context(
        system_name,
        inputs.product_name,
        project_name,
        inputs.product_metadata,
    )
    return WorkloadContext(
        service_id=service_id,
        namespace=namespace,
        project_name=project_name,
        project_id=project_id,
        project=project,
        project_meta=project_meta,
        system_name=system_name,
        system_name_source=system_name_source,
        system_id=architecture_id("sys", inputs.product_name, project_name, system_name),
        system_title=system_title,
        system_category=system_category,
        system_element_type=normalized_likec4_internal_system_type(system_name, project_name),
    )


def ensure_system(inputs: WorkloadInputs, indexes: ModelIndexes, context: WorkloadContext) -> None:
    indexes.systems_by_id.setdefault(
        context.system_id,
        {
            "id": context.system_id,
            "product_id": inputs.product_id,
            "project_id": context.project_id,
            "kind": "internal",
            "element_type": context.system_element_type,
            "name": context.system_name,
            "title": context.system_title or context.system_name,
            "category": context.system_category,
            "tags": ["Internal", "Generated", context.system_category],
            "name_source": context.system_name_source,
        },
    )


__all__ = ["ensure_system", "workload_context"]
