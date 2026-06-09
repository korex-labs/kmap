import subprocess
from argparse import Namespace

import pytest

from kmap.cli import apply_tool_config_overrides, build_parser
from kmap.command.view import commands as view_commands_module
from kmap.command.view import core as view_module
from kmap.command.view import docker as docker_module
from kmap.command.view import paths as view_paths_module


def completed(stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(["docker"], returncode, stdout=stdout, stderr=stderr)


def make_outputs(root, product="demo"):
    likec4 = root / "Likec4" / product
    structurizr = root / "Structurizr" / product
    common = root / "Structurizr" / "common"
    likec4.mkdir(parents=True)
    structurizr.mkdir(parents=True)
    common.mkdir(parents=True)
    (likec4 / "likec4.config.json").write_text("{}", encoding="utf-8")
    (structurizr / "workspace.dsl").write_text("workspace {}\n", encoding="utf-8")
    (common / "workspace.dsl").write_text("workspace {}\n", encoding="utf-8")


def patch_schemas_root(monkeypatch, root):
    monkeypatch.setattr(view_paths_module, "SCHEMAS_ROOT", root)
    monkeypatch.setattr(view_commands_module, "SCHEMAS_ROOT", root)


def docker_run_calls(calls):
    return [cmd for cmd in calls if cmd[:3] == ["docker", "run", "-d"]]


def view_args(product="demo", **overrides):
    values = {
        "product": product,
        "docker": "docker",
        "likec4_port": "5173",
        "structurizr_port": "8080",
        "likec4_image": "likec4/likec4",
        "structurizr_image": "structurizr/structurizr",
        "structurizr_args": "local",
        "restart": False,
        "stop": False,
        "no_likec4": False,
        "no_structurizr": False,
    }
    values.update(overrides)
    return Namespace(**values)


def test_parser_exposes_view_command():
    args = build_parser().parse_args(["view", "demo", "--restart", "--likec4-port", "5174"])

    assert args.command == "view"
    assert args.product == "demo"
    assert args.restart is True
    assert args.likec4_port == "5174"


def test_view_product_starts_both_viewers_and_prints_urls(monkeypatch, tmp_path, capsys):
    make_outputs(tmp_path)
    calls = []
    running_after_start = []

    patch_schemas_root(monkeypatch, tmp_path)
    monkeypatch.setattr(docker_module.time, "sleep", lambda _seconds: None)

    def fake_docker_run(cmd):
        calls.append(cmd)
        if cmd[:3] == ["docker", "ps", "--format"]:
            return completed(stdout="\n".join(running_after_start))
        if cmd[:4] == ["docker", "ps", "-a", "--format"]:
            return completed(stdout="")
        if cmd[:3] == ["docker", "run", "-d"]:
            running_after_start.append(cmd[5])
        return completed(stdout="container-id\n")

    monkeypatch.setattr(docker_module, "docker_run", fake_docker_run)

    assert view_module.view_product(view_args()) == 0

    likec4_run, structurizr_run = docker_run_calls(calls)
    assert likec4_run[:6] == ["docker", "run", "-d", "--init", "--name", "likec4-demo"]
    assert "--rm" not in likec4_run
    assert f"{tmp_path}:/data" in likec4_run
    assert "Likec4/demo" in likec4_run
    assert structurizr_run[:6] == ["docker", "run", "-d", "--init", "--name", "structurizr-demo"]
    assert "--rm" not in structurizr_run
    assert f"{tmp_path / 'Structurizr' / 'demo'}:/usr/local/structurizr" in structurizr_run
    assert f"{tmp_path / 'Structurizr' / 'common'}:/usr/local/common" in structurizr_run
    assert not any(arg.startswith("STRUCTURIZR_WORKSPACE_PATH=") for arg in structurizr_run)
    assert structurizr_run[-2:] == ["structurizr/structurizr", "local"]
    out = capsys.readouterr().out
    assert "LikeC4:      http://localhost:5173" in out
    assert "Structurizr: http://localhost:8080" in out


def test_view_docker_command_builders_preserve_paths_and_args(monkeypatch, tmp_path):
    patch_schemas_root(monkeypatch, tmp_path)
    args = view_args(structurizr_args='local "--port=9090"')

    likec4_cmd = view_module.likec4_run_command(args, "demo", "likec4-demo")
    structurizr_cmd = view_module.structurizr_run_command(args, "demo", "structurizr-demo")

    assert likec4_cmd == [
        "docker",
        "run",
        "-d",
        "--init",
        "--name",
        "likec4-demo",
        "-p",
        "5173:5173",
        "-v",
        f"{tmp_path}:/data",
        "likec4/likec4",
        "start",
        "--host",
        "0.0.0.0",
        "Likec4/demo",
    ]
    assert structurizr_cmd == [
        "docker",
        "run",
        "-d",
        "--init",
        "--name",
        "structurizr-demo",
        "-p",
        "8080:8080",
        "-v",
        f"{tmp_path / 'Structurizr' / 'demo'}:/usr/local/structurizr",
        "-v",
        f"{tmp_path / 'Structurizr' / 'common'}:/usr/local/common",
        "structurizr/structurizr",
        "local",
        "--port=9090",
    ]


def test_view_product_skips_already_running_containers(monkeypatch, tmp_path, capsys):
    make_outputs(tmp_path)
    calls = []
    patch_schemas_root(monkeypatch, tmp_path)
    monkeypatch.setattr(
        docker_module,
        "docker_run",
        lambda cmd: calls.append(cmd) or completed(stdout="likec4-demo\nstructurizr-demo\n"),
    )

    assert view_module.view_product(view_args()) == 0

    assert [cmd[:2] for cmd in calls] == [["docker", "ps"], ["docker", "ps"]]
    assert "Structurizr: http://localhost:8080" in capsys.readouterr().out


def test_view_product_restart_removes_containers_before_start(monkeypatch, tmp_path):
    make_outputs(tmp_path)
    calls = []
    patch_schemas_root(monkeypatch, tmp_path)
    monkeypatch.setattr(docker_module.time, "sleep", lambda _seconds: None)

    def fake_docker_run(cmd):
        calls.append(cmd)
        if cmd[:3] == ["docker", "ps", "--format"]:
            return completed(stdout="likec4-demo\n")
        return completed()

    monkeypatch.setattr(docker_module, "docker_run", fake_docker_run)

    assert view_module.view_product(view_args(restart=True, no_structurizr=True)) == 0

    assert calls[0] == ["docker", "rm", "-f", "likec4-demo"]
    assert calls[1][:6] == ["docker", "run", "-d", "--init", "--name", "likec4-demo"]


def test_view_product_removes_stopped_container_before_start(monkeypatch, tmp_path):
    make_outputs(tmp_path)
    calls = []
    patch_schemas_root(monkeypatch, tmp_path)
    monkeypatch.setattr(docker_module.time, "sleep", lambda _seconds: None)

    def fake_docker_run(cmd):
        calls.append(cmd)
        if cmd[:3] == ["docker", "ps", "--format"]:
            if docker_run_calls(calls):
                return completed(stdout="likec4-demo\n")
            return completed(stdout="")
        if cmd[:4] == ["docker", "ps", "-a", "--format"]:
            return completed(stdout="likec4-demo\n")
        return completed()

    monkeypatch.setattr(docker_module, "docker_run", fake_docker_run)

    assert view_module.view_product(view_args(no_structurizr=True)) == 0

    assert ["docker", "rm", "-f", "likec4-demo"] in calls
    assert docker_run_calls(calls)[0][:6] == ["docker", "run", "-d", "--init", "--name", "likec4-demo"]


def test_view_product_stop_removes_selected_containers(monkeypatch):
    calls = []
    monkeypatch.setattr(docker_module, "docker_run", lambda cmd: calls.append(cmd) or completed())

    assert view_module.view_product(view_args(stop=True, no_likec4=True)) == 0

    assert calls == [["docker", "rm", "-f", "structurizr-demo"]]


def test_view_product_reports_missing_outputs(tmp_path, monkeypatch):
    patch_schemas_root(monkeypatch, tmp_path)

    with pytest.raises(SystemExit, match="Missing"):
        view_module.view_product(view_args())


def test_view_product_validates_ports(tmp_path, monkeypatch):
    make_outputs(tmp_path)
    patch_schemas_root(monkeypatch, tmp_path)

    with pytest.raises(SystemExit, match="--likec4-port"):
        view_module.view_product(view_args(likec4_port="not-a-port"))
    with pytest.raises(SystemExit, match="--structurizr-port"):
        view_module.view_product(view_args(no_likec4=True, structurizr_port="70000"))


def test_view_product_prints_logs_hint_when_start_fails(monkeypatch, tmp_path, capsys):
    make_outputs(tmp_path)
    patch_schemas_root(monkeypatch, tmp_path)

    def fake_docker_run(cmd):
        if cmd == ["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}"]:
            return completed(stdout="likec4-demo\t0.0.0.0:5173->5173/tcp\n")
        if cmd[:3] == ["docker", "ps", "--format"]:
            return completed()
        if cmd[:4] == ["docker", "ps", "-a", "--format"]:
            return completed()
        return completed(stderr="port is already allocated", returncode=1)

    monkeypatch.setattr(docker_module, "docker_run", fake_docker_run)

    assert view_module.view_product(view_args(no_structurizr=True)) == 1

    captured = capsys.readouterr()
    assert "port is already allocated" in captured.err
    assert "--restart` only recreates this product's viewer containers" in captured.err
    assert "likec4-demo is currently using port 5173" in captured.err
    assert "--likec4-port 5174" in captured.err
    assert "docker logs likec4-demo" in captured.err


def test_view_product_prints_structurizr_port_conflict_hint(monkeypatch, tmp_path, capsys):
    make_outputs(tmp_path)
    patch_schemas_root(monkeypatch, tmp_path)

    def fake_docker_run(cmd):
        if cmd == ["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}"]:
            return completed(stdout="structurizr-demo\t0.0.0.0:8080->8080/tcp\n")
        if cmd[:3] == ["docker", "ps", "--format"]:
            return completed()
        if cmd[:4] == ["docker", "ps", "-a", "--format"]:
            return completed()
        return completed(stderr="port is already allocated", returncode=1)

    monkeypatch.setattr(docker_module, "docker_run", fake_docker_run)

    assert view_module.view_product(view_args(no_likec4=True)) == 1

    captured = capsys.readouterr()
    assert "port is already allocated" in captured.err
    assert "--restart` only recreates this product's viewer containers" in captured.err
    assert "structurizr-demo is currently using port 8080" in captured.err
    assert "--structurizr-port 8081" in captured.err
    assert "docker logs structurizr-demo" in captured.err


def test_view_product_reports_container_that_exits_after_start(monkeypatch, tmp_path, capsys):
    make_outputs(tmp_path)
    calls = []
    patch_schemas_root(monkeypatch, tmp_path)
    monkeypatch.setattr(docker_module.time, "sleep", lambda _seconds: None)

    def fake_docker_run(cmd):
        calls.append(cmd)
        if cmd[:3] == ["docker", "ps", "--format"]:
            return completed(stdout="")
        if cmd[:4] == ["docker", "ps", "-a", "--format"]:
            return completed(stdout="")
        return completed(stdout="container-id\n")

    monkeypatch.setattr(docker_module, "docker_run", fake_docker_run)

    assert view_module.view_product(view_args(no_likec4=True)) == 1

    captured = capsys.readouterr()
    assert "Structurizr: http://localhost:8080" not in captured.out
    assert "container exited after start: structurizr-demo" in captured.err
    assert "docker logs structurizr-demo" in captured.err


def test_view_product_prints_successful_viewer_when_later_viewer_exits(monkeypatch, tmp_path, capsys):
    make_outputs(tmp_path)
    calls = []
    running_after_start = []
    patch_schemas_root(monkeypatch, tmp_path)
    monkeypatch.setattr(docker_module.time, "sleep", lambda _seconds: None)

    def fake_docker_run(cmd):
        calls.append(cmd)
        if cmd[:3] == ["docker", "ps", "--format"]:
            return completed(stdout="\n".join(running_after_start))
        if cmd[:4] == ["docker", "ps", "-a", "--format"]:
            return completed(stdout="")
        if cmd[:3] == ["docker", "run", "-d"] and cmd[5] == "likec4-demo":
            running_after_start.append("likec4-demo")
        return completed(stdout="container-id\n")

    monkeypatch.setattr(docker_module, "docker_run", fake_docker_run)

    assert view_module.view_product(view_args()) == 1

    captured = capsys.readouterr()
    assert "LikeC4:      http://localhost:5173" in captured.out
    assert "Structurizr: http://localhost:8080" not in captured.out
    assert "container exited after start: structurizr-demo" in captured.err


def test_parser_defaults_to_current_structurizr_local_image():
    args = build_parser().parse_args(["view", "demo"])
    args = apply_tool_config_overrides(args)

    assert args.structurizr_image == "structurizr/structurizr"
    assert args.structurizr_args == "local"


def test_view_product_reports_invalid_structurizr_args(monkeypatch, tmp_path):
    make_outputs(tmp_path)
    patch_schemas_root(monkeypatch, tmp_path)
    monkeypatch.setattr(docker_module, "docker_run", lambda cmd: completed(stdout=""))

    with pytest.raises(SystemExit, match="Invalid --structurizr-args"):
        view_module.view_product(view_args(no_likec4=True, structurizr_args='"unterminated'))


def test_view_product_requires_at_least_one_viewer():
    with pytest.raises(SystemExit, match="Nothing to view"):
        view_module.view_product(view_args(no_likec4=True, no_structurizr=True))


def test_docker_container_running_reports_docker_errors(monkeypatch):
    monkeypatch.setattr(docker_module, "docker_run", lambda cmd: completed(stderr="docker failed", returncode=1))

    with pytest.raises(SystemExit, match="docker failed"):
        docker_module.docker_container_running("docker", "likec4-demo")


def test_docker_helpers_parse_names_and_use_fallback_errors(monkeypatch, capsys):
    assert docker_module.docker_names(" likec4-demo \n\nstructurizr-demo\n") == {"likec4-demo", "structurizr-demo"}
    assert docker_module.docker_error_message(completed(returncode=1), "fallback") == "fallback"

    calls = []
    monkeypatch.setattr(
        docker_module,
        "docker_run",
        lambda cmd: calls.append(cmd) or completed(returncode=1),
    )

    assert docker_module.docker_rm("docker", "missing") == 1
    assert calls == [["docker", "rm", "-f", "missing"]]
    assert "[kmap] failed to remove container: missing" in capsys.readouterr().err


def test_docker_container_exists_reports_fallback_error(monkeypatch):
    monkeypatch.setattr(docker_module, "docker_run", lambda cmd: completed(returncode=1))

    with pytest.raises(SystemExit, match="Failed to run docker ps -a"):
        docker_module.docker_container_exists("docker", "likec4-demo")


def test_docker_run_captures_output_without_checking(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return completed(stdout="ok")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = docker_module.docker_run(["docker", "ps"])

    assert result.stdout == "ok"
    assert calls == [(["docker", "ps"], {"check": False, "text": True, "capture_output": True})]


def test_docker_container_using_port_handles_failures_and_misses(monkeypatch):
    monkeypatch.setattr(docker_module, "docker_run", lambda cmd: completed(returncode=1))

    assert docker_module.docker_container_using_port("docker", "5173") == ""

    monkeypatch.setattr(
        docker_module,
        "docker_run",
        lambda cmd: completed(stdout="other\t0.0.0.0:8080->8080/tcp\nmalformed line\n"),
    )

    assert docker_module.docker_container_using_port("docker", "5173") == ""
