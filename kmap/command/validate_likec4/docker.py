"""Docker execution helpers for LikeC4 validation."""

import os
import subprocess
from pathlib import Path


def likec4_validate_command(docker: str, image: str, mount_root: Path, project: str) -> list[str]:
    return [
        docker,
        "run",
        "--rm",
        "-v",
        f"{os.fspath(mount_root)}:/data",
        image,
        "validate",
        project,
    ]


def run_likec4_validate(docker: str, image: str, mount_root: Path, project: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        likec4_validate_command(docker, image, mount_root, project),
        check=False,
        text=True,
        capture_output=True,
    )


__all__ = ["likec4_validate_command", "run_likec4_validate"]
