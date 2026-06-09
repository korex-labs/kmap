"""Generated manifest validation for Structurizr workspaces."""

import json
from pathlib import Path


def _validate_generated_manifest(workspace_dir: Path) -> list[str]:
    manifest_file = workspace_dir / "model" / ".kmap-generated.json"
    if not manifest_file.exists():
        return [f"missing generated manifest: {manifest_file}"]
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"invalid generated manifest: {manifest_file}: {exc}"]

    errors = []
    for file_name in manifest.get("files") or []:
        path = workspace_dir / file_name
        if not path.is_file():
            errors.append(f"manifest references missing file: {path}")
    return errors


__all__ = ["_validate_generated_manifest"]
