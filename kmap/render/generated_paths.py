"""Generated renderer path helpers."""

from typing import Any, Dict

from ..config import slug_name


def unique_generated_path(
    project: Dict[str, Any],
    used_paths: set[str],
    *,
    directory: str,
    extension: str,
) -> str:
    base = slug_name(project.get("name") or project.get("title") or project.get("id") or "project")
    path = f"{directory}/{base}.{extension}"
    if path not in used_paths:
        used_paths.add(path)
        return path

    fallback = slug_name(project.get("id") or base)
    path = f"{directory}/{fallback}.{extension}"
    suffix = 2
    while path in used_paths:
        path = f"{directory}/{fallback}-{suffix}.{extension}"
        suffix += 1
    used_paths.add(path)
    return path


__all__ = ["unique_generated_path"]
