"""Progress lifecycle helpers for multi-step commands."""

from collections.abc import Iterator
from contextlib import contextmanager

from ..logging import ProgressBar, set_active_progress, set_output_mode


@contextmanager
def run_all_progress(*, enabled: bool, total: int) -> Iterator[ProgressBar]:
    previous_output_mode = set_output_mode("progress" if enabled else "lines")
    progress = ProgressBar(total=total, enabled=enabled)
    previous_progress = set_active_progress(progress if enabled else None)
    progress.start("starting")
    try:
        yield progress
    finally:
        set_active_progress(previous_progress)
        set_output_mode(previous_output_mode)


__all__ = ["run_all_progress"]
