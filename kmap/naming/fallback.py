"""Fallback system-name normalization helpers."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from ..config import clean_bool
from .aliases import NAMESPACE_ALIAS_IGNORED_TOKENS
from .display import slug_parts

DEFAULT_FALLBACK_SYSTEM_NAME_TOKENS = set(NAMESPACE_ALIAS_IGNORED_TOKENS) | {"main"}


@dataclass(frozen=True)
class _FallbackTokenConfig:
    prefix_tokens: set
    suffix_tokens: set
    product_parts: List[str]
    project_parts: List[str]


def apply_fallback_system_rewrites(name: str, rewrites: List[Dict[str, str]]) -> Tuple[str, List[str]]:
    out = name
    applied = []
    for index, rewrite in enumerate(rewrites or []):
        pattern = rewrite.get("match_regex") or ""
        replacement = rewrite.get("replace") or ""
        try:
            new_value = re.sub(pattern, replacement, out)
        except re.error:
            continue
        if new_value != out:
            out = new_value
            applied.append(f"rewrite[{index}]")
    return out, applied


def canonical_fallback_system_name(
    raw: str,
    product_name: str,
    project_name: str,
    naming_config: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:
    fallback_config = (naming_config or {}).get("fallback") or {}
    source = {
        "raw_fallback_name": raw,
        "normalization_rules": [],
    }
    if not clean_bool(fallback_config.get("enabled"), True):
        return raw, source

    rewritten, rewrite_rules = apply_fallback_system_rewrites(raw, fallback_config.get("rewrites") or [])
    if rewrite_rules:
        source["normalization_rules"].extend(rewrite_rules)

    parts = slug_parts(rewritten)
    if not parts:
        return raw, source

    token_config = _fallback_token_config(fallback_config, product_name, project_name)
    parts = _strip_prefixed_tokens(parts, token_config.prefix_tokens, source)
    parts = _strip_suffixed_tokens(parts, token_config.suffix_tokens, source)
    parts = _strip_product_prefix(parts, token_config.product_parts, source)
    parts = _collapse_project_wrapped_name(parts, token_config, fallback_config, source)

    normalized = "-".join(parts) if parts else raw
    return normalized, source


def _fallback_token_config(
    fallback_config: Dict[str, Any],
    product_name: str,
    project_name: str,
) -> _FallbackTokenConfig:
    return _FallbackTokenConfig(
        prefix_tokens=set(fallback_config.get("strip_prefix_tokens") or DEFAULT_FALLBACK_SYSTEM_NAME_TOKENS),
        suffix_tokens=set(fallback_config.get("strip_suffix_tokens") or DEFAULT_FALLBACK_SYSTEM_NAME_TOKENS),
        product_parts=slug_parts(product_name),
        project_parts=slug_parts(project_name),
    )


def _strip_prefixed_tokens(parts: List[str], prefix_tokens: set, source: Dict[str, Any]) -> List[str]:
    while parts and parts[0] in prefix_tokens:
        parts = parts[1:]
        source["normalization_rules"].append("strip_env_prefix")
    return parts


def _strip_suffixed_tokens(parts: List[str], suffix_tokens: set, source: Dict[str, Any]) -> List[str]:
    while parts and parts[-1] in suffix_tokens:
        parts = parts[:-1]
        source["normalization_rules"].append("strip_env_suffix")
    return parts


def _strip_product_prefix(parts: List[str], product_parts: List[str], source: Dict[str, Any]) -> List[str]:
    if product_parts and parts[: len(product_parts)] == product_parts:
        source["normalization_rules"].append("strip_product_prefix")
        return parts[len(product_parts) :]
    return parts


def _collapse_project_wrapped_name(
    parts: List[str],
    token_config: _FallbackTokenConfig,
    fallback_config: Dict[str, Any],
    source: Dict[str, Any],
) -> List[str]:
    if not (token_config.project_parts and clean_bool(fallback_config.get("collapse_project_wrapped_names"), True)):
        return parts
    collapsed_parts, collapse_rule = collapse_project_wrapped_fallback_name(
        parts,
        token_config.project_parts,
        token_config.prefix_tokens,
        token_config.suffix_tokens,
    )
    if collapse_rule:
        source["normalization_rules"].append(collapse_rule)
    return collapsed_parts


def collapse_project_wrapped_fallback_name(
    parts: List[str],
    project_parts: List[str],
    prefix_tokens: set,
    suffix_tokens: set,
) -> Tuple[List[str], str]:
    if parts == project_parts + project_parts:
        return project_parts, "collapse_repeated_project"
    if parts[: len(project_parts)] == project_parts and parts[-len(project_parts) :] == project_parts:
        middle = parts[len(project_parts) : -len(project_parts)]
        if any(part in prefix_tokens or part in suffix_tokens or part.isdigit() for part in middle):
            return project_parts, "collapse_project_wrapped_name"
    return parts, ""


__all__ = [
    "DEFAULT_FALLBACK_SYSTEM_NAME_TOKENS",
    "apply_fallback_system_rewrites",
    "canonical_fallback_system_name",
    "collapse_project_wrapped_fallback_name",
]
