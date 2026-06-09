"""LikeC4 deployment renderer."""

from typing import Any, Dict, List

from ...metadata import container_runtime_metadata_pairs, runtime_metadata_pairs
from ...rendering_resources import short_join_unique
from ..deployment_groups import merged_instance_runtime, pod_display_titles, pod_groups, pod_system_titles
from .common import likec4_alias, likec4_metadata_lines, likec4_quote
from .deployment_context import DeploymentRenderContext, deployment_render_context, has_scaling
from .deployment_routes import namespace_flows, route_graph, route_hops, route_lines
from .metadata import grouped_runtime_metadata_items


def _stage_header_lines(env_alias: str, env: str, product_name: str) -> List[str]:
    lines = [
        "deployment {",
        f'  {env_alias} = Stage "{likec4_quote(env)}" {{',
    ]
    lines.extend(
        likec4_metadata_lines(
            [
                ("product", product_name),
                ("env", env),
            ],
            indent="    ",
        )
    )
    lines.append("")
    return lines


def _cluster_lines(
    cluster: Dict[str, Any],
    context: DeploymentRenderContext,
) -> List[str]:
    cluster_alias = likec4_alias(cluster.get("id") or cluster.get("name") or "cluster")
    cluster_title = cluster.get("title") or cluster.get("name") or cluster_alias
    lines = [f'    {cluster_alias} = k8s_cluster "{likec4_quote(cluster_title)}" {{']
    lines.extend(
        likec4_metadata_lines(
            [
                ("cluster", cluster.get("name") or cluster_title),
            ],
            indent="      ",
        )
    )
    for namespace in cluster.get("namespaces") or []:
        lines.extend(_namespace_lines(cluster, namespace, context))
    lines.append("    }")
    return lines


def _namespace_lines(
    cluster: Dict[str, Any],
    namespace: Dict[str, Any],
    context: DeploymentRenderContext,
) -> List[str]:
    namespace_alias = likec4_alias(namespace.get("id") or namespace.get("name") or "namespace")
    namespace_title = namespace.get("name") or namespace_alias
    project = context.projects_by_id.get(namespace.get("project_id") or "") or {}
    lines = [f'      {namespace_alias} = k8s_namespace "{likec4_quote(namespace_title)}" {{']
    lines.extend(
        likec4_metadata_lines(
            [
                ("namespace", namespace.get("name") or namespace_title),
                ("project", project.get("name") or ""),
                ("project_title", project.get("title") or ""),
            ],
            indent="        ",
        )
    )

    grouped_pods = pod_groups(namespace.get("instances") or [])
    display_titles = pod_display_titles(grouped_pods, context.containers_by_id, context.systems_by_id)
    instance_aliases: Dict[str, str] = {}
    for pod_group in grouped_pods:
        pod_alias = likec4_alias(pod_group["id"])
        for instance in pod_group["instances"]:
            instance_aliases[instance.get("id")] = pod_alias
        lines.extend(_pod_group_lines(pod_group, pod_alias, display_titles, context))

    routed_flows = namespace_flows(context.traffic_flows, cluster, namespace)
    lines.extend(route_lines(routed_flows, instance_aliases))
    lines.append("      }")
    return lines


def _pod_group_lines(
    pod_group: Dict[str, Any],
    pod_alias: str,
    display_titles: Dict[str, str],
    context: DeploymentRenderContext,
) -> List[str]:
    systems = pod_system_titles(pod_group, context.containers_by_id, context.systems_by_id)
    pod_title = display_titles.get(pod_group["id"]) or pod_group["title"]
    instance_runtime = merged_instance_runtime(pod_group["instances"])
    lines = [f'        {pod_alias} = k8s_pod "{likec4_quote(pod_title)}" {{']
    lines.append('          technology "Kubernetes Pod"')
    lines.extend(
        likec4_metadata_lines(
            grouped_runtime_metadata_items(
                [
                    ("workload", pod_group["title"]),
                    ("system", short_join_unique(systems)),
                    ("node_kind", short_join_unique(pod_group["node_kinds"])),
                    *runtime_metadata_pairs(instance_runtime),
                ],
                preserve_keys=("workload", "system", "node_kind"),
            ),
            indent="          ",
        )
    )
    if has_scaling(instance_runtime):
        lines.extend(["          style {", "            multiple true", "          }"])
    for instance in pod_group["instances"]:
        lines.extend(_container_instance_lines(instance, context.containers_by_id, context.refs))
    lines.append("        }")
    return lines


def _container_instance_lines(
    instance: Dict[str, Any],
    containers_by_id: Dict[str, Dict[str, Any]],
    refs: Dict[str, str],
) -> List[str]:
    container_id = instance.get("container_id") or ""
    container = containers_by_id.get(container_id) or {}
    container_alias = refs.get(container_id)
    container_instance_runtime = instance.get("runtime") or {}
    container_instance_alias = likec4_alias(f"{instance.get('id') or container_id}_container")
    container_title = container.get("title") or container.get("name") or instance.get("name") or "container"
    lines = [f'          {container_instance_alias} = k8s_container "{likec4_quote(container_title)}" {{']
    lines.extend(
        likec4_metadata_lines(
            grouped_runtime_metadata_items(
                [
                    ("container", container.get("title") or container.get("name") or ""),
                    ("container_kind", container.get("kind") or ""),
                    *container_runtime_metadata_pairs(container),
                ],
                preserve_keys=("container", "container_kind"),
            ),
            indent="            ",
        )
    )
    if container_alias:
        lines.extend(_instance_of_lines(container_alias, container_instance_runtime))
    lines.append("          }")
    return lines


def _instance_of_lines(container_alias: str, runtime: Dict[str, Any]) -> List[str]:
    if not has_scaling(runtime):
        return [f"            instanceOf {container_alias}"]

    lines = [f"            instanceOf {container_alias} {{"]
    lines.extend(
        [
            "              style {",
            "                multiple true",
            "              }",
            "            }",
        ]
    )
    return lines


def render_likec4_deployment(architecture: Dict[str, Any], deployment: Dict[str, Any]) -> str:
    env = deployment.get("env") or "env"
    product = architecture.get("product") or {}
    product_name = product.get("name") or "product"
    env_alias = likec4_alias(f"{product_name}_{env}")
    context = deployment_render_context(architecture)

    lines = _stage_header_lines(env_alias, env, product_name)
    for cluster in deployment.get("clusters") or []:
        lines.extend(_cluster_lines(cluster, context))
    lines.append("  }")
    lines.append("}")
    return "\n".join(lines) + "\n"


__all__ = [
    "DeploymentRenderContext",
    "deployment_render_context",
    "render_likec4_deployment",
    "route_graph",
    "route_hops",
]
