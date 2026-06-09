"""Deployment collection assembly helpers."""

from typing import Any, Dict, List


def deployment_entries_from_envs(deployments_by_env: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    deployments = []
    for dep in deployments_by_env.values():
        clusters = []
        for cluster in dep["clusters"].values():
            namespaces = list(cluster["namespaces"].values())
            namespaces.sort(key=lambda item: item.get("name", ""))
            cluster = dict(cluster)
            cluster["namespaces"] = namespaces
            clusters.append(cluster)
        clusters.sort(key=lambda item: item.get("name", ""))
        deployments.append(
            {
                "env": dep["env"],
                "clusters": clusters,
            }
        )
    return sorted(deployments, key=lambda item: item["env"])


__all__ = ["deployment_entries_from_envs"]
