"""Runtime dependency context for namespace workload inspection."""

from dataclasses import dataclass
from typing import Any, Dict, List

from ...inspection.buckets import workload_bucket_candidates
from ...inspection.dependencies.core import workload_dependency_candidates
from ...inspection.runtime import RuntimeEnvCollectionContext, runtime_env_maps
from ...kubernetes import workload_pods, workload_runtime_status
from .namespace_context import InspectionContext
from .observability import workload_observability_context
from .runtime_cache import with_cached_runtime_candidates


@dataclass
class RuntimeDependencyContext:
    runtime_status: Dict[str, Any]
    observability_context: Dict[str, Any]
    dependency_candidates: List[Dict[str, Any]]
    bucket_candidates: List[Dict[str, Any]]


@dataclass
class RuntimeDependencyInput:
    kind: str
    name: str
    workload: Dict[str, Any]
    network_context: Dict[str, Any]
    container_context: Dict[str, Any]


def runtime_dependency_context(
    *,
    context: InspectionContext,
    runtime_input: RuntimeDependencyInput,
) -> RuntimeDependencyContext:
    all_pods = workload_pods(context.resources["pod"], runtime_input.workload)
    runtime_env, vault_env = runtime_env_maps_for_pods(context, all_pods)
    candidates = workload_dependency_candidates(
        containers=runtime_input.container_context["containers"],
        referenced_configmaps=runtime_input.container_context["referenced_configmaps"],
        referenced_secrets=runtime_input.container_context["referenced_secrets"],
        configmaps=context.cm_map,
        secrets=context.sec_map,
        runtime_env=runtime_env,
        vault_env=vault_env,
        internal_alias_to_service=context.internal_alias_to_service,
    )
    bucket_candidates = workload_bucket_candidates(
        containers=runtime_input.container_context["containers"],
        referenced_configmaps=runtime_input.container_context["referenced_configmaps"],
        referenced_secrets=runtime_input.container_context["referenced_secrets"],
        configmaps=context.cm_map,
        secrets=context.sec_map,
        runtime_env=runtime_env,
        vault_env=vault_env,
    )
    return RuntimeDependencyContext(
        runtime_status=workload_runtime_status(runtime_input.workload, all_pods),
        observability_context=workload_observability_context(
            workload=runtime_input.workload,
            services=context.svc_items,
            matched_service_names=runtime_input.network_context["services"],
            containers=runtime_input.container_context["containers"],
            runtime_env=runtime_env,
            vault_env=vault_env,
        ),
        dependency_candidates=with_cached_runtime_candidates(
            candidates,
            context.previous_runtime_candidates,
            runtime_cache_key(context, runtime_input),
        ),
        bucket_candidates=bucket_candidates,
    )


def runtime_env_maps_for_pods(
    context: InspectionContext, pods: List[Dict[str, Any]]
) -> tuple[Dict[str, str], Dict[str, str]]:
    args = context.args
    return runtime_env_maps(
        RuntimeEnvCollectionContext(
            client=context.client,
            namespace=args.namespace,
            pods=pods,
            max_exec_pods_per_workload=args.max_exec_pods_per_workload,
            no_exec=args.no_exec,
        )
    )


def runtime_cache_key(
    context: InspectionContext,
    runtime_input: RuntimeDependencyInput,
) -> tuple[str, str, str, str]:
    return (context.cluster, context.args.namespace, runtime_input.kind, runtime_input.name)


__all__ = [
    "RuntimeDependencyContext",
    "RuntimeDependencyInput",
    "runtime_cache_key",
    "runtime_dependency_context",
    "runtime_env_maps_for_pods",
]
