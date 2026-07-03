"""Local .env loading for kmap command defaults."""

import os
from pathlib import Path

from .paths import KMAP_DIR, SCHEMAS_ROOT

DEFAULT_ENV_FILES = (SCHEMAS_ROOT / ".env", KMAP_DIR / ".env")
MIN_QUOTED_VALUE_LENGTH = 2


def load_dotenv_files(paths: tuple[Path, ...] = DEFAULT_ENV_FILES) -> None:
    for path in paths:
        if path.exists() and path.is_file():
            load_dotenv_file(path)


def load_dotenv_file(path: Path) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        key, value = parse_dotenv_line(raw_line)
        if key and value and key not in os.environ:
            os.environ[key] = value


def parse_dotenv_line(raw_line: str) -> tuple[str, str]:
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
        return "", ""
    key, value = line.split("=", 1)
    key = key.strip()
    if not key:
        return "", ""
    return key, clean_dotenv_value(value)


def clean_dotenv_value(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= MIN_QUOTED_VALUE_LENGTH and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1]
    return stripped


__all__ = ["load_dotenv_file", "load_dotenv_files", "parse_dotenv_line"]
