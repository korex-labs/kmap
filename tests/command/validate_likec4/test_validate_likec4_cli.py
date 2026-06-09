import argparse

from kmap.command.validate_likec4 import validate_likec4
from kmap.command.validate_likec4.cli import add_validate_likec4_parser


def test_add_validate_likec4_parser_wires_options_and_function():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_validate_likec4_parser(subparsers)

    args = parser.parse_args(
        [
            "validate-likec4",
            "--root",
            "Likec4",
            "--product",
            "demo",
            "--image",
            "likec4/test",
            "--include-multi-project",
        ]
    )

    assert args.command == "validate-likec4"
    assert args.root == "Likec4"
    assert args.product == ["demo"]
    assert args.image == "likec4/test"
    assert args.include_multi_project is True
    assert args.func is validate_likec4
