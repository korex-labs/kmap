"""Observability signal extraction for namespace inspection."""

from typing import Any, Dict, Iterable, List

from ...config import clean_metadata_string
from ...inspection.workloads import extract_literal_env_from_container
from ...kubernetes import annotations_of, obj_name, pod_template_annotations_of

PROMETHEUS_ANNOTATION_KEYS = (
    "prometheus.io/scrape",
    "prometheus.io/path",
    "prometheus.io/port",
    "prometheus.io/scheme",
)

OTEL_ENDPOINT_KEYS = (
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
    "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
)


def _append_unique(items: List[str], value: Any) -> None:
    cleaned = clean_metadata_string(value)
    if cleaned and cleaned not in items:
        items.append(cleaned)


def _prometheus_annotations(annotations: Dict[str, Any], source: str, out: Dict[str, List[str]]) -> None:
    matched = False
    for key in PROMETHEUS_ANNOTATION_KEYS:
        value = clean_metadata_string((annotations or {}).get(key))
        if not value:
            continue
        matched = True
        out_key = key.removeprefix("prometheus.io/").replace("-", "_")
        _append_unique(out[f"prometheus_{out_key}s"], value)
    if matched:
        _append_unique(out["prometheus_sources"], source)


def _otel_env_from_containers(containers: Iterable[Dict[str, Any]]) -> Dict[str, str]:
    return {
        key: value
        for container in containers or []
        for key, value in extract_literal_env_from_container(container).items()
        if key.startswith("OTEL_")
    }


def _apply_otel_env(out: Dict[str, List[str]], env: Dict[str, str]) -> None:
    for key, value in sorted((env or {}).items()):
        if not key.startswith("OTEL_"):
            continue
        _append_unique(out["otel_env_vars"], key)
        if key == "OTEL_SERVICE_NAME":
            _append_unique(out["otel_service_names"], value)
        elif key in OTEL_ENDPOINT_KEYS:
            _append_unique(out["otel_exporter_otlp_endpoints"], value)


def workload_observability_context(
    *,
    workload: Dict[str, Any],
    services: List[Dict[str, Any]],
    matched_service_names: Iterable[str],
    containers: List[Dict[str, Any]],
    runtime_env: Dict[str, str],
    vault_env: Dict[str, str],
) -> Dict[str, Any]:
    out: Dict[str, List[str]] = {
        "prometheus_scrapes": [],
        "prometheus_paths": [],
        "prometheus_ports": [],
        "prometheus_schemes": [],
        "prometheus_sources": [],
        "otel_service_names": [],
        "otel_exporter_otlp_endpoints": [],
        "otel_env_vars": [],
    }

    _prometheus_annotations(annotations_of(workload), "workload", out)
    _prometheus_annotations(pod_template_annotations_of(workload), "pod_template", out)

    for service in matched_services(services, matched_service_names):
        name = obj_name(service)
        _prometheus_annotations(annotations_of(service), f"service:{name}", out)

    out.update(otel_observability_signals(containers, runtime_env, vault_env))

    return {key: sorted(values) for key, values in out.items() if values}


def otel_observability_signals(
    containers: Iterable[Dict[str, Any]],
    runtime_env: Dict[str, str],
    vault_env: Dict[str, str],
) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {
        "otel_service_names": [],
        "otel_exporter_otlp_endpoints": [],
        "otel_env_vars": [],
    }
    _apply_otel_env(out, _otel_env_from_containers(containers))
    _apply_otel_env(out, runtime_env)
    _apply_otel_env(out, vault_env)
    return out


def matched_services(
    services: List[Dict[str, Any]],
    matched_service_names: Iterable[str],
) -> List[Dict[str, Any]]:
    names = set(matched_service_names or [])
    return [service for service in services or [] if obj_name(service) in names]


__all__ = [
    "OTEL_ENDPOINT_KEYS",
    "PROMETHEUS_ANNOTATION_KEYS",
    "matched_services",
    "otel_observability_signals",
    "workload_observability_context",
]
