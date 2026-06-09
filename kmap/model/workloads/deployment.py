"""Deployment namespace construction for workload instances."""

from typing import Any, Dict

from ...config import clean_metadata_string
from ...identifiers import architecture_id


def ensure_deployment_namespace(
    *,
    svc: Dict[str, Any],
    env: str,
    namespace: str,
    project_id: str,
    deployment: Dict[str, Any],
) -> tuple[str, Dict[str, Any]]:
    cluster_name = clean_metadata_string(svc.get("cluster")) or "cluster"
    cluster_id = architecture_id("cluster", env, cluster_name)
    cluster = deployment["clusters"].setdefault(
        cluster_id,
        {
            "id": cluster_id,
            "name": cluster_name,
            "title": cluster_name,
            "namespaces": {},
        },
    )
    namespace_id = architecture_id("ns", namespace or "namespace")
    namespace_entry = cluster["namespaces"].setdefault(
        namespace_id,
        {
            "id": namespace_id,
            "name": namespace,
            "project_id": project_id,
            "instances": [],
        },
    )
    return cluster_name, namespace_entry


__all__ = ["ensure_deployment_namespace"]
