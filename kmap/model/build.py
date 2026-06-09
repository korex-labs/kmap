"""Normalized architecture model construction."""

from pathlib import Path
from typing import Any, Dict, List

from ..config import (
    normalize_dependency_hotspots_config,
    normalize_system_naming_config,
)
from ..external.mappings import (
    load_external_mapping_summaries,
    load_external_mappings,
)
from ..identifiers import architecture_id
from ..naming import naming_context_from_args
from ..relations import load_dependency_relations
from .assembly import (
    ArchitectureDocumentContext,
    architecture_document_from_context,
    deployment_entries_from_envs,
    traffic_flows_from_workloads,
)
from .build_state import ConfigInputs, DependencyInputs, ModelBuildState, ProductContext
from .dependencies import build_dependency_relationships
from .internal import apply_single_system_project_overrides
from .metadata import generator_metadata, utc_timestamp
from .reports import load_workloads_from_reports
from .workloads import process_workload


def architecture_model_from_reports(args) -> Dict[str, Any]:
    json_files, workloads = _load_report_inputs(args)
    product = _product_context(args)
    config_inputs = _load_config_inputs(args)
    dependency_inputs = _load_dependency_inputs(args)
    state = ModelBuildState()

    _process_workloads(workloads, product, config_inputs, state)
    apply_single_system_project_overrides(state.systems_by_id, state.projects_by_id, config_inputs.project_metadata)

    return _architecture_document(
        args=args,
        product=product,
        config_inputs=config_inputs,
        dependency_inputs=dependency_inputs,
        state=state,
        report_count=len(json_files),
        workload_count=len(workloads),
    )


def _load_report_inputs(args) -> tuple[List[Path], List[Dict[str, Any]]]:
    return load_workloads_from_reports(Path(args.reports_dir))


def _product_context(args) -> ProductContext:
    naming = naming_context_from_args(args)
    product_name = naming.product or "product"
    return ProductContext(
        naming=naming,
        product_name=product_name,
        product_id=architecture_id("prod", product_name),
        product_metadata=dict(getattr(args, "product_metadata", {}) or {}),
        generated_at=utc_timestamp(),
        generator=generator_metadata(getattr(args, "config", "") or "", "architecture"),
        env=naming.env or "prod",
    )


def _process_workloads(
    workloads: List[Dict[str, Any]],
    product: ProductContext,
    config_inputs: ConfigInputs,
    state: ModelBuildState,
) -> None:
    deployment = state.deployment_for(product.env)
    for svc in workloads:
        process_workload(
            svc=svc,
            naming=product.naming,
            product_name=product.product_name,
            product_id=product.product_id,
            product_metadata=product.product_metadata,
            project_metadata=config_inputs.project_metadata,
            config_namespace_projects=config_inputs.config_namespace_projects,
            system_naming_config=config_inputs.system_naming_config,
            env=product.env,
            deployment=deployment,
            projects_by_id=state.projects_by_id,
            systems_by_id=state.systems_by_id,
            containers_by_id=state.containers_by_id,
            workload_project_ids=state.workload_project_ids,
            workload_primary_container_ids=state.workload_primary_container_ids,
            workload_primary_instance_ids=state.workload_primary_instance_ids,
            workloads_by_service_id=state.workloads_by_service_id,
        )


def _architecture_document(
    *,
    args: Any,
    product: ProductContext,
    config_inputs: ConfigInputs,
    dependency_inputs: DependencyInputs,
    state: ModelBuildState,
    report_count: int,
    workload_count: int,
) -> Dict[str, Any]:
    relationships = _dependency_relationships(dependency_inputs, state)
    traffic_flows = _traffic_flows(state)
    return architecture_document_from_context(
        ArchitectureDocumentContext(
            naming=product.naming,
            product_id=product.product_id,
            product_name=product.product_name,
            product_metadata=product.product_metadata,
            generated_at=product.generated_at,
            generator=product.generator,
            config_file=getattr(args, "config", "") or "",
            discovery_config=config_inputs.discovery_config,
            projects_by_id=state.projects_by_id,
            systems_by_id=state.systems_by_id,
            containers_by_id=state.containers_by_id,
            relationships=relationships,
            traffic_flows=traffic_flows,
            deployments=deployment_entries_from_envs(state.deployments_by_env),
            external_mapping_summaries=dependency_inputs.external_mapping_summaries,
            dependency_hotspots_config=config_inputs.dependency_hotspots_config,
            report_count=report_count,
            workload_count=workload_count,
        )
    )


def _dependency_relationships(
    dependency_inputs: DependencyInputs,
    state: ModelBuildState,
) -> List[Dict[str, Any]]:
    return build_dependency_relationships(
        dependency_relations=dependency_inputs.dependency_relations,
        workload_primary_container_ids=state.workload_primary_container_ids,
        workload_project_ids=state.workload_project_ids,
        external_mappings=dependency_inputs.external_mappings,
        systems_by_id=state.systems_by_id,
        containers_by_id=state.containers_by_id,
    )


def _traffic_flows(state: ModelBuildState) -> List[Dict[str, Any]]:
    return traffic_flows_from_workloads(
        state.workloads_by_service_id,
        state.workload_primary_container_ids,
        state.workload_primary_instance_ids,
    )


def _load_config_inputs(args) -> ConfigInputs:
    return ConfigInputs(
        project_metadata=dict(getattr(args, "project_metadata", {}) or {}),
        config_namespace_projects=dict(getattr(args, "config_namespace_projects", {}) or {}),
        system_naming_config=dict(getattr(args, "system_naming_config", {}) or normalize_system_naming_config({})),
        dependency_hotspots_config=dict(
            getattr(args, "dependency_hotspots_config", {}) or normalize_dependency_hotspots_config({})
        ),
        discovery_config=dict(getattr(args, "discovery_config", {}) or {}),
    )


def _load_dependency_inputs(args) -> DependencyInputs:
    config_path = getattr(args, "config", None)
    return DependencyInputs(
        external_mappings=load_external_mappings(config_path),
        external_mapping_summaries=load_external_mapping_summaries(config_path),
        dependency_relations=load_dependency_relations(getattr(args, "dependencies_file", "")),
    )


__all__ = [
    "architecture_model_from_reports",
    "generator_metadata",
    "utc_timestamp",
]
