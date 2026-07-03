"""Subprocess helpers with kmap logging/progress integration."""

import subprocess
from typing import List, Optional

from .commands import shlex_join
from .progress import progress_command_failed, progress_command_finished, progress_command_started


def run_cmd(
    cmd: List[str],
    *,
    check: bool = True,
    capture: bool = True,
    timeout: Optional[int] = None,
    progress_failure: bool = True,
    progress: bool = True,
) -> subprocess.CompletedProcess:
    from . import eprint

    eprint(f"[kmap] run: {shlex_join(cmd)}")
    if progress:
        progress_command_started(cmd)
    try:
        cp = subprocess.run(
            cmd,
            check=check,
            capture_output=capture,
            text=True,
            timeout=timeout,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        if progress and progress_failure:
            progress_command_failed(cmd)
        raise
    if progress:
        progress_command_finished(cmd)
    return cp


def completed_process_message(error: subprocess.CalledProcessError) -> str:
    output = first_non_empty(error.stderr, error.stdout)
    if output:
        return output
    return f"exit code {error.returncode}"


def first_non_empty(*values: object) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


__all__ = ["completed_process_message", "first_non_empty", "run_cmd"]
