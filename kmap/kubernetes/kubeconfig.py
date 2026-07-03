"""Kubeconfig path discovery helpers."""

import os
from pathlib import Path


def default_kubeconfig_path() -> str:
    env_value = os.environ.get("KUBECONFIG", "").strip()
    if env_value:
        return str(Path(env_value).expanduser())

    default_path = Path.home() / ".kube" / "config"
    if default_path.exists():
        return str(default_path)
    return ""


__all__ = ["default_kubeconfig_path"]
