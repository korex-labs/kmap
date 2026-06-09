import argparse

from kmap.command.view import view_product
from kmap.command.view.cli import add_view_parser


def test_add_view_parser_wires_viewer_options_and_function():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_view_parser(subparsers)

    args = parser.parse_args(
        [
            "view",
            "demo",
            "--restart",
            "--no-structurizr",
            "--likec4-port",
            "5174",
        ]
    )

    assert args.func is view_product
    assert args.product == "demo"
    assert args.restart is True
    assert args.no_structurizr is True
    assert args.likec4_port == "5174"
    assert args.likec4_image is None
