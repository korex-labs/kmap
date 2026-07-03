import contextlib
import subprocess

import pytest

from kmap.logging import (
    ProgressBar,
    color_mode_preference,
    colorize_log_message,
    command_namespace,
    completed_process_message,
    eprint,
    first_non_empty,
    fit_progress_line,
    log_color_enabled,
    progress_command_failed,
    progress_command_finished,
    progress_command_started,
    progress_line,
    run_cmd,
    set_active_progress,
    set_output_mode,
    shlex_join,
    short_command,
    should_print_in_progress,
    visible_command_parts,
)


def test_logging_helpers_colorize_and_report_process_errors(monkeypatch, capsys):
    monkeypatch.setenv("KMAP_COLOR", "always")

    colored = colorize_log_message("[kmap] config ok: config/demo.yaml")
    assert "\033[" in colored
    assert "[kmap]" in colored

    error = subprocess.CalledProcessError(1, ["cmd"], stderr="boom")
    assert completed_process_message(error) == "boom"

    eprint("[kmap] config ok: config/demo.yaml")
    captured = capsys.readouterr()
    assert "[kmap]" in captured.err


def test_completed_process_message_prefers_stderr_then_stdout_then_exit_code():
    assert completed_process_message(subprocess.CalledProcessError(1, ["cmd"], output="ok", stderr="boom")) == "boom"
    assert completed_process_message(subprocess.CalledProcessError(2, ["cmd"], output="ok", stderr="")) == "ok"
    assert completed_process_message(subprocess.CalledProcessError(3, ["cmd"], output="", stderr="")) == "exit code 3"


def test_log_color_enabled_honors_env_modes(monkeypatch):
    monkeypatch.setenv("KMAP_COLOR", "never")
    assert log_color_enabled() is False

    monkeypatch.setenv("KMAP_COLOR", "always")
    monkeypatch.setenv("NO_COLOR", "1")
    assert log_color_enabled() is True

    monkeypatch.setenv("KMAP_COLOR", "auto")
    assert log_color_enabled() is False


def test_color_mode_preference_normalizes_known_values():
    assert color_mode_preference("yes") is True
    assert color_mode_preference("off") is False
    assert color_mode_preference("auto") is None
    assert color_mode_preference("") is None


def test_eprint_filters_progress_noise_and_interrupts_active_bar(monkeypatch, capsys):
    previous_mode = set_output_mode("progress")
    bar = ProgressBar(total=1, enabled=True)
    previous_progress = set_active_progress(bar)
    try:
        eprint("[kmap] wrote quiet progress detail")
        assert capsys.readouterr().err == ""

        eprint("[kmap] warning: noisy progress detail")
        captured = capsys.readouterr()
    finally:
        set_active_progress(previous_progress)
        set_output_mode(previous_mode)

    assert "warning" in captured.err
    assert should_print_in_progress("[kmap] not found") is True
    assert should_print_in_progress("[kmap] wrote file") is False


def test_progress_helpers_shorten_and_fit_commands(monkeypatch):
    monkeypatch.setattr("kmap.logging.shutil.get_terminal_size", lambda fallback: type("Size", (), {"columns": 60})())

    assert short_command(
        [
            "kubectl",
            "--context",
            "demo-context",
            "--request-timeout=15s",
            "get",
            "pod",
            "-o",
            "json",
            "-n",
            "demo-monitoring-prod-0001",
        ]
    ) == ("kubectl get pod -n demo-monitoring-prod-0001")
    assert short_command(
        [
            "kubectl",
            "--context",
            "demo-context",
            "exec",
            "pod-1",
            "-c",
            "app",
            "-n",
            "demo",
            "--",
            "env",
        ]
    ) == ("kubectl exec pod-1 -c app -- env -n demo")
    line = fit_progress_line("[kmap] ", "x" * 200)

    assert len(line) == 59
    assert line.endswith("…")


def test_progress_line_builds_expected_prefix(monkeypatch):
    monkeypatch.setattr("kmap.logging.shutil.get_terminal_size", lambda fallback: type("Size", (), {"columns": 80})())

    line = progress_line(current=1, total=4, eta="ETA 00:03", message="collecting pods")

    assert line.startswith("\r[kmap] [######------------------] 1/4  25% ETA 00:03 collecting pods")
    assert len(line) == 80


def test_short_command_preserves_namespace_from_namespace_equals_form():
    assert (
        short_command(
            [
                "kubectl",
                "--kubeconfig",
                "/tmp/kubeconfig",
                "get",
                "svc",
                "--namespace=payments",
                "--output=json",
            ]
        )
        == "kubectl get svc --output=json -n payments"
    )


def test_command_part_helpers_strip_context_and_keep_namespace_for_display():
    cmd = [
        "kubectl",
        "--context=prod",
        "--kubeconfig",
        "/tmp/kubeconfig",
        "get",
        "pods",
        "--namespace",
        "payments",
        "--output=json",
    ]

    assert visible_command_parts(cmd) == ["kubectl", "get", "pods", "--output=json"]
    assert command_namespace(cmd) == "payments"


def test_shlex_join_falls_back_for_non_string_parts():
    assert shlex_join(["kubectl", "get", 123]) == "kubectl get 123"


