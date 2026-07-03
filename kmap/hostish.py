"""Host-like value parsing used by inspection, naming, and renderers."""

import re
from typing import Optional, Tuple

VALID_HOST_RE = re.compile(
    r"^(?:(?P<scheme>[a-z][a-z0-9+\-.]*)://)?"
    r"(?P<host>[A-Za-z0-9][A-Za-z0-9.\-]*|\[[0-9a-fA-F:]+\])"
    r"(?::(?P<port>\d{1,5}))?"
    r"(?P<path>/.*)?$"
)
BRANCHY_VALUE_RE = re.compile(r"(^|[-_.])(test|release|qa|dev)([-_.]|$)", re.IGNORECASE)
DURATION_VALUE_RE = re.compile(r"^\d+(?:ms|s|m|h)$", re.IGNORECASE)
MAX_PORT = 65535
REJECTED_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
REJECTED_SCALAR_VALUES = {"true", "false", "yes", "no", "on", "off", "null", "none"}


def parse_hostish(value: str) -> Optional[Tuple[str, Optional[int], Optional[str]]]:
    value = _clean_hostish_value(value)
    if not value or _is_rejected_scalar_value(value):
        return None

    m = VALID_HOST_RE.match(value)
    if not m:
        return None

    host = _normalized_hostish_host(m.group("host") or "")
    path = m.group("path")
    if _is_rejected_hostish_host(host):
        return None

    port = _hostish_port(m.group("port"))
    if port == 0:
        return None

    return host, port, path


def _clean_hostish_value(value: str) -> str:
    return (value or "").strip().strip('"').strip("'")


def _is_rejected_scalar_value(value: str) -> bool:
    if value.lower() in REJECTED_SCALAR_VALUES:
        return True
    return value.startswith("vault://") or value.isdigit() or bool(DURATION_VALUE_RE.fullmatch(value))


def _normalized_hostish_host(host: str) -> str:
    return (host or "").strip().lower().strip("[]")


def _is_rejected_hostish_host(host: str) -> bool:
    if not host:
        return True
    if host.startswith(".") or host.endswith(".") or ".." in host:
        return True
    if host in REJECTED_HOSTS:
        return True
    if BRANCHY_VALUE_RE.search(host):
        return True
    return _is_numeric_host(host)


def _is_numeric_host(host: str) -> bool:
    if re.fullmatch(r"\d+(?:\.\d+){3}", host):
        return True
    return bool(re.fullmatch(r"\d+(?:\.\d+)+", host))


def _hostish_port(port_raw: Optional[str]) -> Optional[int]:
    if not port_raw:
        return None
    port = int(port_raw)
    if 1 <= port <= MAX_PORT:
        return port
    return 0


__all__ = ["parse_hostish"]
