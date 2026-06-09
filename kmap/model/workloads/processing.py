"""Workload-to-model construction helpers."""

from typing import Any, Dict

from ...config import clean_metadata_string
from ...identifiers import architecture_id
from ...metadata import update_container_runtime_metadata
from ...naming import should_model_workload
from ..inventory import architecture_container_inventory
from ..projects import record_project_namespace_discovery
from .context import (
    APP_SERVICE_ANNOTATION,
    configured_system_title_from_project,
    resolved_project_name,
    resolved_system_name_and_source,
)
from .deployment import ensure_deployment_namespace
from .entries import (
    WorkloadContainerEntryOptions,
    WorkloadInstanceOptions,
    append_workload_instance,
    container_entry,
    record_container_discovery,
    resolved_container_title,
    set_primary_workload_id,
)
from .processing_context import ensure_system, workload_context
from .processing_state import ContainerProcessContext, ModelIndexes, WorkloadContext, WorkloadInputs


def process_workload(**kwargs: Any) -> None:
    inputs = WorkloadInputs.from_kwargs(kwargs)
    indexes = ModelIndexes.from_kwargs(kwargs)
    _process_workload(inputs, indexes)


def _process_workload(inputs: WorkloadInputs, indexes: ModelIndexes) -> None:
    svc = inputs.svc
    if not should_model_workload(svc):
        return

    service_id = clean_metadata_string(svc.get("service_id"))
    if service_id:
        indexes.workloads_by_service_id[service_id] = svc
    context = workload_context(inputs, indexes, service_id)
    if service_id:
        indexes.workload_project_ids[service_id] = context.project_id
    record_project_namespace_discovery(
        context.project,
        namespace=context.namespace,
        cluster=svc.get("cluster") or "",
        project_meta=context.project_meta,
        report_discovery=svc.get("discovery") or {},
    )

    ensure_system(inputs, indexes, context)

    cluster_name, namespace_entry = ensure_deployment_namespace(
        svc=svc,
        env=inputs.env,
        namespace=context.namespace,
        project_id=context.project_id,
        deployment=inputs.deployment,
    )

    for container in architecture_container_inventory(svc):
        _process_container(
            ContainerProcessContext(
                container=container,
                cluster_name=cluster_name,
                namespace_entry=namespace_entry,
            ),
            inputs,
            indexes,
            context,
        )


def _process_container(
    container_context: ContainerProcessContext,
    inputs: WorkloadInputs,
    indexes: ModelIndexes,
    context: WorkloadContext,
) -> None:
    container = container_context.container
    raw_container_name = clean_metadata_string(container.get("name")) or "container"
    container_id = architecture_id(
        "ctr",
        inputs.product_name,
        context.project_name,
        context.system_name,
        raw_container_name,
    )
    set_primary_workload_id(indexes.workload_primary_container_ids, context.service_id, container_id)
    indexes.containers_by_id.setdefault(
        container_id,
        _container_entry(container_id, container, inputs, context, raw_container_name),
    )
    entry = indexes.containers_by_id[container_id]
    record_container_discovery(entry, inputs.svc, context.namespace, container_context.cluster_name)
    update_container_runtime_metadata(entry, inputs.svc, container)
    instance_id = _append_workload_instance(
        inputs=inputs,
        context=context,
        namespace_entry=container_context.namespace_entry,
        raw_container_name=raw_container_name,
        container_id=container_id,
    )
    set_primary_workload_id(indexes.workload_primary_instance_ids, context.service_id, instance_id)


def _append_workload_instance(
    *,
    inputs: WorkloadInputs,
    context: WorkloadContext,
    namespace_entry: Dict[str, Any],
    raw_container_name: str,
    container_id: str,
) -> str:
    return append_workload_instance(
        namespace_entry,
        WorkloadInstanceOptions(
            env=inputs.env,
            project_name=context.project_name,
            system_name=context.system_name,
            svc=inputs.svc,
            raw_container_name=raw_container_name,
            container_id=container_id,
        ),
    )


def _container_entry(
    container_id: str,
    container: Dict[str, Any],
    inputs: WorkloadInputs,
    context: WorkloadContext,
    raw_container_name: str,
) -> Dict[str, Any]:
    return container_entry(
        WorkloadContainerEntryOptions(
            container_id=container_id,
            container=container,
            product_id=inputs.product_id,
            project_id=context.project_id,
            system_id=context.system_id,
            system_name=context.system_name,
            project_name=context.project_name,
            product_name=inputs.product_name,
            product_metadata=inputs.product_metadata,
            system_title=context.system_title,
            system_element_type=context.system_element_type,
            system_category=context.system_category,
            raw_container_name=raw_container_name,
        )
    )


__all__ = [
    "APP_SERVICE_ANNOTATION",
    "configured_system_title_from_project",
    "ensure_deployment_namespace",
    "process_workload",
    "resolved_container_title",
    "resolved_project_name",
    "resolved_system_name_and_source",
]
