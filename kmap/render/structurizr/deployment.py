"""Structurizr deployment renderer."""

from dataclasses import dataclass
from typing import Any, Dict, List

from ...identifiers import q
from ...metadata import container_runtime_metadata_pairs, runtime_metadata_pairs
from ...rendering_resources import short_join_unique
from ..deployment_groups import (
    append_unique,
    merged_instance_runtime,
    pod_display_titles,
    pod_groups,
    pod_system_titles,
)
from . import structurizr_properties_lines
from .references import structurizr_reference_map


@dataclass
class _DeploymentRenderContext:
    refs: Dict[str, str]
    containers_by_id: Dict[str, Dict[str, Any]]
    systems_by_id: Dict[str, Dict[str, Any]]
    projects_by_id: Dict[str, Dict[str, Any]]


def _container_title(container: Dict[str, Any], instance: Dict[str, Any]) -> str:
    return container.get("title") or container.get("name") or instance.get("name") or "container"


def _replicas(instances: List[Dict[str, Any]]) -> str:
    values: List[str] = []
    for instance in instances:
        replica_values = [instance.get("replicas")]
        runtime = instance.get("runtime") or {}
        replica_values.extend(runtime.get("replicas_desired") or [])
        for replicas in replica_values:
            if isinstance(replicas, int) and replicas > 0:
                append_unique(values, str(replicas))
            elif isinstance(replicas, str) and replicas.strip().isdigit():
                append_unique(values, replicas.strip())
    return values[0] if len(values) == 1 else ""


def _cluster_description(cluster: Dict[str, Any]) -> str:
    name = cluster.get("name") or cluster.get("title") or cluster.get("id") or "cluster"
    return f"Kubernetes cluster: {name}"


def _namespace_description(namespace: Dict[str, Any], project: Dict[str, Any]) -> str:
    name = namespace.get("name") or namespace.get("id") or "namespace"
    project_title = project.get("title") or project.get("name") or ""
    if project_title:
        return f"Kubernetes namespace: {name}; project: {project_title}"
    return f"Kubernetes namespace: {name}"


def _pod_description(pod_group: Dict[str, Any], systems: List[str]) -> str:
    system_summary = short_join_unique(systems)
    if system_summary:
        return f"Kubernetes workload: {pod_group['title']}; system: {system_summary}"
    return f"Kubernetes workload: {pod_group['title']}"


def render_structurizr_deployment(architecture: Dict[str, Any], deployment: Dict[str, Any]) -> str:
    env = deployment.get("env") or "env"
    context = _deployment_render_context(architecture)
    lines = [f'deploymentEnvironment "{q(env)}" {{']
    for cluster in deployment.get("clusters") or []:
        lines.extend(_cluster_lines(cluster, context))
    lines.append("}")
    return "\n".join(lines) + "\n"


def _deployment_render_context(architecture: Dict[str, Any]) -> _DeploymentRenderContext:
    return _DeploymentRenderContext(
        refs=structurizr_reference_map(architecture),
        containers_by_id={container.get("id"): container for container in architecture.get("containers") or []},
        systems_by_id={system.get("id"): system for system in architecture.get("systems") or []},
        projects_by_id={project.get("id"): project for project in architecture.get("projects") or []},
    )


def _cluster_lines(cluster: Dict[str, Any], context: _DeploymentRenderContext) -> List[str]:
    cluster_title = cluster.get("title") or cluster.get("name") or cluster.get("id") or "cluster"
    lines = [
        f'    deploymentNode "{q(cluster_title)}" "{q(_cluster_description(cluster))}" "Kubernetes Cluster" {{',
        '        tags "K8s"',
        *structurizr_properties_lines(
            [
                ("cluster", cluster.get("name") or cluster_title),
            ],
            indent="        ",
        ),
    ]
    for namespace in cluster.get("namespaces") or []:
        lines.extend(_namespace_lines(namespace, context))
    lines.append("    }")
    return lines


def _namespace_lines(namespace: Dict[str, Any], context: _DeploymentRenderContext) -> List[str]:
    namespace_title = namespace.get("name") or namespace.get("id") or "namespace"
    project = context.projects_by_id.get(namespace.get("project_id") or "") or {}
    lines = [
        f'        deploymentNode "Namespace: {q(namespace_title)}" '
        f'"{q(_namespace_description(namespace, project))}" "Kubernetes Namespace" {{',
        *structurizr_properties_lines(
            [
                ("namespace", namespace.get("name") or namespace_title),
                ("project", project.get("name") or ""),
                ("project_title", project.get("title") or ""),
            ],
            indent="            ",
        ),
    ]
    grouped_pods = pod_groups(namespace.get("instances") or [])
    display_titles = pod_display_titles(grouped_pods, context.containers_by_id, context.systems_by_id)
    for pod_group in grouped_pods:
        lines.extend(_pod_lines(pod_group, display_titles, context))
    lines.append("        }")
    return lines


def _pod_lines(
    pod_group: Dict[str, Any],
    display_titles: Dict[str, str],
    context: _DeploymentRenderContext,
) -> List[str]:
    systems = pod_system_titles(pod_group, context.containers_by_id, context.systems_by_id)
    pod_title = display_titles.get(pod_group["id"]) or pod_group["title"]
    lines = [
        f'            deploymentNode "Deployment: {q(pod_title)}" '
        f'"{q(_pod_description(pod_group, systems))}" "Kubernetes Pod" {{'
    ]
    replicas = _replicas(pod_group["instances"])
    if replicas:
        lines.append(f"                instances {replicas}")
    lines.extend(
        structurizr_properties_lines(
            [
                ("workload", pod_group["title"]),
                ("system", short_join_unique(systems)),
                ("node_kind", short_join_unique(pod_group["node_kinds"])),
                *runtime_metadata_pairs(merged_instance_runtime(pod_group["instances"])),
            ],
            indent="                ",
        )
    )
    for instance in pod_group["instances"]:
        lines.extend(_container_instance_lines(instance, context))
    lines.append("            }")
    return lines


def _container_instance_lines(instance: Dict[str, Any], context: _DeploymentRenderContext) -> List[str]:
    container_id = instance.get("container_id") or ""
    container_ref = context.refs.get(container_id)
    if not container_ref:
        return []
    container = context.containers_by_id.get(container_id) or {}
    return [
        f"                containerInstance {container_ref} {{",
        *structurizr_properties_lines(
            [
                ("container", _container_title(container, instance)),
                ("container_kind", container.get("kind") or ""),
                *container_runtime_metadata_pairs(container),
            ],
            indent="                    ",
        ),
        "                }",
    ]


__all__ = ["render_structurizr_deployment"]
