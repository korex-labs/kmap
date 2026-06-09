"""Workload report-entry assembly for namespace inspection."""

from dataclasses import dataclass
from typing import Any, Dict, List

from ...inspection.workloads import workload_container_context
from ...kubernetes import (
    obj_name,
    pod_labels_from_template,
    selector_of_workload,
    workload_app_service,
    workload_scheduling_context,
    workload_security_context,
    workload_service_id,
)
from .namespace_context import InspectionContext
from .namespace_runtime import (
    RuntimeDependencyContext,
    RuntimeDependencyInput,
    runtime_cache_key,
    runtime_dependency_context,
    runtime_env_maps_for_pods,
)
from .network import workload_network_context
from .report import WorkloadReportEntryContext, workload_report_entry
from .storage import workload_storage_context


@dataclass
class InspectedWorkloadContext:
    name: str
    selector: Dict[str, Any]
    app_service: str
    app_service_source: Dict[str, Any]
    container_context: Dict[str, Any]
    network_context: Dict[str, Any]
    storage_context: Dict[str, Any]
    observability_context: Dict[str, Any]
    security_context: Dict[str, Any]
    scheduling_context: Dict[str, Any]
    runtime_status: Dict[str, Any]
    dependency_candidates: List[Dict[str, Any]]
    bucket_candidates: List[Dict[str, Any]]


@dataclass
class StaticWorkloadContext:
    name: str
    selector: Dict[str, Any]
    app_service: str
    app_service_source: Dict[str, Any]
    container_context: Dict[str, Any]
    network_context: Dict[str, Any]
    storage_context: Dict[str, Any]
    security_context: Dict[str, Any]
    scheduling_context: Dict[str, Any]


def build_inspected_workload_entry(
    *,
    context: InspectionContext,
    kind: str,
    workload: Dict[str, Any],
) -> Dict[str, Any]:
    return workload_report_entry(workload_report_entry_context(context, kind, workload))


def workload_report_entry_context(
    context: InspectionContext,
    kind: str,
    workload: Dict[str, Any],
) -> WorkloadReportEntryContext:
    args = context.args
    workload_context = inspected_workload_context(context, kind, workload)
    return WorkloadReportEntryContext(
        cluster=context.cluster,
        namespace=args.namespace,
        project=getattr(args, "project", ""),
        kind=kind,
        service_name=workload_context.name,
        service_id=workload_service_id(context.cluster, args.namespace, kind, workload_context.name),
        selector=workload_context.selector,
        app_service=workload_context.app_service,
        app_service_source=workload_context.app_service_source,
        container_context=workload_context.container_context,
        network_context=workload_context.network_context,
        storage_context=workload_context.storage_context,
        observability_context=workload_context.observability_context,
        security_context=workload_context.security_context,
        scheduling_context=workload_context.scheduling_context,
        runtime_status=workload_context.runtime_status,
        autoscaling=context.autoscaling_by_target.get((kind, workload_context.name), {}),
        release_names=context.release_names,
        replicasets_by_deployment=context.replicasets_by_deployment,
        dependency_candidates=workload_context.dependency_candidates,
        bucket_candidates=workload_context.bucket_candidates,
    )


def inspected_workload_context(
    context: InspectionContext,
    kind: str,
    workload: Dict[str, Any],
) -> InspectedWorkloadContext:
    static_context = static_workload_context(context, workload)
    runtime_context = runtime_dependency_context(
        context=context,
        runtime_input=RuntimeDependencyInput(
            kind=kind,
            name=static_context.name,
            workload=workload,
            network_context=static_context.network_context,
            container_context=static_context.container_context,
        ),
    )

    return InspectedWorkloadContext(
        name=static_context.name,
        selector=static_context.selector,
        app_service=static_context.app_service,
        app_service_source=static_context.app_service_source,
        container_context=static_context.container_context,
        network_context=static_context.network_context,
        storage_context=static_context.storage_context,
        observability_context=runtime_context.observability_context,
        security_context=static_context.security_context,
        scheduling_context=static_context.scheduling_context,
        runtime_status=runtime_context.runtime_status,
        dependency_candidates=runtime_context.dependency_candidates,
        bucket_candidates=runtime_context.bucket_candidates,
    )


def static_workload_context(context: InspectionContext, workload: Dict[str, Any]) -> StaticWorkloadContext:
    app_service, app_service_source = workload_app_service(workload)
    return StaticWorkloadContext(
        name=obj_name(workload),
        selector=selector_of_workload(workload) or pod_labels_from_template(workload),
        app_service=app_service,
        app_service_source=app_service_source,
        container_context=workload_container_context(workload),
        network_context=workload_network_context(
            workload, context.args.namespace, context.svc_items, context.ing_items
        ),
        storage_context=workload_storage_context(workload, context.resources["pvc"].get("items") or []),
        security_context=workload_security_context(workload),
        scheduling_context=workload_scheduling_context(workload),
    )


__all__ = [
    "InspectedWorkloadContext",
    "RuntimeDependencyContext",
    "RuntimeDependencyInput",
    "StaticWorkloadContext",
    "build_inspected_workload_entry",
    "inspected_workload_context",
    "runtime_cache_key",
    "runtime_dependency_context",
    "runtime_env_maps_for_pods",
    "static_workload_context",
    "workload_report_entry_context",
]
