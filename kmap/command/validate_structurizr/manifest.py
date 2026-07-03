"""Generated manifest validation for Structurizr workspaces."""

import json
from pathlib import Path


def _validate_generated_manifest(workspace_dir: Path) -> list[str]:
    manifest_file = workspace_dir / "model" / ".kmap-generated.json"
    if not manifest_file.exists():
        return [f"missing generated manifest: {manifest_file}"]
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"invalid generated manifest: {manifest_file}: {exc}"]

    errors = []
    if not isinstance(manifest, dict):
        return [f"invalid generated manifest: {manifest_file}: expected object"]
    files = manifest.get("files") or []
    if not isinstance(files, list):
        return [f"invalid generated manifest: {manifest_file}: files must be a list"]
    for file_name in files:
        if not isinstance(file_name, str):
            errors.append(f"invalid generated manifest: {manifest_file}: files entries must be strings")
            continue
        path = workspace_dir / file_name
        if not path.is_file():
            errors.append(f"manifest references missing file: {path}")
    return errors


__all__ = ["_validate_generated_manifest"]
