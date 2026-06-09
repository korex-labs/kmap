import json
from argparse import Namespace

import pytest

from kmap.command import render as render_command
from kmap.paths import SCHEMAS_ROOT
from kmap.render.likec4 import default_likec4_output_dir


def minimal_architecture():
    return {
        "workspace": {
            "generated_at": "2026-04-28T10:00:00Z",
            "generator": {
                "tool": "kmap",
                "version": "0.1.0",
                "config_file": "config/demo.yaml",
                "rules_file": "GENERATION_RULES.md",
            },
        },
        "product": {"name": "demo", "title": "Demo"},
    }


def test_render_command_dispatches_selected_outputs(monkeypatch):
    calls = []

    monkeypatch.setattr(
        render_command,
        "render_structurizr_architecture",
        lambda args: calls.append(("structurizr", args)) or 0,
    )
    monkeypatch.setattr(render_command, "render_likec4", lambda args: calls.append(("likec4", args)) or 0)

    rc = render_command.render_outputs(
        Namespace(
            architecture_file="architecture.json",
            render="both",
            struct_output_dir="Structurizr/demo",
            likec4_output_dir="Likec4/demo",
            likec4_common_path="../common",
        )
    )

    assert rc == 0
    assert [name for name, _ in calls] == ["structurizr", "likec4"]
    assert calls[0][1].output_dir == "Structurizr/demo"
    assert calls[1][1].output_dir == "Likec4/demo"


def test_render_command_derives_default_structurizr_output_dir(tmp_path):
    architecture_file = tmp_path / "architecture.json"
    architecture_file.write_text(json.dumps(minimal_architecture()), encoding="utf-8")

    assert render_command.architecture_product_name(str(architecture_file)) == "demo"
    assert (
        render_command.default_structurizr_output_dir("Demo Product") == SCHEMAS_ROOT / "Structurizr" / "Demo-Product"
    )


def test_renderers_share_schema_root_for_default_output_dirs():
    assert (
        render_command.default_structurizr_output_dir("Demo Product") == SCHEMAS_ROOT / "Structurizr" / "Demo-Product"
    )
    assert default_likec4_output_dir("Demo Product") == SCHEMAS_ROOT / "Likec4" / "Demo-Product"


def test_render_command_rejects_invalid_render_mode():
    with pytest.raises(SystemExit, match="--render must be one of"):
        render_command.render_outputs(Namespace(architecture_file="architecture.json", render="diagram"))


def test_render_command_can_render_likec4_only(monkeypatch):
    calls = []

    monkeypatch.setattr(
        render_command,
        "render_structurizr_architecture",
        lambda args: calls.append(("structurizr", args)) or 0,
    )
    monkeypatch.setattr(render_command, "render_likec4", lambda args: calls.append(("likec4", args)) or 0)

    rc = render_command.render_outputs(
        Namespace(
            architecture_file="architecture.json",
            render="likec4",
            likec4_output_dir="Likec4/demo",
            likec4_common_path="../shared",
        )
    )

    assert rc == 0
    assert [name for name, _ in calls] == ["likec4"]
    assert calls[0][1].output_dir == "Likec4/demo"
    assert calls[0][1].common_path == "../shared"


def test_render_command_stops_when_structurizr_fails(monkeypatch):
    calls = []

    monkeypatch.setattr(render_command, "architecture_product_name", lambda path: "demo")
    monkeypatch.setattr(render_command, "render_structurizr_architecture", lambda args: calls.append("struct") or 7)
    monkeypatch.setattr(render_command, "render_likec4", lambda args: calls.append("likec4") or 0)

    rc = render_command.render_outputs(
        Namespace(
            architecture_file="architecture.json",
            render="both",
            struct_output_dir="",
            likec4_output_dir="",
            likec4_common_path="../common",
        )
    )

    assert rc == 7
    assert calls == ["struct"]


def test_architecture_product_name_uses_workspace_fallback_and_rejects_empty_model(tmp_path):
    architecture_file = tmp_path / "architecture.json"
    architecture_file.write_text(json.dumps({"workspace": {"product": "workspace-demo"}}), encoding="utf-8")

    assert render_command.architecture_product_name(str(architecture_file)) == "workspace-demo"

    empty_file = tmp_path / "empty.json"
    empty_file.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="Invalid architecture model"):
        render_command.architecture_product_name(str(empty_file))
