"""Config metadata normalization helpers."""

from typing import Any, Dict, List

from .names import slug_name

PROJECT_METADATA_FIELDS = ("title", "repo", "owner_team", "domain_team", "description", "element_type")


def clean_metadata_string(value: Any) -> str:
    return str(value or "").strip()


def clean_metadata_tags(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [x.strip() for x in value.split(",") if x.strip()]
    return []


def clean_metadata_resources(value: Any) -> Dict[str, str]:
    if not isinstance(value, dict):
        return {}
    out = {}
    for raw_key, raw_value in value.items():
        key = clean_metadata_resource_key(raw_key)
        val = clean_metadata_string(raw_value)
        if key and val:
            out[key] = val
    return out


def clean_metadata_resource_key(value: Any) -> str:
    return slug_name(clean_metadata_string(value)).replace("-", "_")


def normalize_project_metadata_item(raw_project: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(raw_project, dict):
        return {}
    item = project_metadata_scalar_fields(raw_project)
    tags = clean_metadata_tags(raw_project.get("tags"))
    if tags:
        item["tags"] = tags
    resources = clean_metadata_resources(raw_project.get("resources"))
    if resources:
        item["resources"] = resources
        if resources.get("repo") and not item.get("repo"):
            item["repo"] = resources["repo"]
    return item


def project_metadata_scalar_fields(raw_project: Dict[str, Any]) -> Dict[str, str]:
    return {
        field: clean_metadata_string(raw_project.get(field))
        for field in PROJECT_METADATA_FIELDS
        if clean_metadata_string(raw_project.get(field))
    }


def merge_project_metadata(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base or {})
    for key, value in (update or {}).items():
        if key == "tags":
            _merge_metadata_tags(out, value)
        elif key == "resources":
            _merge_metadata_resources(out, value)
        else:
            _merge_metadata_scalar(out, key, value)
    return out


def _merge_metadata_tags(out: Dict[str, Any], value: Any) -> None:
    tags = list(out.get("tags") or [])
    for tag in value or []:
        if tag not in tags:
            tags.append(tag)
    if tags:
        out["tags"] = tags


def _merge_metadata_resources(out: Dict[str, Any], value: Any) -> None:
    resources = dict(out.get("resources") or {})
    resources.update(value or {})
    if not resources:
        return
    out["resources"] = resources
    if resources.get("repo") and not out.get("repo"):
        out["repo"] = resources["repo"]


def _merge_metadata_scalar(out: Dict[str, Any], key: str, value: Any) -> None:
    if value and not out.get(key):
        out[key] = value


__all__ = [
    "PROJECT_METADATA_FIELDS",
    "clean_metadata_resource_key",
    "clean_metadata_resources",
    "clean_metadata_string",
    "clean_metadata_tags",
    "merge_project_metadata",
    "normalize_project_metadata_item",
    "project_metadata_scalar_fields",
]
