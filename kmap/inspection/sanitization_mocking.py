"""Mocking helpers for persisted inspection reports."""

from typing import Any, Dict, Iterable, List

from .dependency_sanitization import mock_dns_label, mock_host, mock_hostish_value, mock_identity_label, mock_label


def mock_selector(selector: Dict[str, str], seed: str = "") -> Dict[str, str]:
    return {
        mock_dns_label("label", str(key), seed): mock_dns_label("value", str(value), seed)
        for key, value in (selector or {}).items()
    }


def mock_entrypoint(ep: Dict[str, Any], seed: str = "") -> Dict[str, Any]:
    out = dict(ep)
    ep_type = str(out.get("type") or "entrypoint").lower()
    if out.get("name"):
        out["name"] = mock_label(ep_type, str(out["name"]), seed)
    host = str(out.get("host") or "")
    mocked_host = mock_host(host, seed) if host else ""
    if mocked_host:
        out["host"] = mocked_host
    port = out.get("port")
    if port and mocked_host:
        out["endpoint"] = f"{mocked_host}:{port}"
    elif mocked_host:
        out["endpoint"] = mocked_host
    elif out.get("endpoint"):
        out["endpoint"] = mock_hostish_value(str(out["endpoint"]), seed)
    return out


def mock_traffic_route(route: Dict[str, Any], seed: str = "") -> Dict[str, Any]:
    out = dict(route)
    source = dict(out.get("source") or {})
    if source.get("name"):
        source["name"] = (
            mock_host(str(source["name"]), seed)
            if "." in str(source["name"])
            else mock_label("source", str(source["name"]), seed)
        )
    out["source"] = source
    out["hops"] = [mock_traffic_hop(hop, seed) for hop in out.get("hops") or []]
    target = dict(out.get("target") or {})
    if target.get("names"):
        target["names"] = [mock_label("container", str(name), seed) for name in target.get("names") or []]
    out["target"] = target
    return out


def mock_traffic_hop(hop: Dict[str, Any], seed: str = "") -> Dict[str, Any]:
    item = dict(hop)
    if item.get("name"):
        item["name"] = mock_label(str(item.get("type") or "hop").lower(), str(item["name"]), seed)
    if item.get("host"):
        item["host"] = mock_host(str(item["host"]), seed)
    return item


def sanitize_name_list(items: Iterable[str], kind: str, data_mode: str, mock_seed: str = "") -> List[str]:
    values = [str(item) for item in (items or []) if str(item)]
    if data_mode == "raw":
        return values
    if data_mode == "mocked":
        return [mock_label(kind, value, mock_seed) for value in values]
    return [f"redacted-{kind}-{index}" for index, _ in enumerate(values, start=1)]


def mocked_report_identity_fields(report: Dict[str, Any], mock_seed: str = "") -> Dict[str, Any]:
    return {
        "cluster": mock_label("cluster", str(report.get("cluster") or ""), mock_seed),
        "namespace": mock_identity_label(str(report.get("namespace") or ""), mock_seed),
        "discovery": {
            key: mock_label(key, str(value), mock_seed)
            for key, value in (report.get("discovery") or {}).items()
            if str(value)
        },
        "helm_releases": sanitize_name_list(report.get("helm_releases", []), "release", "mocked", mock_seed),
    }


def mocked_workload_identity_fields(wk: Dict[str, Any], mock_seed: str = "") -> Dict[str, Any]:
    fields = {
        "service_id": mock_label("service-id", str(wk.get("service_id") or ""), mock_seed),
        "cluster": mock_label("cluster", str(wk.get("cluster") or ""), mock_seed),
        "namespace": mock_identity_label(str(wk.get("namespace") or ""), mock_seed),
        "project": mock_label("project", str(wk.get("project") or ""), mock_seed),
        "containers": [
            mock_container(container, mock_seed) for container in wk.get("containers") or [] if container.get("name")
        ],
        "service_name": mock_identity_label(
            f"{wk.get('namespace') or ''}:{wk.get('kind') or ''}:{wk.get('service_name') or ''}",
            mock_seed,
        ),
        "release": mock_label("release", str(wk.get("release") or ""), mock_seed) if wk.get("release") else "",
        "selector": mock_selector(wk.get("selector") or {}, mock_seed),
    }
    if wk.get("app_service"):
        fields["app_service"] = mock_label("app-service", str(wk.get("app_service") or ""), mock_seed)
    return fields


def mock_container(container: Dict[str, Any], mock_seed: str) -> Dict[str, Any]:
    return {
        **container,
        "name": mock_label("container", str(container.get("name") or ""), mock_seed),
        "image": mock_label("image", str(container.get("image") or ""), mock_seed) if container.get("image") else "",
    }


def mocked_workload_runtime_reference_fields(wk: Dict[str, Any], mock_seed: str = "") -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    for field, kind in (
        ("replicasets", "replicaset"),
        ("statefulsets", "statefulset"),
        ("daemonsets", "daemonset"),
        ("services", "service"),
        ("ingresses", "ingress"),
        ("referenced_configmaps", "configmap"),
    ):
        fields[field] = sanitize_name_list(wk.get(field, []), kind, "mocked", mock_seed)
    fields["entrypoints"] = [mock_entrypoint(ep, mock_seed) for ep in (wk.get("entrypoints") or [])]
    fields["traffic_routes"] = [mock_traffic_route(route, mock_seed) for route in wk.get("traffic_routes") or []]
    return fields


__all__ = [
    "mock_container",
    "mock_entrypoint",
    "mock_selector",
    "mock_traffic_route",
    "mocked_report_identity_fields",
    "mocked_workload_identity_fields",
    "mocked_workload_runtime_reference_fields",
    "sanitize_name_list",
]
