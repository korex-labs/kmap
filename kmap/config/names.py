"""Config naming helpers."""

import re


def slug_name(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", s or "")
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "unknown"


__all__ = ["slug_name"]
