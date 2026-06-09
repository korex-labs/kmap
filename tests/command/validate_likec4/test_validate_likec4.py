import subprocess
from argparse import Namespace

from kmap.command.validate_likec4 import selected_likec4_projects, validate_likec4
from kmap.command.validate_likec4.docker import likec4_validate_command, run_likec4_validate


def test_selected_likec4_projects_finds_generated_projects(tmp_path):
    (tmp_path / "demo").mkdir()
    (tmp_path / "demo" / "likec4.config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "common").mkdir()
    (tmp_path / "common" / "likec4.config.json").write_text("{}", encoding="utf-8")

    assert selected_likec4_projects(tmp_path, []) == [tmp_path / "common", tmp_path / "demo"]
    assert selected_likec4_projects(tmp_path, ["demo"]) == [tmp_path / "demo"]


def test_selected_likec4_projects_skips_aggregate_folders_by_default(tmp_path):
    (tmp_path / "demo").mkdir()
    (tmp_path / "demo" / "likec4.config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "aggregate").mkdir()
    (tmp_path / "aggregate" / "likec4.config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "aggregate" / "child").mkdir()
    (tmp_path / "aggregate" / "child" / "likec4.config.json").write_text("{}", encoding="utf-8")

    assert selected_likec4_projects(tmp_path, []) == [tmp_path / "aggregate" / "child", tmp_path / "demo"]
    assert selected_likec4_projects(tmp_path, [], include_multi_project=True) == [
        tmp_path / "aggregate",
        tmp_path / "aggregate" / "child",
        tmp_path / "demo",
    ]
    assert selected_likec4_projects(tmp_path, ["aggregate"]) == [tmp_path / "aggregate"]


def test_validate_likec4_runs_docker_for_each_project(monkeypatch, tmp_path, capsys):
    calls = []
    (tmp_path / "demo").mkdir()
    (tmp_path / "demo" / "likec4.config.json").write_text("{}", encoding="utf-8")

    def fake_run_likec4_validate(docker, image, mount_root, project):
        calls.append((docker, image, mount_root, project))
        return subprocess.CompletedProcess(["docker"], 0, stdout="", stderr="")

    monkeypatch.setattr("kmap.command.validate_likec4.run_likec4_validate", fake_run_likec4_validate)

    rc = validate_likec4(
        Namespace(root=str(tmp_path), product=[], include_multi_project=False, docker="dockerx", image="likec4/test")
    )

    assert rc == 0
    assert calls == [("dockerx", "likec4/test", tmp_path.parent.resolve(), f"{tmp_path.name}/demo")]
    assert "Validating LikeC4 project" in capsys.readouterr().err


def test_likec4_validate_command_preserves_mount_and_project(tmp_path):
    assert likec4_validate_command("podman", "likec4/test", tmp_path, "Likec4/demo") == [
        "podman",
        "run",
        "--rm",
        "-v",
        f"{tmp_path}:/data",
        "likec4/test",
        "validate",
        "Likec4/demo",
    ]


def test_run_likec4_validate_executes_command_with_captured_output(monkeypatch, tmp_path):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_likec4_validate("podman", "likec4/test", tmp_path, "Likec4/demo")

    assert result.stdout == "ok"
    assert calls == [
        (
            likec4_validate_command("podman", "likec4/test", tmp_path, "Likec4/demo"),
            {"check": False, "text": True, "capture_output": True},
        )
    ]


def test_validate_likec4_returns_docker_failure(monkeypatch, tmp_path, capsys):
    (tmp_path / "demo").mkdir()
    (tmp_path / "demo" / "likec4.config.json").write_text("{}", encoding="utf-8")

    def fake_run_likec4_validate(docker, image, mount_root, project):
        return subprocess.CompletedProcess(["docker"], 9, stdout="", stderr="invalid c4")

    monkeypatch.setattr("kmap.command.validate_likec4.run_likec4_validate", fake_run_likec4_validate)

    assert (
        validate_likec4(
            Namespace(
                root=str(tmp_path), product=[], include_multi_project=False, docker="docker", image="likec4/likec4"
            )
        )
        == 9
    )
    assert "invalid c4" in capsys.readouterr().err


def test_validate_likec4_reports_no_projects(tmp_path, capsys):
    assert (
        validate_likec4(
            Namespace(
                root=str(tmp_path), product=[], include_multi_project=False, docker="docker", image="likec4/likec4"
            )
        )
        == 0
    )
    assert "no LikeC4 projects found" in capsys.readouterr().err
