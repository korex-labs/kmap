from argparse import Namespace

from kmap.command.run_all.paths import (
    DEFAULT_ARCHITECTURE_FILE,
    DEFAULT_DEPENDENCIES_FILE,
    DEFAULT_REPORTS_DIR,
    apply_default_output_paths,
)


def test_apply_default_output_paths_uses_namespace_dir_for_single_namespace(monkeypatch):
    monkeypatch.delenv("OUT_DIR", raising=False)
    monkeypatch.delenv("OUTPUT_FILE", raising=False)
    monkeypatch.delenv("JSON_OUTPUT_FILE", raising=False)
    args = Namespace(
        product="demo",
        out_dir=DEFAULT_REPORTS_DIR,
        dependencies_file=DEFAULT_DEPENDENCIES_FILE,
        dependencies_json_output_file=None,
        architecture_output_file=DEFAULT_ARCHITECTURE_FILE,
    )

    apply_default_output_paths(args, ["payments"])

    assert args.out_dir.endswith("/.tmp/payments")
    assert args.dependencies_file.endswith("/.tmp/payments/dependencies.list")
    assert args.dependencies_json_output_file.endswith("/.tmp/payments/dependencies.json")
    assert args.architecture_output_file.endswith("/.tmp/payments/architecture.json")


def test_apply_default_output_paths_uses_product_multi_dir_for_multiple_namespaces(monkeypatch):
    monkeypatch.delenv("OUT_DIR", raising=False)
    monkeypatch.delenv("OUTPUT_FILE", raising=False)
    monkeypatch.delenv("JSON_OUTPUT_FILE", raising=False)
    args = Namespace(
        product="Demo Product",
        out_dir=DEFAULT_REPORTS_DIR,
        dependencies_file=DEFAULT_DEPENDENCIES_FILE,
        dependencies_json_output_file=None,
        architecture_output_file=DEFAULT_ARCHITECTURE_FILE,
    )

    apply_default_output_paths(args, ["api", "worker"])

    assert args.out_dir.endswith("/.tmp/Demo-Product-multi")


def test_apply_default_output_paths_preserves_explicit_paths(monkeypatch):
    monkeypatch.delenv("OUT_DIR", raising=False)
    monkeypatch.delenv("OUTPUT_FILE", raising=False)
    monkeypatch.delenv("JSON_OUTPUT_FILE", raising=False)
    args = Namespace(
        product="demo",
        out_dir="/tmp/custom",
        dependencies_file="/tmp/custom/deps.list",
        dependencies_json_output_file="/tmp/custom/deps.json",
        architecture_output_file="/tmp/custom/arch.json",
    )

    apply_default_output_paths(args, ["api"])

    assert args.out_dir == "/tmp/custom"
    assert args.dependencies_file == "/tmp/custom/deps.list"
    assert args.dependencies_json_output_file == "/tmp/custom/deps.json"
    assert args.architecture_output_file == "/tmp/custom/arch.json"
