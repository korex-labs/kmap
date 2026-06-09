"""Display labels, descriptions, and visual naming helpers."""

import re
from typing import Any, Dict, List, Optional

from ..config import clean_metadata_string, slug_name
from ..identifiers import architecture_id_part, ident
from .display_dependencies import dependency_display_name, endpoint_label
from .display_text import clip_text, humanize_slug, is_url, short_label, slug_parts

DISPLAY_PREFIX_TOKENS = {"prod", "production", "stage", "staging", "dev", "test", "qa", "uat", "main"}
HEAT_LEVEL_1_MAX = 2
HEAT_LEVEL_2_MAX = 4
INFRA_ELEMENT_TYPES = {
    "AWS_S3_Bucket",
    "ClickHouse_DB",
    "Kafka",
    "Mongo_DB",
    "MySQL_DB",
    "NATS",
    "PgSQL_DB",
    "Redis_DB",
    "ServersCom_Object_Storage",
    "Vault",
    "bucket",
}


def display_system_name(project_name: str, product_name: str) -> str:
    if slug_name(project_name).lower() == slug_name(product_name).lower():
        return product_name or project_name
    if product_name:
        return f"{product_name} / {humanize_slug(project_name)}"
    return humanize_slug(project_name)


def display_container_name(service_name: str) -> str:
    raw = (service_name or "").strip()
    if not raw:
        return "Workload"
    normalized = re.sub(r"^(prod|production|stage|staging|dev|test|qa|main)-", "", raw, flags=re.I)
    return humanize_slug(normalized)


def display_title_from_discovered_name(raw: str, product_name: str = "", project_name: str = "") -> str:
    return display_title_from_discovered_name_with_context(raw, product_name, project_name)


def display_title_from_discovered_name_with_context(
    raw: str,
    product_name: str = "",
    project_name: str = "",
    product_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    parts = [p for p in re.split(r"[-_.\s]+", raw or "") if p]
    if not parts:
        return raw or ""

    remove_edge_tokens = set(DISPLAY_PREFIX_TOKENS)
    remove_anywhere_tokens = set()
    for value in (
        product_name,
        (product_metadata or {}).get("title"),
        (product_metadata or {}).get("domain"),
    ):
        remove_anywhere_tokens.update(slug_parts(clean_metadata_string(value)))

    cleaned: List[str] = []
    for part in parts:
        part_key = architecture_id_part(part)
        if not cleaned and part_key in remove_edge_tokens:
            continue
        if part_key in remove_anywhere_tokens:
            continue
        cleaned.append(part)

    while cleaned and architecture_id_part(cleaned[-1]) in remove_edge_tokens:
        cleaned = cleaned[:-1]

    if not cleaned:
        cleaned = parts
    return humanize_slug("-".join(cleaned))


def should_collapse_container_title_to_app(system_element_type: str, system_category: str) -> bool:
    if system_element_type in INFRA_ELEMENT_TYPES:
        return False
    return system_category in {"App", "Gateway", "Support"}


def container_display_qualifier(service_name: str) -> str:
    raw = (service_name or "").strip()
    if not raw:
        return ""

    parts = [p for p in re.split(r"[-_.]+", raw) if p]
    env_tokens = {"prod", "production", "stage", "staging", "dev", "test", "qa", "uat", "main"}
    qualifiers: List[str] = []

    for part in parts:
        lower = part.lower()
        if lower in env_tokens:
            qualifiers.append(lower)
        elif part.isdigit():
            qualifiers.append(part)
        elif re.fullmatch(r"[a-z]{2,6}\d{2,6}", lower):
            qualifiers.append(lower)

    if qualifiers:
        return " ".join(qualifiers[:3])

    return slug_name(raw)[-12:]


def container_description(svc: Dict[str, Any], inbound_count: int = 0) -> str:
    parts = []
    namespace = (svc.get("namespace") or "").strip()
    workload = (svc.get("service_name") or "").strip()

    if namespace:
        parts.append(f"Namespace: {namespace}")
    if workload:
        parts.append(f"Workload: {workload}")
    if inbound_count:
        parts.append(f"Used by: {inbound_count}")
    return clip_text("\\n".join(parts) or "Kubernetes workload", 100)


def external_description(dep_key: str = "", inbound_count: int = 0) -> str:
    parts = ["External dependency"]
    if dep_key:
        parts.append(f"Endpoint: {endpoint_label(dep_key)}")
    if inbound_count:
        parts.append(f"Used by: {inbound_count}")
    return clip_text("\\n".join(parts), 100)


def view_key_suffix(project_name: str) -> str:
    return ident(project_name or "system")


def dependency_heat_tag(inbound_count: int) -> Optional[str]:
    if inbound_count <= 0:
        return None
    if inbound_count <= HEAT_LEVEL_1_MAX:
        return "Dependency Heat 1"
    if inbound_count <= HEAT_LEVEL_2_MAX:
        return "Dependency Heat 2"
    return "Dependency Heat 3"


__all__ = [
    "clip_text",
    "container_description",
    "container_display_qualifier",
    "dependency_display_name",
    "dependency_heat_tag",
    "display_container_name",
    "display_system_name",
    "display_title_from_discovered_name",
    "display_title_from_discovered_name_with_context",
    "endpoint_label",
    "external_description",
    "humanize_slug",
    "is_url",
    "short_label",
    "should_collapse_container_title_to_app",
    "slug_parts",
    "view_key_suffix",
]
