import argparse

from kmap.command.render_inventory.cli import add_render_inventory_parser
from kmap.inventory.buckets import DEFAULT_BUCKET_REPORTS_DIR
from kmap.inventory.namespaces import DEFAULT_CONFIG_DIR, DEFAULT_INVENTORY_DIR, render_inventory
from kmap.paths import SCHEMAS_ROOT

DEFAULT_INVENTORY_EXEC_TIMEOUT = 5
CUSTOM_INVENTORY_EXEC_ATTEMPTS = 2
CUSTOM_INVENTORY_EXEC_TIMEOUT = 3


def test_add_render_inventory_parser_wires_defaults_and_function():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_render_inventory_parser(subparsers)

    args = parser.parse_args(["render-inventory"])

    assert args.command == "render-inventory"
    assert args.config_dir == str(DEFAULT_CONFIG_DIR)
    assert args.config_dir == str(SCHEMAS_ROOT / "config")
    assert args.bucket_artifacts_dir == str(DEFAULT_BUCKET_REPORTS_DIR)
    assert args.bucket_artifacts_dir == str(SCHEMAS_ROOT / "artifacts" / "buckets")
    assert args.output_dir == str(DEFAULT_INVENTORY_DIR)
    assert args.output_dir == str(SCHEMAS_ROOT / "Inventory")
    assert args.full is False
    assert args.cluster == ""
    assert args.fragment_id == ""
    assert args.kubectl == "kubectl"
    assert args.inventory_exec_timeout == DEFAULT_INVENTORY_EXEC_TIMEOUT
    assert args.inventory_exec_attempts == 1
    assert args.output == "progress"
    assert args.func is render_inventory

    args = parser.parse_args(
        [
            "render-inventory",
            "--config-dir",
            "cfg",
            "--bucket-artifacts-dir",
            "artifacts",
            "--output-dir",
            "Inventory",
            "--full",
            "--cluster",
            "prod-cluster",
            "--fragment-id",
            "team-a",
            "--no-exec",
            "--inventory-exec-timeout",
            "3",
            "--inventory-exec-attempts",
            "2",
            "--output",
            "lines",
        ]
    )

    assert args.config_dir == "cfg"
    assert args.bucket_artifacts_dir == "artifacts"
    assert args.output_dir == "Inventory"
    assert args.full is True
    assert args.cluster == "prod-cluster"
    assert args.fragment_id == "team-a"
    assert args.no_exec is True
    assert args.inventory_exec_timeout == CUSTOM_INVENTORY_EXEC_TIMEOUT
    assert args.inventory_exec_attempts == CUSTOM_INVENTORY_EXEC_ATTEMPTS
    assert args.output == "lines"
