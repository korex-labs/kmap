"""Dependency display label helpers."""

from typing import Optional

from ..hostish import parse_hostish
from .display_text import short_label

MIN_PRIVATE_HOST_LABELS = 3


def dependency_display_name(dep_key: str) -> str:
    from .display import display_container_name

    parsed = parse_hostish(dep_key or "")
    host = dep_key or "external"
    port: Optional[int] = None
    if parsed:
        host, port, _ = parsed
    host = host.strip().lower()
    labels = [part for part in host.split(".") if part]

    if ".svc" in host or host.endswith(".svc.cluster.local"):
        return short_label(display_container_name(labels[0] if labels else host), 42)

    if (
        len(labels) >= MIN_PRIVATE_HOST_LABELS
        and "-" in labels[0]
        and any(part in host for part in (".lan", ".consul"))
    ):
        return short_label(display_container_name(labels[0]), 42)

    title = short_label(host, 42)
    if port and "." not in host:
        title = f"{title}:{port}"
    return title


def endpoint_label(dep_key: str) -> str:
    parsed = parse_hostish(dep_key or "")
    if not parsed:
        return dep_key or ""

    host, _, _ = parsed
    host = (host or "").strip().lower()
    internal_suffixes = (".svc", ".svc.cluster.local", ".lan", ".consul", ".local")

    if any(suffix in host for suffix in internal_suffixes):
        return host.split(".", 1)[0]
    return host


__all__ = ["MIN_PRIVATE_HOST_LABELS", "dependency_display_name", "endpoint_label"]