def test_disabled_progress_bar_methods_are_noops(capsys):
    bar = ProgressBar(total=1, enabled=False)

    bar.start("start")
    bar.add_step("step")
    bar.update("update")
    bar.advance("advance")
    bar.done()
    bar.interrupt()
    bar.fail()

    assert bar.current == 0
    assert bar.total == 1
    assert capsys.readouterr().err == ""


def test_progress_bar_done_fail_and_eta_render(capsys, monkeypatch):
    monkeypatch.setattr("kmap.logging.shutil.get_terminal_size", lambda fallback: type("Size", (), {"columns": 80})())
    times = iter([1.0, 5.0, 5.0, 5.0])
    monkeypatch.setattr("kmap.logging.time.monotonic", lambda: next(times))
    bar = ProgressBar(total=3, enabled=True)

    bar.start("start")
    bar.advance("one")
    bar.fail("failed")
    bar.done("done")

    rendered = capsys.readouterr().err
    assert "ETA 00:08" in rendered
    assert "failed" in rendered
    assert "done" in rendered


def test_progress_command_hooks_advance_active_bar(capsys):
    previous_mode = set_output_mode("progress")
    bar = ProgressBar(total=0, enabled=True)
    previous_progress = set_active_progress(bar)
    try:
        progress_command_started(["kubectl", "get", "pod"])
        progress_command_finished(["kubectl", "get", "pod"])
    finally:
        set_active_progress(previous_progress)
        set_output_mode(previous_mode)

    assert bar.total == 1
    assert bar.current == 1
    assert "kubectl get pod" in capsys.readouterr().err


def test_progress_command_failed_marks_active_bar(capsys):
    previous_mode = set_output_mode("progress")
    bar = ProgressBar(total=0, enabled=True)
    previous_progress = set_active_progress(bar)
    try:
        progress_command_failed(["kubectl", "get", "pod"])
    finally:
        set_active_progress(previous_progress)
        set_output_mode(previous_mode)

    assert "failed kubectl get pod" in capsys.readouterr().err


def test_run_cmd_updates_progress_on_success(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr("kmap.logging.subprocess.run", fake_run)

    previous_mode = set_output_mode("progress")
    bar = ProgressBar(total=0, enabled=True)
    previous_progress = set_active_progress(bar)
    try:
        result = run_cmd(["kubectl", "get", "pod"], timeout=5)
    finally:
        set_active_progress(previous_progress)
        set_output_mode(previous_mode)

    assert result.stdout == "ok"
    assert calls == [
        (
            ["kubectl", "get", "pod"],
            {"check": True, "capture_output": True, "text": True, "timeout": 5},
        )
    ]
    assert bar.total == 1
    assert bar.current == 1


def test_run_cmd_can_suppress_progress_failure(monkeypatch):
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=1)

    monkeypatch.setattr("kmap.logging.subprocess.run", fake_run)

    previous_mode = set_output_mode("progress")
    bar = ProgressBar(total=0, enabled=True)
    previous_progress = set_active_progress(bar)
    try:
        with contextlib.suppress(subprocess.TimeoutExpired):
            run_cmd(["kubectl", "exec", "pod"], timeout=1, progress_failure=False)
    finally:
        set_active_progress(previous_progress)
        set_output_mode(previous_mode)

    assert bar.total == 1
    assert bar.current == 0
    assert not bar.last_message.startswith("failed")


def test_run_cmd_can_suppress_progress_accounting(monkeypatch):
    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr("kmap.logging.subprocess.run", fake_run)

    previous_mode = set_output_mode("progress")
    bar = ProgressBar(total=0, enabled=True)
    previous_progress = set_active_progress(bar)
    try:
        result = run_cmd(["kubectl", "exec", "pod"], progress=False)
    finally:
        set_active_progress(previous_progress)
        set_output_mode(previous_mode)

    assert result.stdout == "ok"
    assert bar.total == 0
    assert bar.current == 0


def test_run_cmd_marks_progress_failed_by_default(monkeypatch):
    def fake_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd, stderr="boom")

    monkeypatch.setattr("kmap.logging.subprocess.run", fake_run)

    previous_mode = set_output_mode("progress")
    bar = ProgressBar(total=0, enabled=True)
    previous_progress = set_active_progress(bar)
    try:
        with pytest.raises(subprocess.CalledProcessError):
            run_cmd(["kubectl", "get", "pod"])
    finally:
        set_active_progress(previous_progress)
        set_output_mode(previous_mode)

    assert bar.total == 1
    assert bar.current == 0
    assert bar.last_message.startswith("failed")


def test_run_cmd_does_not_mark_progress_failed_for_unexpected_errors(monkeypatch):
    def fake_run(cmd, **kwargs):
        raise RuntimeError("bug")

    monkeypatch.setattr("kmap.logging.subprocess.run", fake_run)

    previous_mode = set_output_mode("progress")
    bar = ProgressBar(total=0, enabled=True)
    previous_progress = set_active_progress(bar)
    try:
        with pytest.raises(RuntimeError, match="bug"):
            run_cmd(["kubectl", "get", "pod"])
    finally:
        set_active_progress(previous_progress)
        set_output_mode(previous_mode)

    assert bar.total == 1
    assert bar.current == 0
    assert not bar.last_message.startswith("failed")


def test_first_non_empty_uses_first_stripped_text():
    assert first_non_empty("", None, "  value  ", "later") == "value"
    assert first_non_empty("", None) == ""
