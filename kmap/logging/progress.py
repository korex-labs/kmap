"""Progress bar and command progress helpers."""

import shutil
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

from .commands import short_command
from .output import output_mode

_ACTIVE_PROGRESS: Optional["ProgressBar"] = None


def set_active_progress(progress: Optional["ProgressBar"]) -> Optional["ProgressBar"]:
    global _ACTIVE_PROGRESS
    previous = _ACTIVE_PROGRESS
    _ACTIVE_PROGRESS = progress
    return previous


def active_progress() -> Optional["ProgressBar"]:
    if output_mode() != "progress":
        return None
    return _ACTIVE_PROGRESS


@dataclass
class ProgressBar:
    total: int
    label: str = "kmap"
    enabled: bool = True

    def __post_init__(self):
        self.current = 0
        self.last_message = ""
        self.started_at = 0.0

    def start(self, message: str = "") -> None:
        if not self.enabled:
            return
        if not self.started_at:
            self.started_at = time.monotonic()
        self.last_message = message
        self._render(message)

    def add_step(self, message: str) -> None:
        if not self.enabled:
            return
        self.total += 1
        self.last_message = message
        self._render(message)

    def update(self, message: str) -> None:
        if not self.enabled:
            return
        self.last_message = message
        self._render(message)

    def advance(self, message: str) -> None:
        if not self.enabled:
            return
        self.current = min(self.total, self.current + 1)
        self.last_message = message
        self._render(message)

    def done(self, message: str = "done") -> None:
        if not self.enabled:
            return
        self.current = self.total
        self.last_message = message
        self._render(message)
        print(file=sys.stderr)

    def interrupt(self) -> None:
        if self.enabled:
            print(file=sys.stderr)

    def fail(self, message: str = "failed") -> None:
        if not self.enabled:
            return
        self.last_message = message
        self._render(message)
        print(file=sys.stderr)

    def _render(self, message: str) -> None:
        print(
            progress_line(current=self.current, total=self.total, eta=self._eta_label(), message=message),
            end="",
            file=sys.stderr,
            flush=True,
        )

    def _eta_label(self) -> str:
        if not self.started_at or self.current <= 0 or self.current >= self.total:
            return "ETA --:--"
        elapsed = max(0.0, time.monotonic() - self.started_at)
        remaining = max(0, self.total - self.current)
        seconds = int((elapsed / self.current) * remaining)
        return f"ETA {seconds // 60:02d}:{seconds % 60:02d}"


def fit_progress_line(prefix: str, message: str) -> str:
    width = max(40, shutil.get_terminal_size((100, 20)).columns)
    available = max(8, width - len(prefix) - 1)
    text = " ".join(str(message or "").split())
    if len(text) > available:
        text = text[: max(1, available - 1)] + "…"
    return f"{prefix}{text}".ljust(width - 1)


def progress_line(*, current: int, total: int, eta: str, message: str) -> str:
    safe_total = max(1, total)
    width = 24
    ratio = min(1.0, current / safe_total)
    filled = int(width * ratio)
    bar = "#" * filled + "-" * (width - filled)
    percent = int(ratio * 100)
    prefix = f"[kmap] [{bar}] {current}/{total} {percent:3d}% {eta} "
    return "\r" + fit_progress_line(prefix, message)


def progress_command_started(cmd: List[str]) -> None:
    update_command_progress(cmd, "running", "add_step")


def progress_command_finished(cmd: List[str]) -> None:
    update_command_progress(cmd, "finished", "advance")


def progress_command_failed(cmd: List[str]) -> None:
    update_command_progress(cmd, "failed", "fail")


def update_command_progress(cmd: List[str], action: str, method_name: str) -> None:
    progress = active_progress()
    if progress:
        getattr(progress, method_name)(f"{action} {short_command(cmd)}")


__all__ = [
    "ProgressBar",
    "active_progress",
    "fit_progress_line",
    "progress_command_failed",
    "progress_command_finished",
    "progress_command_started",
    "progress_line",
    "set_active_progress",
]
