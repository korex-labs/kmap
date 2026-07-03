"""Workspace file validation for generated Structurizr workspaces."""

import re
from pathlib import Path

from .manifest import _validate_generated_manifest

INCLUDE_RE = re.compile(r"^\s*!include\s+(.+?)\s*$")


def _include_targets(workspace_file: Path, workspace_text: str | None = None) -> list[Path]:
    targets = []
    text = workspace_text if workspace_text is not None else workspace_file.read_text(encoding="utf-8")
    for line in text.splitlines():
        match = INCLUDE_RE.match(line)
        if match:
            targets.append(workspace_file.parent / match.group(1))
    return targets


def _validate_include_targets(workspace_file: Path, workspace_text: str | None = None) -> list[str]:
    errors = []
    try:
        include_targets = _include_targets(workspace_file, workspace_text)
    except (OSError, UnicodeDecodeError) as exc:
        return [f"cannot read workspace.dsl: {workspace_file}: {exc}"]
    for include_target in include_targets:
        if include_target.is_dir():
            if not any(include_target.glob("*.dsl")):
                errors.append(f"included directory has no .dsl files: {include_target}")
        elif not include_target.is_file():
            errors.append(f"missing include target: {include_target}")
    return errors


def _validate_workspace(workspace_dir: Path) -> list[str]:
    errors = []
    workspace_file = workspace_dir / "workspace.dsl"
    if not workspace_file.is_file():
        return [f"missing workspace.dsl: {workspace_file}"]

    try:
        workspace_text = workspace_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"cannot read workspace.dsl: {workspace_file}: {exc}"]

    if "workspace extends ../common/workspace.dsl" not in workspace_text:
        errors.append(f"workspace does not extend common workspace: {workspace_file}")

    common_workspace = workspace_dir.parent / "common" / "workspace.dsl"
    if not common_workspace.is_file():
        errors.append(f"missing common workspace: {common_workspace}")

    errors.extend(_validate_include_targets(workspace_file, workspace_text))
    errors.extend(_validate_generated_manifest(workspace_dir))
    return errors


__all__ = ["INCLUDE_RE", "_include_targets", "_validate_include_targets", "_validate_workspace"]
