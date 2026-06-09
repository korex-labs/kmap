"""LikeC4 deployment view rendering helpers."""

from typing import Any, Dict, List

from ..deployment_groups import pod_groups
from .common import likec4_alias
from .views_shared import quote, view_footer_lines, view_title


def deployment_view_lines(product_name: str, deployments: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for deployment in deployments:
        env = deployment.get("env") or "env"
        env_alias = likec4_alias(f"{product_name}_{env}")
        lines.extend(
            [
                f"  deployment view {likec4_alias(product_name + '_' + env + '_deployment')} {{",
                f'    title "{quote(view_title("Deployments", product_name, env))}"',
            ]
        )
        lines.extend(deployment_cluster_include_lines(env_alias, deployment.get("clusters") or []))
        lines.extend(view_footer_lines("TopBottom"))
        lines.extend(deployment_container_drilldown_view_lines(product_name, env, env_alias, deployment))
    return lines


def deployment_container_drilldown_view_lines(
    product_name: str,
    env: str,
    env_alias: str,
    deployment: Dict[str, Any],
) -> List[str]:
    lines: List[str] = []
    for cluster in deployment.get("clusters") or []:
        cluster_alias = likec4_alias(cluster.get("id") or cluster.get("name") or "cluster")
        cluster_ref = f"{env_alias}.{cluster_alias}"
        for namespace in cluster.get("namespaces") or []:
            namespace_alias = likec4_alias(namespace.get("id") or namespace.get("name") or "namespace")
            namespace_ref = f"{cluster_ref}.{namespace_alias}"
            for pod_group in pod_groups(namespace.get("instances") or []):
                lines.extend(
                    deployment_pod_container_view_lines(
                        product_name=product_name,
                        env=env,
                        cluster_alias=cluster_alias,
                        namespace_alias=namespace_alias,
                        namespace_ref=namespace_ref,
                        pod_group=pod_group,
                    )
                )
    return lines


def deployment_pod_container_view_lines(
    *,
    product_name: str,
    env: str,
    cluster_alias: str,
    namespace_alias: str,
    namespace_ref: str,
    pod_group: Dict[str, Any],
) -> List[str]:
    pod_alias = likec4_alias(pod_group["id"])
    pod_ref = f"{namespace_ref}.{pod_alias}"
    view_alias = likec4_alias(f"{product_name}_{env}_{cluster_alias}_{namespace_alias}_{pod_alias}_containers")
    return [
        f"  deployment view {view_alias} {{",
        f'    title "{quote(view_title("Deployments", product_name, env, pod_group["title"], "Containers"))}"',
        f"    include {pod_ref}",
        f"    include {pod_ref}.*",
        "    autoLayout LeftRight",
        "  }",
        "",
    ]


def deployment_cluster_include_lines(env_alias: str, clusters: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = []
    for cluster in clusters:
        cluster_alias = likec4_alias(cluster.get("id") or cluster.get("name") or "cluster")
        cluster_ref = f"{env_alias}.{cluster_alias}"
        lines.append(f"    include {cluster_ref}")
        for namespace in cluster.get("namespaces") or []:
            lines.extend(deployment_namespace_include_lines(cluster_ref, namespace))
    return lines


def deployment_namespace_include_lines(cluster_ref: str, namespace: Dict[str, Any]) -> List[str]:
    namespace_alias = likec4_alias(namespace.get("id") or namespace.get("name") or "namespace")
    namespace_ref = f"{cluster_ref}.{namespace_alias}"
    lines = [f"    include {namespace_ref}"]
    lines.extend(
        f"    include {namespace_ref}.{likec4_alias(pod_group['id'])}"
        for pod_group in pod_groups(namespace.get("instances") or [])
    )
    return lines


__all__ = [
    "deployment_cluster_include_lines",
    "deployment_container_drilldown_view_lines",
    "deployment_namespace_include_lines",
    "deployment_pod_container_view_lines",
    "deployment_view_lines",
]
