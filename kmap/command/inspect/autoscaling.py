"""Kubernetes autoscaling metadata extraction."""

from typing import Any, Dict, Tuple

from ...config import clean_metadata_string

WorkloadKey = Tuple[str, str]


def _target_key(ref: Dict[str, Any]) -> WorkloadKey:
    kind = clean_metadata_string(ref.get("kind")) or "Deployment"
    name = clean_metadata_string(ref.get("name"))
    return kind, name


def _metric_target_formula(metric_name: str, target: Dict[str, Any]) -> str:
    for key in ("averageUtilization", "averageValue", "value"):
        value = target.get(key)
        if value is not None:
            return f"{metric_name} {key} {value}"
    return metric_name


def _hpa_metric_formula(metric: Dict[str, Any]) -> str:
    metric_type = clean_metadata_string(metric.get("type"))
    if metric_type == "Resource":
        return _hpa_resource_metric_formula(metric.get("resource") or {})
    if metric_type == "Pods":
        return _hpa_named_metric_formula(metric.get("pods") or {}, "pods")
    if metric_type == "Object":
        return _hpa_named_metric_formula(metric.get("object") or {}, "object")
    if metric_type == "External":
        return _hpa_named_metric_formula(metric.get("external") or {}, "external")
    if metric_type == "ContainerResource":
        return _hpa_container_resource_metric_formula(metric.get("containerResource") or {})
    return metric_type


def _hpa_resource_metric_formula(resource: Dict[str, Any]) -> str:
    metric_name = clean_metadata_string(resource.get("name")) or "resource"
    return _metric_target_formula(metric_name, resource.get("target") or {})


def _hpa_named_metric_formula(metric_config: Dict[str, Any], fallback_name: str) -> str:
    metric_name = clean_metadata_string((metric_config.get("metric") or {}).get("name")) or fallback_name
    return _metric_target_formula(metric_name, metric_config.get("target") or {})


def _hpa_container_resource_metric_formula(resource: Dict[str, Any]) -> str:
    name = clean_metadata_string(resource.get("name")) or "container_resource"
    container = clean_metadata_string(resource.get("container"))
    metric_name = f"{container}.{name}" if container else name
    return _metric_target_formula(metric_name, resource.get("target") or {})


def _hpa_formula(spec: Dict[str, Any]) -> str:
    formulas = [_hpa_metric_formula(metric) for metric in spec.get("metrics") or []]
    formulas = [formula for formula in formulas if formula]
    return "; ".join(formulas)


def autoscaling_metadata_from_hpa(hpa: Dict[str, Any]) -> Dict[str, str]:
    spec = hpa.get("spec") or {}
    metadata: Dict[str, str] = {
        "scaling_enabled": "true",
        "scaling_type": "hpa",
    }
    for source_key, target_key in (
        ("minReplicas", "min_replicas"),
        ("maxReplicas", "max_replicas"),
    ):
        value = spec.get(source_key)
        if value is not None:
            metadata[target_key] = clean_metadata_string(value)
    formula = _hpa_formula(spec)
    if formula:
        metadata["scale_formula"] = formula
    return metadata


def _keda_trigger_formula(trigger: Dict[str, Any]) -> str:
    trigger_type = clean_metadata_string(trigger.get("type")) or "trigger"
    metadata = trigger.get("metadata") or {}
    metric_name = clean_metadata_string(metadata.get("metricName") or metadata.get("metricNameFromEnv"))
    threshold = clean_metadata_string(
        metadata.get("threshold")
        or metadata.get("targetValue")
        or metadata.get("activationThreshold")
        or metadata.get("value")
    )
    if metric_name and threshold:
        return f"{metric_name} >= {threshold}"
    if threshold:
        return f"{trigger_type} >= {threshold}"
    if metric_name:
        return f"{trigger_type}:{metric_name}"
    return trigger_type


def autoscaling_metadata_from_keda_scaled_object(scaled_object: Dict[str, Any]) -> Dict[str, str]:
    spec = scaled_object.get("spec") or {}
    metadata: Dict[str, str] = {
        "scaling_enabled": "true",
        "scaling_type": "keda",
    }
    for source_key, target_key in (
        ("minReplicaCount", "min_replicas"),
        ("maxReplicaCount", "max_replicas"),
    ):
        value = spec.get(source_key)
        if value is not None:
            metadata[target_key] = clean_metadata_string(value)

    scaling_modifiers = (spec.get("advanced") or {}).get("scalingModifiers") or {}
    formula = clean_metadata_string(scaling_modifiers.get("formula"))
    if not formula:
        formulas = [_keda_trigger_formula(trigger) for trigger in spec.get("triggers") or []]
        formula = "; ".join(formula for formula in formulas if formula)
    if formula:
        metadata["scale_formula"] = formula
    return metadata


def autoscaling_by_workload(
    hpa_data: Dict[str, Any],
    keda_scaled_objects_data: Dict[str, Any],
) -> Dict[WorkloadKey, Dict[str, str]]:
    out: Dict[WorkloadKey, Dict[str, str]] = {}
    for hpa in hpa_data.get("items") or []:
        target = _target_key((hpa.get("spec") or {}).get("scaleTargetRef") or {})
        if not target[1]:
            continue
        out[target] = autoscaling_metadata_from_hpa(hpa)

    for scaled_object in keda_scaled_objects_data.get("items") or []:
        target = _target_key((scaled_object.get("spec") or {}).get("scaleTargetRef") or {})
        if not target[1]:
            continue
        keda_metadata = autoscaling_metadata_from_keda_scaled_object(scaled_object)
        existing = out.get(target)
        out[target] = merge_autoscaling_metadata(existing, keda_metadata) if existing else keda_metadata
    return out


def merge_autoscaling_metadata(
    existing: Dict[str, str],
    incoming: Dict[str, str],
) -> Dict[str, str]:
    merged = dict(existing)
    merged["scaling_type"] = ",".join(
        value for value in ("hpa", "keda") if value in {existing.get("scaling_type"), incoming.get("scaling_type")}
    )
    for key, value in incoming.items():
        if key == "scaling_type":
            continue
        if key == "scale_formula" and merged.get(key):
            merged[key] = f"{merged[key]}; {value}"
        else:
            merged[key] = value
    return merged


def autoscaling_text(metadata: Dict[str, Any]) -> str:
    if not metadata:
        return ""
    keys = ("scaling_enabled", "scaling_type", "min_replicas", "max_replicas", "scale_formula")
    return ", ".join(f"{key}={metadata[key]}" for key in keys if clean_metadata_string(metadata.get(key)))


__all__ = [
    "autoscaling_by_workload",
    "autoscaling_metadata_from_hpa",
    "autoscaling_metadata_from_keda_scaled_object",
    "autoscaling_text",
    "merge_autoscaling_metadata",
]
