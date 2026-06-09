"""Discovery target config normalization."""

from typing import Any, Dict

from .metadata import clean_metadata_string


def _discovery_target(raw_target: Any) -> Dict[str, str]:
    if not isinstance(raw_target, dict):
        return {}
    item = {
        "context": clean_metadata_string(raw_target.get("context")),
        "kubeconfig": clean_metadata_string(raw_target.get("kubeconfig")),
    }
    return {key: value for key, value in item.items() if value}


def normalize_discovery_config(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = config.get("discovery") or {}
    if not isinstance(raw, dict):
        raw = {}

    out = _discovery_target(raw)
    out["namespaces"] = namespace_discovery_targets(config.get("namespaces") or config.get("namespace") or {})
    return out


def namespace_discovery_targets(raw_namespaces: Any) -> Dict[str, Dict[str, str]]:
    namespaces = {}
    if not isinstance(raw_namespaces, dict):
        return namespaces
    for name, value in raw_namespaces.items():
        namespace = clean_metadata_string(name)
        namespace_entry = value if isinstance(value, dict) else {}
        namespace_target = _discovery_target(namespace_entry.get("discovery") or {})
        if namespace and namespace_target:
            namespaces[namespace] = namespace_target
    return namespaces


def resolve_discovery_target(
    discovery_config: Dict[str, Any],
    namespace: str,
    project: str,
    kubeconfig_override: str = "",
) -> Dict[str, str]:
    discovery_config = discovery_config or {}
    resolved = _discovery_target(discovery_config)
    resolved.update(_namespace_discovery_target(discovery_config, namespace))
    override = clean_metadata_string(kubeconfig_override)
    if override:
        resolved["kubeconfig"] = override
    return {key: value for key, value in resolved.items() if value}


def _namespace_discovery_target(discovery_config: Dict[str, Any], namespace: str) -> Dict[str, str]:
    namespace_target = (discovery_config.get("namespaces") or {}).get(namespace) or {}
    return clean_discovery_target_values(namespace_target)


def clean_discovery_target_values(target: Dict[str, Any]) -> Dict[str, str]:
    return {key: clean_metadata_string(value) for key, value in target.items() if value}


__all__ = [
    "clean_discovery_target_values",
    "namespace_discovery_targets",
    "normalize_discovery_config",
    "resolve_discovery_target",
]
