"""Console output mode and color helpers."""

import os
import sys
from typing import Optional, Tuple

LOG_RESET = "\033[0m"
LOG_COLORS = {
    "prefix": "\033[1;36m",
    "run": "\033[36m",
    "ok": "\033[32m",
    "warning": "\033[33m",
    "error": "\033[31m",
    "write": "\033[32m",
    "note": "\033[2m",
}
LOG_STYLE_RULES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("error", ("failed", "not found")),
    ("warning", ("warning",)),
    ("ok", ("config ok",)),
    ("write", ("wrote ",)),
    ("run", ("run:",)),
    ("note", ("info:", "no workloads matched")),
)
COLOR_DISABLED_VALUES = {"0", "false", "never", "no", "off"}
COLOR_ENABLED_VALUES = {"1", "true", "always", "yes", "on"}
_OUTPUT_MODE = os.environ.get("KMAP_OUTPUT", "lines").strip().lower() or "lines"


def output_mode() -> str:
    return _OUTPUT_MODE


def set_output_mode(mode: str) -> str:
    global _OUTPUT_MODE
    previous = _OUTPUT_MODE
    _OUTPUT_MODE = mode if mode in {"progress", "lines"} else "lines"
    return previous


def log_color_enabled() -> bool:
    preference = color_mode_preference(os.environ.get("KMAP_COLOR", "auto"))
    if preference is not None:
        return preference
    if os.environ.get("NO_COLOR") is not None:
        return False
    return sys.stderr.isatty()


def color_mode_preference(value: str) -> Optional[bool]:
    color_mode = str(value or "auto").strip().lower()
    if color_mode in COLOR_DISABLED_VALUES:
        return False
    if color_mode in COLOR_ENABLED_VALUES:
        return True
    return None


def colorize_log_message(message: str) -> str:
    if not log_color_enabled():
        return message

    style = log_message_style(message)
    if message.startswith("[kmap]"):
        return colorized_kmap_message(message, style)
    if style:
        return f"{style}{message}{LOG_RESET}"
    return message


def colorized_kmap_message(message: str, style: str) -> str:
    prefix = f"{LOG_COLORS['prefix']}[kmap]{LOG_RESET}"
    rest = message[len("[kmap]") :]
    if style:
        return f"{prefix}{style}{rest}{LOG_RESET}"
    return f"{prefix}{rest}"


def log_message_style(message: str) -> str:
    lower = message.lower()
    if lower.startswith("- "):
        return LOG_COLORS["error"]
    for color_key, tokens in LOG_STYLE_RULES:
        if any(token in lower for token in tokens):
            return LOG_COLORS[color_key]
    return ""


def should_print_in_progress(message: str) -> bool:
    lower = (message or "").lower()
    return any(token in lower for token in ("warning", "failed", "error", "not found"))


__all__ = [
    "color_mode_preference",
    "colorize_log_message",
    "colorized_kmap_message",
    "log_color_enabled",
    "log_message_style",
    "output_mode",
    "set_output_mode",
    "should_print_in_progress",
]
