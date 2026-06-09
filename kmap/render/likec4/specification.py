"""Generated LikeC4 specification extensions."""

from typing import Any, Dict, Iterable, List

from ...config import clean_metadata_string
from .common import likec4_alias

COMMON_LIKEC4_TAGS = {
    "App",
    "Cloud",
    "Data",
    "External",
    "Gateway",
    "Infra",
    "K8s",
    "Messaging",
    "Monitoring",
    "Support",
    "Topic",
}


def _tag_values(architecture: Dict[str, Any]) -> Iterable[str]:
    product = architecture.get("product") or {}
    yield from product.get("tags") or []
    for project in architecture.get("projects") or []:
        yield from project.get("tags") or []


def generated_likec4_tag_names(architecture: Dict[str, Any]) -> List[str]:
    tags: List[str] = []
    seen = set(COMMON_LIKEC4_TAGS)
    for tag in _tag_values(architecture):
        raw_tag = clean_metadata_string(tag)
        if not raw_tag:
            continue
        tag_name = likec4_alias(raw_tag)
        if not tag_name or tag_name in seen:
            continue
        seen.add(tag_name)
        tags.append(tag_name)
    return tags


def render_likec4_specification(architecture: Dict[str, Any]) -> str:
    lines = [
        "specification {",
        "  // Generated config tags by kmap. Do not edit manually.",
    ]
    lines.extend(f"  tag {tag}" for tag in generated_likec4_tag_names(architecture))
    lines.append("}")
    return "\n".join(lines) + "\n"


__all__ = ["generated_likec4_tag_names", "render_likec4_specification"]
