"""Structurizr single-model rendering."""

from typing import Any

from ...identifiers import q
from .elements import internal_system_lines, system_lines
from .references import structurizr_reference_map
from .relations import deduplicated_structurizr_relationships, structurizr_relationship_technology


def structurizr_model_context(architecture: dict[str, Any]) -> dict[str, Any]:
    refs = structurizr_reference_map(architecture)
    systems_by_id = {system.get("id"): system for system in architecture.get("systems") or []}
    projects_by_id = {project.get("id"): project for project in architecture.get("projects") or []}
    containers_by_system: dict[str, list[dict[str, Any]]] = {}
    for container in architecture.get("containers") or []:
        system_id = container.get("system_id") or ""
        containers_by_system.setdefault(system_id, []).append(container)
    inbound_counts: dict[str, int] = {}
    for relationship in architecture.get("relationships") or []:
        target_id = relationship.get("target_id") or ""
        if target_id:
            inbound_counts[target_id] = inbound_counts.get(target_id, 0) + 1
    return {
        "refs": refs,
        "systems_by_id": systems_by_id,
        "projects_by_id": projects_by_id,
        "containers_by_system": containers_by_system,
        "inbound_counts": inbound_counts,
    }


def render_project_model(
    architecture: dict[str, Any],
    project: dict[str, Any],
    context: dict[str, Any],
) -> str:
    lines: list[str] = []
    project_id = project.get("id") or ""
    systems = [system for system in architecture.get("systems") or [] if (system.get("project_id") or "") == project_id]
    for system in sorted(systems, key=lambda item: item.get("id") or ""):
        if lines:
            lines.append("")
        lines.extend(
            internal_system_lines(
                system,
                project,
                context["containers_by_system"].get(system.get("id") or "", []),
                context["refs"],
                architecture,
                context["inbound_counts"],
            )
        )
    return "\n".join(lines) + ("\n" if lines else "")


def render_external_model(
    architecture: dict[str, Any],
    systems: list[dict[str, Any]],
    context: dict[str, Any],
) -> str:
    _ = architecture
    lines: list[str] = []
    for system in systems:
        if lines:
            lines.append("")
        lines.extend(
            system_lines(
                system,
                context["containers_by_system"].get(system.get("id") or "", []),
                context["refs"],
                context["inbound_counts"],
            )
        )
    return "\n".join(lines) + ("\n" if lines else "")


def render_structurizr_model(architecture: dict[str, Any]) -> str:
    context = structurizr_model_context(architecture)
    lines: list[str] = []
    internal_systems = [system for system in architecture.get("systems") or [] if system.get("project_id")]
    external_systems = [system for system in architecture.get("systems") or [] if not system.get("project_id")]

    _append_internal_systems(lines, internal_systems, architecture, context)
    _append_external_systems(lines, external_systems, context)
    lines.extend(_relationship_lines(architecture, context["refs"]))

    return "\n".join(lines) + ("\n" if lines else "")


def _append_internal_systems(
    lines: list[str],
    systems: list[dict[str, Any]],
    architecture: dict[str, Any],
    context: dict[str, Any],
) -> None:
    for system in systems:
        project = context["projects_by_id"].get(system.get("project_id") or "")
        if not project:
            continue
        _append_spaced_lines(
            lines,
            internal_system_lines(
                system,
                project,
                context["containers_by_system"].get(system.get("id") or "", []),
                context["refs"],
                architecture,
                context["inbound_counts"],
            ),
        )


def _append_external_systems(lines: list[str], systems: list[dict[str, Any]], context: dict[str, Any]) -> None:
    for system in systems:
        _append_spaced_lines(
            lines,
            system_lines(
                system,
                context["containers_by_system"].get(system.get("id") or "", []),
                context["refs"],
                context["inbound_counts"],
            ),
        )


def _append_spaced_lines(lines: list[str], new_lines: list[str]) -> None:
    if lines:
        lines.append("")
    lines.extend(new_lines)


def _relationship_lines(architecture: dict[str, Any], refs: dict[str, str]) -> list[str]:
    return [
        _relationship_line(relationship, refs)
        for relationship in deduplicated_structurizr_relationships(architecture.get("relationships") or [], refs)
    ]


def _relationship_line(relationship: dict[str, Any], refs: dict[str, str]) -> str:
    source = refs.get(relationship.get("source_id") or "")
    target = refs.get(relationship.get("target_id") or "")
    technology = structurizr_relationship_technology(relationship)
    return f'{source} -> {target} "uses" "{q(technology)}"'


__all__ = [
    "render_external_model",
    "render_project_model",
    "render_structurizr_model",
    "structurizr_model_context",
]
