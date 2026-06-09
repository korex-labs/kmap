"""View command path and argument validation helpers."""

from pathlib import Path

from ...paths import SCHEMAS_ROOT

MAX_TCP_PORT = 65535


def container_name(prefix: str, product: str) -> str:
    return f"{prefix}-{product}"


def likec4_output_path(product: str) -> Path:
    return SCHEMAS_ROOT / "Likec4" / product / "likec4.config.json"


def structurizr_workspace_path(product: str) -> Path:
    return SCHEMAS_ROOT / "Structurizr" / product / "workspace.dsl"


def structurizr_common_workspace_path() -> Path:
    return SCHEMAS_ROOT / "Structurizr" / "common" / "workspace.dsl"


def require_file(path: Path, hint: str) -> None:
    if path.exists():
        return
    raise SystemExit(f"Missing {path}\n{hint}")


def validate_port(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not text.isdigit():
        raise SystemExit(f"{label} must be a TCP port number, got {value!r}")
    port = int(text)
    if port < 1 or port > MAX_TCP_PORT:
        raise SystemExit(f"{label} must be between 1 and {MAX_TCP_PORT}, got {value!r}")
    return text


__all__ = [
    "MAX_TCP_PORT",
    "SCHEMAS_ROOT",
    "container_name",
    "likec4_output_path",
    "require_file",
    "structurizr_common_workspace_path",
    "structurizr_workspace_path",
    "validate_port",
]
