from pathlib import Path

import pytest

from kmap import io as io_module
from kmap.io import (
    dump_json,
    ensure_dir,
    load_json_file,
    load_required_json_file,
    load_required_yaml_file,
    load_yaml_config_or_error,
    load_yaml_file,
    read_yaml_file,
    safe_json_loads,
    write_text_atomic,
)


def test_io_helpers_round_trip_json_and_yaml(tmp_path):
    json_path = tmp_path / "data.json"
    yaml_path = tmp_path / "config.yaml"

    dump_json(json_path, {"name": "demo"})
    yaml_path.write_text("product: demo\n", encoding="utf-8")

    assert load_json_file(json_path, {}) == {"name": "demo"}
    assert load_required_json_file(json_path) == {"name": "demo"}
    assert load_yaml_file(yaml_path, {}) == {"product": "demo"}
    assert read_yaml_file(yaml_path) == {"product": "demo"}
    assert load_yaml_config_or_error(yaml_path) == {"product": "demo"}
    assert safe_json_loads('{"ok": true}', {}) == {"ok": True}
    assert safe_json_loads("{bad", {"fallback": True}) == {"fallback": True}


def test_required_loaders_fail_loudly_on_malformed_files(tmp_path):
    json_path = tmp_path / "bad.json"
    yaml_path = tmp_path / "bad.yaml"
    json_path.write_text("{bad", encoding="utf-8")
    yaml_path.write_text(":\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="Invalid JSON file"):
        load_required_json_file(json_path)
    with pytest.raises(SystemExit, match="Invalid YAML file"):
        load_required_yaml_file(yaml_path)


def test_io_helpers_return_defaults_for_optional_loader_failures(tmp_path):
    missing_json = tmp_path / "missing.json"
    bad_yaml = tmp_path / "bad.yaml"
    empty_yaml = tmp_path / "empty.yaml"
    bad_yaml.write_text(":\n", encoding="utf-8")
    empty_yaml.write_text("", encoding="utf-8")

    assert load_json_file(missing_json, {"fallback": True}) == {"fallback": True}
    assert load_yaml_file(bad_yaml, {"fallback": True}) == {"fallback": True}
    assert load_yaml_file(empty_yaml, {"fallback": True}) == {"fallback": True}


def test_optional_loaders_do_not_swallow_unexpected_errors(monkeypatch):
    def fail_json_loads(raw):
        raise RuntimeError("bug")

    def fail_read_yaml_file(path):
        raise RuntimeError("bug")

    monkeypatch.setattr(io_module.json, "loads", fail_json_loads)
    monkeypatch.setattr(io_module, "read_yaml_file", fail_read_yaml_file)

    with pytest.raises(RuntimeError, match="bug"):
        safe_json_loads("{}", {})
    with pytest.raises(RuntimeError, match="bug"):
        load_yaml_file(Path("config.yaml"), {})


def test_required_yaml_loader_handles_empty_and_non_mapping_files(tmp_path):
    empty_yaml = tmp_path / "empty.yaml"
    list_yaml = tmp_path / "list.yaml"
    empty_yaml.write_text("", encoding="utf-8")
    list_yaml.write_text("- item\n", encoding="utf-8")

    assert load_required_yaml_file(empty_yaml) == {}
    with pytest.raises(SystemExit, match="Invalid YAML file format"):
        load_required_yaml_file(list_yaml)


def test_load_yaml_config_or_error_uses_config_wording(tmp_path):
    bad_yaml = tmp_path / "bad.yaml"
    list_yaml = tmp_path / "list.yaml"
    bad_yaml.write_text(":\n", encoding="utf-8")
    list_yaml.write_text("- item\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="Invalid config file:"):
        load_yaml_config_or_error(bad_yaml)
    with pytest.raises(SystemExit, match="Invalid config file format:"):
        load_yaml_config_or_error(list_yaml)


def test_ensure_dir_creates_nested_directories(tmp_path):
    nested = tmp_path / "one" / "two"

    ensure_dir(nested)

    assert nested.is_dir()


def test_write_text_atomic_preserves_existing_file_when_replace_is_interrupted(monkeypatch, tmp_path):
    target = tmp_path / "report.txt"
    target.write_text("old\n", encoding="utf-8")

    def interrupt_replace(source, destination):
        raise KeyboardInterrupt

    monkeypatch.setattr("kmap.io.os.replace", interrupt_replace)

    with pytest.raises(KeyboardInterrupt):
        write_text_atomic(target, "new\n")

    assert target.read_text(encoding="utf-8") == "old\n"
    assert list(tmp_path.glob(".report.txt.*.tmp")) == []
