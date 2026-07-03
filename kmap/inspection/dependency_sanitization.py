"""Dependency candidate sanitization and deterministic mock helpers."""

import hashlib
import re
from typing import Any, Dict

from ..hostish import parse_hostish

SENSITIVE_VAR_RE = re.compile(
    r"(PASSWORD|PASSWD|PASS\b|TOKEN\b|SECRET\b|PRIVATE_KEY\b|ACCESS_KEY\b|API_KEY|JWT|COOKIE|SESSION|AUTH|CREDENTIAL|CERT|KEY\b)",
    re.IGNORECASE,
)
KUBERNETES_SERVICE_HOST_LABELS = 2


def mock_label(kind: str, raw_value: str, seed: str = "") -> str:
    material = f"{seed}:{kind}:{raw_value or ''}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:8]
    return f"mock-{kind}-{digest}"


def mock_dns_label(kind: str, raw_value: str, seed: str = "") -> str:
    material = f"{seed}:{kind}:{raw_value or ''}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:8]
    return f"{kind}-{digest}"[:63]


def mock_identity_label(raw_value: str, seed: str = "") -> str:
    material = f"{seed}:identity:{raw_value or ''}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:8]
    return f"id-{digest}"


def mock_host(value: str, seed: str = "") -> str:
    host = (value or "").strip().lower()
    if not host:
        return host
    if host.endswith(".svc.cluster.local") or host.endswith(".svc"):
        labels = host.split(".")
        if len(labels) >= KUBERNETES_SERVICE_HOST_LABELS:
            labels[0] = mock_identity_label(labels[0], seed)
            labels[1] = mock_identity_label(labels[1], seed)
            return ".".join(labels)
    if "." not in host:
        return mock_identity_label(host, seed)
    return f"{mock_identity_label(host, seed)}.example.test"


def mock_hostish_value(value: str, seed: str = "") -> str:
    parsed = parse_hostish(value or "")
    if not parsed:
        return mock_label("value", value or "", seed)
    host, port, _ = parsed
    mocked_host = mock_host(host, seed)
    return f"{mocked_host}:{port}" if port else mocked_host


def mock_database_metadata(metadata: Dict[str, Any], seed: str = "") -> Dict[str, Any]:
    out = dict(metadata or {})
    if out.get("names"):
        out["names"] = [mock_label("database", str(name), seed) for name in out.get("names") or [] if str(name)]
    if out.get("source_vars"):
        out["source_vars"] = [mock_label("var", str(var), seed) for var in out.get("source_vars") or [] if str(var)]
    return out


def sanitize_dependency_candidate(dep: Dict[str, Any], data_mode: str, mock_seed: str = "") -> Dict[str, Any]:
    out = dict(dep)
    if data_mode == "raw":
        return out

    out["value"] = "<redacted>"
    out["value_redacted"] = True
    sanitize_dependency_source_name(out, data_mode, mock_seed)

    if SENSITIVE_VAR_RE.search(str(out.get("var") or "")):
        out["var_redacted"] = True
    if data_mode == "mocked":
        mock_dependency_candidate_fields(out, mock_seed)
    return out


def sanitize_dependency_source_name(out: Dict[str, Any], data_mode: str, mock_seed: str = "") -> None:
    source = str(out.get("source") or "")
    source_name = str(out.get("source_name") or "")
    if source == "Secret":
        out["source_name"] = mock_label("secret", source_name, mock_seed) if data_mode == "mocked" else "referenced"
    elif source == "ConfigMap" and data_mode == "mocked":
        out["source_name"] = mock_label("configmap", source_name, mock_seed)


def mock_dependency_candidate_fields(out: Dict[str, Any], mock_seed: str = "") -> None:
    if out.get("var"):
        out["var"] = mock_label("var", str(out["var"]), mock_seed)
    if out.get("key"):
        out["key"] = mock_hostish_value(str(out["key"]), mock_seed)
    if out.get("host"):
        out["host"] = mock_host(str(out["host"]), mock_seed)
    if out.get("path"):
        out["path"] = f"/{mock_label('path', str(out['path']), mock_seed)}"
    if out.get("internal_candidates"):
        out["internal_candidates"] = [
            mock_label("workload", str(item), mock_seed) for item in (out.get("internal_candidates") or [])
        ]
    metadata = out.get("metadata") or {}
    database = metadata.get("database") or {}
    if database:
        metadata = dict(metadata)
        metadata["database"] = mock_database_metadata(database, mock_seed)
        out["metadata"] = metadata


__all__ = [
    "SENSITIVE_VAR_RE",
    "mock_database_metadata",
    "mock_dependency_candidate_fields",
    "mock_dns_label",
    "mock_host",
    "mock_hostish_value",
    "mock_identity_label",
    "mock_label",
    "sanitize_dependency_candidate",
    "sanitize_dependency_source_name",
]
