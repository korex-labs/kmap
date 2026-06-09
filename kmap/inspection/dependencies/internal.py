"""Internal service matching for dependency candidates."""

from typing import Any, Dict, List


def dependency_alias_key(candidate: Dict[str, Any]) -> str:
    return str(candidate.get("host") or candidate.get("key") or "").lower()


def mark_internal_dependency_candidates(
    candidates: List[Dict[str, Any]],
    internal_alias_to_service: Dict[str, List[str]],
) -> List[Dict[str, Any]]:
    for dep in candidates:
        key = dependency_alias_key(dep)
        if key in internal_alias_to_service:
            dep["class"] = "internal_namespace_candidate"
            dep["internal_candidates"] = sorted(set(internal_alias_to_service[key]))
    return candidates


__all__ = ["dependency_alias_key", "mark_internal_dependency_candidates"]
