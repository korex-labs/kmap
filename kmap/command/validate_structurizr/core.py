"""Command entrypoint for Structurizr validation."""

from pathlib import Path

from ...logging import eprint
from .discovery import _selected_workspaces
from .workspace import _validate_workspace


def validate_structurizr(args) -> int:
    root = Path(args.root)
    products = list(args.product or [])
    workspaces = _selected_workspaces(root, products)
    if not workspaces:
        eprint(f"[kmap] no generated Structurizr workspaces found in {root}")
        return 0

    errors = []
    for workspace_dir in workspaces:
        workspace_errors = _validate_workspace(workspace_dir)
        if workspace_errors:
            errors.extend(workspace_errors)
        else:
            eprint(f"[kmap] Structurizr workspace ok: {workspace_dir}")

    if errors:
        for error in errors:
            eprint(f"[kmap] Structurizr validation error: {error}")
        return 1
    return 0


__all__ = ["validate_structurizr"]
