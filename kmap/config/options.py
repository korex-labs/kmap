"""Config option normalization helpers."""

from typing import Any, Dict, Optional

from .metadata import clean_metadata_string, clean_metadata_tags

NAMESPACE_ALIAS_IGNORED_TOKENS = (
    "prod",
    "production",
    "stage",
    "staging",
    "test",
    "qa",
    "dev",
    "uat",
)
DEFAULT_FALLBACK_SYSTEM_NAME_TOKENS = set(NAMESPACE_ALIAS_IGNORED_TOKENS) | {"main"}


def clean_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def clean_int(value: Any, default: int, minimum: Optional[int] = None) -> int:
    try:
        out = int(value)
    except (TypeError, ValueError):
        out = default
    if minimum is not None and out < minimum:
        return minimum
    return out


def normalize_system_naming_config(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = clean_mapping(config.get("system_naming"))
    fallback = clean_mapping(raw.get("fallback") or raw.get("fallback_names"))
    service_aliases = clean_mapping(raw.get("service_aliases") or raw.get("dependency_aliases"))

    return {
        "fallback": {
            "enabled": clean_bool(fallback.get("enabled"), True),
            "strip_prefix_tokens": fallback_token_list(fallback, "strip_prefix_tokens"),
            "strip_suffix_tokens": fallback_token_list(fallback, "strip_suffix_tokens"),
            "collapse_project_wrapped_names": clean_bool(fallback.get("collapse_project_wrapped_names"), True),
            "rewrites": fallback_rewrite_rules(fallback),
        },
        "service_aliases": {
            "rewrites": alias_rewrite_rules(service_aliases),
        },
    }


def normalize_dependency_hotspots_config(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = clean_mapping(config.get("dependency_hotspots"))

    return {
        "enabled": clean_bool(raw.get("enabled"), True),
        "metric": dependency_hotspot_metric(raw.get("metric")),
        "min_count": clean_int(raw.get("min_count"), 3, minimum=1),
        "max_hotspots": clean_int(raw.get("max_hotspots") or raw.get("max_nodes"), 15, minimum=1),
    }


def clean_mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def fallback_token_list(fallback: Dict[str, Any], key: str) -> list[str]:
    tokens = set(DEFAULT_FALLBACK_SYSTEM_NAME_TOKENS)
    tokens.update(x.lower() for x in clean_metadata_tags(fallback.get(key)))
    return sorted(tokens)


def fallback_rewrite_rules(fallback: Dict[str, Any]) -> list[Dict[str, str]]:
    return rewrite_rules(fallback)


def alias_rewrite_rules(alias_config: Dict[str, Any]) -> list[Dict[str, str]]:
    return rewrite_rules(alias_config)


def rewrite_rules(config: Dict[str, Any]) -> list[Dict[str, str]]:
    rewrites = []
    for item in config.get("rewrites") or config.get("rewrite_rules") or []:
        if not isinstance(item, dict):
            continue
        match_regex = clean_metadata_string(item.get("match_regex") or item.get("regex"))
        replace = clean_metadata_string(item.get("replace") or item.get("replacement"))
        if match_regex and replace:
            rewrites.append(
                {
                    "match_regex": match_regex,
                    "replace": replace,
                }
            )
    return rewrites


def dependency_hotspot_metric(value: Any) -> str:
    metric = clean_metadata_string(value) or "incoming_distinct_source_container_count"
    allowed_metrics = {
        "incoming_relationship_count",
        "incoming_distinct_source_system_count",
        "incoming_distinct_source_container_count",
    }
    return metric if metric in allowed_metrics else "incoming_distinct_source_container_count"


__all__ = [
    "DEFAULT_FALLBACK_SYSTEM_NAME_TOKENS",
    "NAMESPACE_ALIAS_IGNORED_TOKENS",
    "alias_rewrite_rules",
    "clean_bool",
    "clean_int",
    "clean_mapping",
    "dependency_hotspot_metric",
    "fallback_rewrite_rules",
    "fallback_token_list",
    "normalize_dependency_hotspots_config",
    "normalize_system_naming_config",
    "rewrite_rules",
]
