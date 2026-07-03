"""Logging and subprocess helpers."""

import shutil
import subprocess
import sys
import time

from . import progress as _progress
from .commands import command_namespace, shlex_join, short_command, visible_command_parts
from .output import (
    color_mode_preference,
    colorize_log_message,
    log_color_enabled,
    output_mode,
    set_output_mode,
    should_print_in_progress,
)
from .progress import (
    ProgressBar,
    active_progress,
    fit_progress_line,
    progress_command_failed,
    progress_command_finished,
    progress_command_started,
    progress_line,
)
from .runner import completed_process_message, first_non_empty, run_cmd

_ACTIVE_PROGRESS = _progress._ACTIVE_PROGRESS


def set_active_progress(progress: ProgressBar | None) -> ProgressBar | None:
    previous = _progress.set_active_progress(progress)
    globals()["_ACTIVE_PROGRESS"] = _progress._ACTIVE_PROGRESS
    return previous


def eprint(*args: object, **kwargs: object) -> None:
    progress = active_progress()
    if len(args) == 1 and isinstance(args[0], str):
        if output_mode() == "progress" and not should_print_in_progress(args[0]):
            return
        if progress and progress.enabled:
            progress.interrupt()
        args = (colorize_log_message(args[0]),)
    print(*args, file=sys.stderr, **kwargs)


__all__ = [
    "ProgressBar",
    "color_mode_preference",
    "colorize_log_message",
    "command_namespace",
    "completed_process_message",
    "eprint",
    "first_non_empty",
    "fit_progress_line",
    "log_color_enabled",
    "output_mode",
    "progress_command_failed",
    "progress_command_finished",
    "progress_command_started",
    "progress_line",
    "run_cmd",
    "set_active_progress",
    "set_output_mode",
    "shlex_join",
    "short_command",
    "should_print_in_progress",
    "shutil",
    "subprocess",
    "time",
    "visible_command_parts",
]
