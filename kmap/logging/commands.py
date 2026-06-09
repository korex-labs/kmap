"""Command redaction and display helpers."""

from typing import List

COMMAND_VALUE_OPTIONS = {"--context", "--kubeconfig", "--request-timeout", "--kube-context", "-o", "--output"}
COMMAND_VALUE_OPTION_PREFIXES = ("--context=", "--kubeconfig=", "--request-timeout=", "--kube-context=")
COMMAND_NAMESPACE_OPTIONS = {"-n", "--namespace"}


def short_command(cmd: List[str]) -> str:
    cleaned = visible_command_parts(cmd)
    namespace = command_namespace(cmd)
    if namespace and cleaned and cleaned[0] == "kubectl":
        cleaned += ["-n", namespace]
    return shlex_join(cleaned)


def visible_command_parts(cmd: List[str]) -> List[str]:
    cleaned: List[str] = []
    skip_next = False
    for part in cmd:
        if skip_next:
            skip_next = False
            continue
        if command_part_hides_next(part):
            skip_next = True
            continue
        if command_part_is_hidden(part):
            continue
        cleaned.append(part)
    return cleaned


def command_part_hides_next(part: str) -> bool:
    return part in COMMAND_VALUE_OPTIONS or part in COMMAND_NAMESPACE_OPTIONS


def command_part_is_hidden(part: str) -> bool:
    return part.startswith(COMMAND_VALUE_OPTION_PREFIXES) or part.startswith("--namespace=")


def command_namespace(cmd: List[str]) -> str:
    for index, part in enumerate(cmd[:-1]):
        if part in {"-n", "--namespace"}:
            return cmd[index + 1]
    for part in cmd:
        if part.startswith("--namespace="):
            return part.split("=", 1)[1]
    return ""


def shlex_join(cmd: List[str]) -> str:
    try:
        import shlex

        return shlex.join(cmd)
    except Exception:
        return " ".join(cmd)


__all__ = [
    "command_namespace",
    "command_part_hides_next",
    "command_part_is_hidden",
    "shlex_join",
    "short_command",
    "visible_command_parts",
]
