"""Shared state and context types for dependency modeling."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DependencyBuildState:
    external_mappings: List[Dict[str, Any]]
    systems_by_id: Dict[str, Dict[str, Any]]
    containers_by_id: Dict[str, Dict[str, Any]]
    external_system_ids_by_key: Dict[str, str] = field(default_factory=dict)
    external_endpoint_container_ids_by_key: Dict[str, str] = field(default_factory=dict)


@dataclass
class RelationContext:
    source_service: str
    source_id: str
    source_project_id: str | None
    dep_key: str
    source_var: str
    rel_metadata: Dict[str, Any]
    database_metadata: Dict[str, Any]
    dependency_type: str
    match_type: str
    evidence: str
    source_origin: str


@dataclass
class TargetResolution:
    target_id: str
    category: str
    boundary_kind: str
    target_project_id: str | None = None
    mapping: Dict[str, Any] | None = None


@dataclass
class ExternalIdentity:
    mapping: Dict[str, Any] | None
    aggregate_mapping: bool
    external_name: str
    external_key: str


__all__ = ["DependencyBuildState", "ExternalIdentity", "RelationContext", "TargetResolution"]
