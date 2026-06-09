"""Command entrypoint for LikeC4 validation."""

import argparse
import sys
from pathlib import Path

from ...logging import eprint
from .discovery import selected_likec4_projects
from .docker import run_likec4_validate


def validate_likec4(args: argparse.Namespace) -> int:
    root = Path(args.root)
    products = list(args.product or [])
    projects = selected_likec4_projects(
        root,
        products,
        include_multi_project=getattr(args, "include_multi_project", False),
    )
    if not projects:
        eprint(f"[kmap] no LikeC4 projects found in {root}")
        return 0

    rc = 0
    mount_root = root.parent.resolve()
    for project_dir in projects:
        project = project_dir.relative_to(root.parent).as_posix()
        eprint(f"[kmap] Validating LikeC4 project: {project}")
        result = _run_likec4_validate(args.docker, args.image, mount_root, project)
        if result.returncode == 0:
            continue
        rc = result.returncode or 1
        eprint(result.stderr.strip() or result.stdout.strip() or f"[kmap] LikeC4 validation failed: {project}")
    return rc


def _run_likec4_validate(docker: str, image: str, mount_root: Path, project: str):
    package = sys.modules.get("kmap.command.validate_likec4")
    runner = getattr(package, "run_likec4_validate", run_likec4_validate)
    return runner(docker, image, mount_root, project)


__all__ = ["_run_likec4_validate", "run_likec4_validate", "selected_likec4_projects", "validate_likec4"]
