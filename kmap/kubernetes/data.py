"""Kubernetes ConfigMap and Secret data helpers."""

import base64
import binascii
from typing import Any, Dict


def decode_secret_data(secret: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    data = secret.get("data") or {}
    if not isinstance(data, dict):
        return out
    for key, value in data.items():
        try:
            out[key] = base64.b64decode(value, validate=True).decode("utf-8", errors="replace")
        except (binascii.Error, TypeError, ValueError):
            continue
    return out


def configmap_data(configmap: Dict[str, Any]) -> Dict[str, str]:
    data = configmap.get("data") or {}
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items()}


__all__ = ["configmap_data", "decode_secret_data"]
