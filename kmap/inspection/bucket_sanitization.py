"""Bucket candidate sanitization helpers."""

from typing import Any, Dict

from .dependency_sanitization import mock_hostish_value, mock_label


def sanitize_bucket_candidate(candidate: Dict[str, Any], data_mode: str, mock_seed: str = "") -> Dict[str, Any]:
    out = dict(candidate)
    if data_mode == "raw":
        return out
    if out.get("source") == "Secret":
        out["source_name"] = "referenced"
    if data_mode == "mocked":
        if out.get("source_name") and out.get("source") == "ConfigMap":
            out["source_name"] = mock_label("configmap", str(out["source_name"]), mock_seed)
        if out.get("var"):
            out["var"] = mock_label("var", str(out["var"]), mock_seed)
        if out.get("bucket"):
            out["bucket"] = mock_label("bucket", str(out["bucket"]), mock_seed)
        if out.get("endpoint"):
            out["endpoint"] = mock_hostish_value(str(out["endpoint"]), mock_seed)
    return out


__all__ = ["sanitize_bucket_candidate"]
