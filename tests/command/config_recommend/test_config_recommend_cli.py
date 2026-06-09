import argparse

from kmap.command.config_recommend import config_recommend
from kmap.command.config_recommend.cli import add_config_recommend_parser


def test_add_config_recommend_parser_wires_command():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_config_recommend_parser(subparsers)

    args = parser.parse_args(["recommend-config", "config/demo.yaml"])

    assert args.command == "recommend-config"
    assert args.config_file == "config/demo.yaml"
    assert not args.include_low
    assert args.func is config_recommend

    args = parser.parse_args(["recommend-config", "config/demo.yaml", "--include-low"])

    assert args.include_low
