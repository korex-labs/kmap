import argparse

from kmap.command.render import render_outputs
from kmap.command.render.cli import add_render_parser


def test_add_render_parser_wires_renderer_options_and_function():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_render_parser(subparsers, default_architecture_file=".tmp/reports/architecture.json")

    args = parser.parse_args(
        [
            "render",
            "architecture.json",
            "--render",
            "likec4",
            "--likec4-output-dir",
            "Likec4/demo",
            "--struct-output-dir",
            "Structurizr/demo",
        ]
    )

    assert args.func is render_outputs
    assert args.architecture_file == "architecture.json"
    assert args.render == "likec4"
    assert args.likec4_output_dir == "Likec4/demo"
    assert args.struct_output_dir == "Structurizr/demo"
