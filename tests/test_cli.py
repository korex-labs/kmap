from argparse import Namespace

import pytest

from kmap import cli

KEYBOARD_INTERRUPT_EXIT_CODE = 130


def parser_factory():
    return Parser()


class Parser:
    def parse_args(self, argv):
        return Namespace(func=lambda args: (_ for _ in ()).throw(KeyboardInterrupt))


def test_main_handles_keyboard_interrupt_without_traceback(monkeypatch, capsys):
    monkeypatch.setattr(cli, "build_parser", parser_factory)
    monkeypatch.setattr(cli, "apply_tool_config_overrides", lambda args: args)
    monkeypatch.setattr(cli, "apply_config_overrides", lambda args: args)

    assert cli.main(["run-all"]) == KEYBOARD_INTERRUPT_EXIT_CODE

    captured = capsys.readouterr()
    assert "interrupted" in captured.err
    assert "Traceback" not in captured.err


def test_numeric_parser_helpers_reject_invalid_values():
    with pytest.raises(cli.argparse.ArgumentTypeError, match="expected a non-negative number"):
        cli.parse_non_negative_float("-1")
    with pytest.raises(cli.argparse.ArgumentTypeError, match="expected a positive integer"):
        cli.parse_positive_int("bad")
