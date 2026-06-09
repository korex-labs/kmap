"""Config resource validation helpers."""

from typing import Any, Dict, List
from urllib.parse import urlparse

from .metadata import clean_metadata_string


def validate_url_like(value: str) -> bool:
    text = clean_metadata_string(value)
    if not text:
        return False
    if text.startswith(("http://", "https://")):
        parsed = urlparse(text)
        return bool(parsed.scheme and parsed.netloc)
    return True


def validate_namespace_resources(ns_path: str, resources: Any, errors: List[str]) -> None:
    if resources is None:
        return
    if not isinstance(resources, dict):
        errors.append(f"{ns_path}.resources: expected mapping")
        return

    for key, value in resources.items():
        resource_path = path_join(ns_path, "resources", key)
        if not clean_metadata_string(key):
            errors.append(f"{resource_path}: resource key must not be empty")
        if not is_string_like(value):
            errors.append(f"{resource_path}: expected string value")
            continue
        if not validate_url_like(str(value)):
            errors.append(f"{resource_path}: invalid URL")


def validate_product_resources(config: Dict[str, Any], errors: List[str]) -> None:
    validate_namespace_resources("", config.get("resources"), errors)


def path_join(*parts: Any) -> str:
    return ".".join(str(part) for part in parts if str(part))


def is_string_like(value: Any) -> bool:
    return isinstance(value, (str, int, float))


__all__ = [
    "is_string_like",
    "path_join",
    "validate_namespace_resources",
    "validate_product_resources",
    "validate_url_like",
]
