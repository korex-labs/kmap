"""Docker lifecycle helpers for local kmap viewers."""

import subprocess
import time

from ...logging import eprint

DOCKER_NAMES_FORMAT = "{{.Names}}"
DOCKER_PORTS_FORMAT = "{{.Names}}\t{{.Ports}}"


def docker_run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def docker_error_message(result: subprocess.CompletedProcess[str], fallback: str) -> str:
    return result.stderr.strip() or fallback


def docker_names(stdout: str) -> set[str]:
    return {line.strip() for line in stdout.splitlines() if line.strip()}


def docker_container_running(docker_bin: str, name: str) -> bool:
    result = docker_run([docker_bin, "ps", "--format", DOCKER_NAMES_FORMAT])
    if result.returncode != 0:
        raise SystemExit(docker_error_message(result, f"Failed to run {docker_bin} ps"))
    return name in docker_names(result.stdout)


def docker_container_exists(docker_bin: str, name: str) -> bool:
    result = docker_run([docker_bin, "ps", "-a", "--format", DOCKER_NAMES_FORMAT])
    if result.returncode != 0:
        raise SystemExit(docker_error_message(result, f"Failed to run {docker_bin} ps -a"))
    return name in docker_names(result.stdout)


def docker_rm(docker_bin: str, name: str) -> int:
    result = docker_run([docker_bin, "rm", "-f", name])
    if result.returncode != 0 and "No such container" not in result.stderr:
        eprint(docker_error_message(result, f"[kmap] failed to remove container: {name}"))
        return result.returncode
    return 0


def docker_container_using_port(docker_bin: str, port: str) -> str:
    result = docker_run([docker_bin, "ps", "--format", DOCKER_PORTS_FORMAT])
    if result.returncode != 0:
        return ""
    needle = f":{port}->"
    for line in result.stdout.splitlines():
        if needle not in line:
            continue
        name, _, _ports = line.partition("\t")
        return name.strip()
    return ""


def eprint_logs_hint(name: str) -> None:
    eprint(f"[kmap] check logs: docker logs {name}")


def ensure_started(docker_bin: str, name: str) -> int:
    time.sleep(1)
    if docker_container_running(docker_bin, name):
        return 0
    eprint(f"[kmap] container exited after start: {name}")
    eprint_logs_hint(name)
    return 1


def prepare_viewer_container(docker_bin: str, name: str, *, restart: bool, kind: str) -> int | None:
    if restart:
        rc = docker_rm(docker_bin, name)
        return rc if rc != 0 else None
    if docker_container_running(docker_bin, name):
        eprint(f"[kmap] {kind} container already running: {name}")
        return 0
    if docker_container_exists(docker_bin, name):
        rc = docker_rm(docker_bin, name)
        return rc if rc != 0 else None
    return None


__all__ = [
    "DOCKER_NAMES_FORMAT",
    "DOCKER_PORTS_FORMAT",
    "docker_container_exists",
    "docker_container_running",
    "docker_container_using_port",
    "docker_error_message",
    "docker_names",
    "docker_rm",
    "docker_run",
    "ensure_started",
    "eprint_logs_hint",
    "prepare_viewer_container",
]
