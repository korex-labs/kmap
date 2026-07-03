"""kubectl and helm subprocess client."""

import shutil
import subprocess
import time
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any

from ..io import safe_json_loads
from ..logging import completed_process_message, eprint, progress_command_failed, run_cmd
from .kubeconfig import default_kubeconfig_path

EXEC_CAPTURE_MAX_ATTEMPTS = 3
EXEC_CAPTURE_RETRY_SLEEP_SECONDS = 1.0


@dataclass
class KubectlClient:
    kubectl: str = "kubectl"
    helm: str = "helm"
    context: str | None = None
    kubeconfig: str | None = None
    namespace: str | None = None
    request_timeout: str = "15s"
    qps_sleep: float = 0.15
    exec_sleep: float = 0.4
    exec_timeout: float = 20.0
    exec_attempts: int = EXEC_CAPTURE_MAX_ATTEMPTS

    def __post_init__(self) -> None:
        if not self.kubeconfig:
            self.kubeconfig = default_kubeconfig_path()
        if self.kubeconfig:
            self.kubeconfig = str(Path(self.kubeconfig).expanduser())

    def base(self) -> list[str]:
        cmd = [self.kubectl]
        if self.kubeconfig:
            cmd += ["--kubeconfig", self.kubeconfig]
        if self.context:
            cmd += ["--context", self.context]
        return cmd

    def current_context(self) -> str:
        try:
            cp = run_cmd([*self.base(), "config", "current-context"], timeout=self.command_timeout_seconds())
            ctx = cp.stdout.strip()
            return ctx or "unknown-context"
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            return "unknown-context"

    def cluster_label(self) -> str:
        parts = []
        if self.context:
            parts.append(f"context={self.context}")
        if self.kubeconfig:
            parts.append(f"kubeconfig={self.kubeconfig}")
        return ", ".join(parts) or "default kubectl context"

    def check_reachable(self) -> tuple[bool, str]:
        cmd = [*self.base(), f"--request-timeout={self.request_timeout}", "version", "--output=json"]
        try:
            cp = run_cmd(
                cmd,
                check=False,
                timeout=self.command_timeout_seconds(),
                progress_failure=False,
                progress=False,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            return False, str(exc)
        if cp.returncode == 0:
            return True, ""
        return False, completed_process_output(cp)

    def get_json(self, kind: str, namespace: str | None = None) -> dict[str, Any]:
        ns = namespace if namespace is not None else self.namespace
        cmd = [*self.base(), f"--request-timeout={self.request_timeout}", "get", kind]
        if ns:
            cmd += ["-n", ns]
        cmd += ["-o", "json"]
        try:
            cp = run_cmd(cmd, timeout=self.command_timeout_seconds())
        except subprocess.CalledProcessError as exc:
            scope = f" namespace={ns}" if ns else ""
            eprint(f"[kmap] warning: kubectl get {kind}{scope} failed: {completed_process_message(exc)}")
            return {"items": []}
        except subprocess.TimeoutExpired as exc:
            scope = f" namespace={ns}" if ns else ""
            eprint(f"[kmap] warning: kubectl get {kind}{scope} timed out after {exc.timeout}s")
            return {"items": []}
        time.sleep(self.qps_sleep)
        return safe_json_loads(cp.stdout, {"items": []})

    def helm_list(self, namespace: str) -> list[dict[str, Any]]:
        if not shutil.which(self.helm):
            return []
        cmd = [self.helm]
        if self.kubeconfig:
            cmd += ["--kubeconfig", self.kubeconfig]
        if self.context:
            cmd += ["--kube-context", self.context]
        cmd += ["list", "-n", namespace, "-o", "json"]
        try:
            cp = run_cmd(cmd, timeout=self.command_timeout_seconds())
            return safe_json_loads(cp.stdout, [])
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            return []

    def command_timeout_seconds(self) -> int:
        return max(10, request_timeout_seconds(self.request_timeout) + 5)

    def exec_capture(
        self,
        namespace: str,
        pod: str,
        container: str,
        argv: list[str],
        *,
        report_failure: bool = True,
    ) -> str:
        cmd = self.exec_command(namespace, pod, container, argv)
        max_attempts = max(1, int(self.exec_attempts))
        for attempt in range(max_attempts):
            output, retryable = self.exec_capture_attempt(cmd)
            if output:
                return output
            if not retryable:
                return ""
            if attempt < max_attempts - 1:
                time.sleep(EXEC_CAPTURE_RETRY_SLEEP_SECONDS)
        if report_failure:
            progress_command_failed(cmd)
        return ""

    def exec_command(self, namespace: str, pod: str, container: str, argv: list[str]) -> list[str]:
        return [*self.base(), "exec", pod, "-c", container, "-n", namespace, "--", *argv]

    def exec_capture_once(self, cmd: list[str]) -> str:
        output, _ = self.exec_capture_attempt(cmd)
        return output

    def exec_capture_attempt(self, cmd: list[str]) -> tuple[str, bool]:
        try:
            cp = run_cmd(cmd, check=False, timeout=self.exec_timeout, progress_failure=False, progress=False)
            time.sleep(self.exec_sleep)
            if cp.returncode == 0:
                return (cp.stdout or "").strip(), False
            return "", retryable_exec_failure(cp.returncode, cp.stderr or "")
        except (subprocess.TimeoutExpired, OSError):
            return "", True


def retryable_exec_failure(returncode: int, stderr: str) -> bool:
    lower = (stderr or "").lower()
    non_retryable_tokens = (
        "executable file not found",
        "no such file or directory",
        "not found in $path",
        "stat /vault/vault-env",
    )
    if returncode in {126, 127}:
        return False
    return not any(token in lower for token in non_retryable_tokens)


def request_timeout_seconds(value: str) -> int:
    raw = str(value or "").strip().lower()
    try:
        if raw.endswith("ms"):
            seconds = float(raw[:-2]) / 1000
        elif raw.endswith("s"):
            seconds = float(raw[:-1])
        elif raw.endswith("m"):
            seconds = float(raw[:-1]) * 60
        else:
            seconds = float(raw)
        if not isfinite(seconds):
            return 15
        return max(1, int(seconds))
    except ValueError:
        return 15


def completed_process_output(process: subprocess.CompletedProcess) -> str:
    stderr = (process.stderr or "").strip()
    stdout = (process.stdout or "").strip()
    if stderr:
        return stderr
    if stdout:
        return stdout
    return f"exit code {process.returncode}"


__all__ = ["KubectlClient", "completed_process_output", "request_timeout_seconds", "retryable_exec_failure"]
