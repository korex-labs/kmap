"""Workspace discovery for Structurizr validation."""

from pathlib import Path


def _selected_workspaces(root: Path, products: list[str]) -> list[Path]:
    if products:
        return [root / product for product in products]
    return sorted(path.parent.parent for path in root.glob("*/model/.kmap-generated.json"))


__all__ = ["_selected_workspaces"]
