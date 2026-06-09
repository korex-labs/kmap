"""Structurizr view rendering from the normalized architecture model."""

from dataclasses import dataclass
from typing import Any, Dict, List

from ...identifiers import q
from .references import structurizr_reference_map
from .view_helpers import (
    containers_by_system,
    deployment_view_key,
    internal_project_views,
    project_view_connection_ids,
    system_project_ids,
    view_key,
)


@dataclass(frozen=True)
class _ProjectViewRenderContext:
    project_view: Dict[str, Any]
    refs: Dict[str, str]
    containers_by_system: Dict[str, List[Dict[str, Any]]]
    containers_by_id: Dict[str, Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    system_project_ids: Dict[str, str]


def _landscape_lines(systems: List[Dict[str, Any]], refs: Dict[str, str]) -> List[str]:
    lines: List[str] = ["systemLandscape landscape {"]
    seen_refs: set[str] = set()
    for system in systems:
        ref = refs.get(system.get("id") or "")
        if ref and ref not in seen_refs:
            lines.append(_include_ref(ref))
            seen_refs.add(ref)
    lines.append("  autoLayout lr")
    lines.append("}")
    return lines


def _include_ref(ref: str) -> str:
    return f"  include {ref}"


def _extend_known_refs(lines: List[str], element_ids: List[str], refs: Dict[str, str]) -> None:
    lines.extend(_include_ref(refs[element_id]) for element_id in element_ids if refs.get(element_id))


def _project_view_lines(context: _ProjectViewRenderContext) -> List[str]:
    project_view = context.project_view
    system_ids = [system_id for system_id in project_view["system_ids"] if system_id]
    system_ref = context.refs.get(system_ids[0] if system_ids else "") or ""
    if not system_ref:
        return []

    title = project_view.get("title") or system_ref
    system_containers = [
        container for system_id in system_ids for container in context.containers_by_system.get(system_id, [])
    ]
    container_ids = {container.get("id") or "" for container in system_containers}
    connected_system_ids, connected_element_ids = project_view_connection_ids(
        system_ids, container_ids, context.containers_by_id, context.relationships
    )
    connected_system_ids = {
        connected_system_id
        for connected_system_id in connected_system_ids
        if context.system_project_ids.get(connected_system_id) != project_view["id"]
    }

    lines = [
        "",
        f'systemContext {system_ref} {view_key("system_context", system_ref)} "System Context - {q(title)}" {{',
        _include_ref(system_ref),
    ]
    _extend_known_refs(lines, sorted(connected_system_ids), context.refs)
    lines.append("  autoLayout lr")
    lines.append("}")

    lines.append(f'container {system_ref} {view_key("containers", system_ref)} "Containers - {q(title)}" {{')
    _extend_known_refs(lines, [container.get("id") or "" for container in system_containers], context.refs)
    _extend_known_refs(lines, sorted(connected_element_ids), context.refs)
    lines.append("  autoLayout lr")
    lines.append("}")
    return lines


def _deployment_view_lines(product_name: str, deployment: Dict[str, Any]) -> List[str]:
    env = deployment.get("env") or "env"
    return [
        "",
        f'deployment * "{q(env)}" "{q(deployment_view_key(product_name, env))}" '
        f'"Deployments - {q(product_name)} / {q(env)}" {{',
        "  include *",
        "  autoLayout tb",
        "}",
    ]


def render_structurizr_views(architecture: Dict[str, Any]) -> str:
    refs = structurizr_reference_map(architecture)
    product = architecture.get("product") or {}
    product_name = product.get("name") or "product"
    systems = architecture.get("systems") or []
    containers = architecture.get("containers") or []
    relationships = architecture.get("relationships") or []
    containers_by_id = {container.get("id"): container for container in containers}
    grouped_containers = containers_by_system(containers)
    project_ids_by_system = system_project_ids(systems)

    lines = _landscape_lines(systems, refs)
    for project_view in internal_project_views(architecture):
        lines.extend(
            _project_view_lines(
                _ProjectViewRenderContext(
                    project_view=project_view,
                    refs=refs,
                    containers_by_system=grouped_containers,
                    containers_by_id=containers_by_id,
                    relationships=relationships,
                    system_project_ids=project_ids_by_system,
                )
            )
        )

    for deployment in architecture.get("deployments") or []:
        lines.extend(_deployment_view_lines(product_name, deployment))

    return "\n".join(lines) + "\n"


__all__ = ["render_structurizr_views"]
