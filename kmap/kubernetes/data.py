"""Kubernetes ConfigMap and Secret data helpers."""

import base64
from typing import Any, Dict


def decode_secret_data(secret: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for key, value in (secret.get("data") or {}).items():
        try:
            out[key] = base64.b64decode(value).decode("utf-8", errors="replace")
        except Exception:
            continue
    return out


def configmap_data(configmap: Dict[str, Any]) -> Dict[str, str]:
    return {str(key): str(value) for key, value in ((configmap.get("data") or {}).items())}


__all__ = ["configmap_data", "decode_secret_data"]
