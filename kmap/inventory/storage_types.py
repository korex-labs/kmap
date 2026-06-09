"""Storage backend classification for bucket inventory."""

import re
from typing import Any

BUILTIN_STORAGE_TYPE_RULES = [
    ("Servers.com", ("servers.com",)),
    ("OpenStack", ("openstack", "swift", "os_auth_url")),
    ("Ceph", ("ceph",)),
    ("MinIO", ("minio",)),
]


def storage_type_rules_from_config(tool_config: dict[str, Any] | None) -> list[dict[str, str]]:
    rules = ((tool_config or {}).get("inventory") or {}).get("storage_type_labels") or []
    return [storage_type_rule(rule) for rule in rules if isinstance(rule, dict)]


def storage_type_rule(rule: dict[str, Any]) -> dict[str, str]:
    return {"match": str(rule.get("match") or ""), "label": str(rule.get("label") or "")}


def storage_type_label(
    *,
    endpoint: str,
    bucket: str,
    source_var: str,
    storage_type_rules: list[dict[str, str]] | None = None,
) -> str:
    haystack = " ".join((endpoint, bucket, source_var))
    configured = configured_storage_type_label(haystack, storage_type_rules or [])
    if configured:
        return configured

    return builtin_storage_type_label(endpoint=endpoint, haystack=haystack)


def builtin_storage_type_label(*, endpoint: str, haystack: str) -> str:
    lowered = haystack.lower()
    s3_region = amazon_s3_region(endpoint)
    if s3_region:
        return f"S3 ({s3_region})"

    return _first_builtin_storage_type(lowered)


def _first_builtin_storage_type(lowered: str) -> str:
    for label, markers in BUILTIN_STORAGE_TYPE_RULES:
        if any(marker in lowered for marker in markers):
            return label
    return "S3" if _matches_generic_s3(lowered) else ""


def _matches_generic_s3(lowered: str) -> bool:
    return "amazonaws" in lowered or ".s3." in lowered or lowered.startswith("s3.")


def configured_storage_type_label(haystack: str, storage_type_rules: list[dict[str, str]]) -> str:
    for rule in storage_type_rules:
        pattern = str(rule.get("match") or "")
        label = str(rule.get("label") or "")
        if not pattern or not label:
            continue
        match = re.search(pattern, haystack, flags=re.I)
        if match:
            return format_storage_type_label(label, match)
    return ""


def format_storage_type_label(label: str, match: re.Match) -> str:
    values = {key: value for key, value in match.groupdict().items() if value is not None}
    try:
        return label.format(**values)
    except (IndexError, KeyError, ValueError):
        return label


def amazon_s3_region(endpoint: str) -> str:
    match = re.search(r"(?:^|[.])s3[.-](?P<region>[a-z0-9-]+)[.]amazonaws[.]com$", endpoint or "", flags=re.I)
    return match.group("region") if match else ""


__all__ = [
    "amazon_s3_region",
    "storage_type_label",
    "storage_type_rules_from_config",
]
