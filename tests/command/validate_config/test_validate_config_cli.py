import argparse

from kmap.command.validate_config import validate_config
from kmap.command.validate_config.cli import add_validate_config_parser


def test_add_validate_config_parser_wires_config_file_and_function():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_validate_config_parser(subparsers)

    args = parser.parse_args(["validate-config", "config/example.minimum.yaml"])

    assert args.func is validate_config
    assert args.config_file == "config/example.minimum.yaml"
