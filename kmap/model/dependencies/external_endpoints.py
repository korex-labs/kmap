"""External endpoint container construction for dependency modeling."""

from typing import Any, Dict

from ...identifiers import architecture_id
from ...naming import dependency_display_name, external_description


def ensure_external_endpoint_container(
    *,
    dep_key: str,
    endpoint_name: str,
    mapping: Dict[str, Any],
    target_system_id: str,
    external_endpoint_container_ids_by_key: Dict[str, str],
    containers_by_id: Dict[str, Dict[str, Any]],
) -> str:
    endpoint_container_id = external_endpoint_container_ids_by_key.get(dep_key, "")
    if endpoint_container_id:
        return endpoint_container_id

    endpoint_container_id = architecture_id("extc", mapping["name"], endpoint_name)
    external_endpoint_container_ids_by_key[dep_key] = endpoint_container_id
    containers_by_id.setdefault(
        endpoint_container_id,
        external_endpoint_container_entry(
            endpoint_container_id=endpoint_container_id,
            target_system_id=target_system_id,
            endpoint_name=endpoint_name,
            dep_key=dep_key,
        ),
    )
    return endpoint_container_id


def external_endpoint_container_entry(
    *,
    endpoint_container_id: str,
    target_system_id: str,
    endpoint_name: str,
    dep_key: str,
) -> Dict[str, Any]:
    return {
        "id": endpoint_container_id,
        "system_id": target_system_id,
        "name": endpoint_name,
        "title": dependency_display_name(dep_key) if dep_key else endpoint_name,
        "kind": "external",
        "technology": "External dependency",
        "description": external_description(dep_key, 0),
        "tags": ["External", "External Endpoint"],
    }


__all__ = ["ensure_external_endpoint_container", "external_endpoint_container_entry"]
