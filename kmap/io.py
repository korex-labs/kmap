"""File and serialization helpers for kmap."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import yaml


def safe_json_loads(raw: str, default: Any):
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def load_json_file(path: Path, default: Any):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return default


def load_required_json_file(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Invalid JSON file: {path}: {exc}") from exc


def load_yaml_file(path: Path, default: Any):
    try:
        data = read_yaml_file(path)
        return default if data is None else data
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return default


def load_required_yaml_file(path: Path) -> Dict[str, Any]:
    try:
        data = read_yaml_file(path)
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise SystemExit(f"Invalid YAML file: {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SystemExit(f"Invalid YAML file format: {path}: expected YAML mapping")
    return data


def read_yaml_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_yaml_config_or_error(path: Path) -> Dict[str, Any]:
    try:
        return load_required_yaml_file(path)
    except SystemExit as exc:
        message = str(exc)
        message = message.replace("Invalid YAML file format:", "Invalid config file format:", 1)
        message = message.replace("Invalid YAML file:", "Invalid config file:", 1)
        raise SystemExit(message) from exc


def write_text_atomic(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding=encoding,
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def dump_json(path: Path, obj: Any):
    write_text_atomic(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


__all__ = [
    "dump_json",
    "ensure_dir",
    "load_json_file",
    "load_required_json_file",
    "load_required_yaml_file",
    "load_yaml_config_or_error",
    "load_yaml_file",
    "read_yaml_file",
    "safe_json_loads",
    "write_text_atomic",
]
