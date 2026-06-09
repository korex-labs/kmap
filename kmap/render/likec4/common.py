"""Shared LikeC4 rendering helpers."""

from typing import Any, Dict, List, Tuple

from ...config import clean_metadata_string
from ...identifiers import ident, q
from ...metadata import resource_property_key


def likec4_alias(value: str) -> str:
    return ident(str(value or "").replace(".", "_").replace("-", "_"))


def likec4_quote(value: str) -> str:
    return q(value)


def likec4_reference_map(architecture: Dict[str, Any]) -> Dict[str, str]:
    refs: Dict[str, str] = {}
    for system in architecture.get("systems") or []:
        system_id = system.get("id") or ""
        if system_id:
            refs[system_id] = likec4_alias(system_id)
    for container in architecture.get("containers") or []:
        container_id = container.get("id") or ""
        system_id = container.get("system_id") or ""
        system_ref = refs.get(system_id) or likec4_alias(system_id)
        container_alias = likec4_alias(container_id)
        if container_id and system_ref and container_alias:
            refs[container_id] = f"{system_ref}.{container_alias}"
    return refs


def likec4_metadata_lines(items: List[Tuple[str, str]], indent: str = "    ") -> List[str]:
    cleaned = [
        (resource_property_key(key), clean_metadata_string(value))
        for key, value in items
        if resource_property_key(key) and clean_metadata_string(value)
    ]
    if not cleaned:
        return []
    lines = [f"{indent}metadata {{"]
    for key, value in cleaned:
        lines.append(f'{indent}  {key} "{likec4_quote(value)}"')
    lines.append(f"{indent}}}")
    return lines


__all__ = [
    "likec4_alias",
    "likec4_metadata_lines",
    "likec4_quote",
    "likec4_reference_map",
]
