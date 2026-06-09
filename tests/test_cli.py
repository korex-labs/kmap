from argparse import Namespace

from kmap import cli

KEYBOARD_INTERRUPT_EXIT_CODE = 130


def test_main_handles_keyboard_interrupt_without_traceback(monkeypatch, capsys):
    class Parser:
        def parse_args(self, argv):
            return Namespace(func=lambda args: (_ for _ in ()).throw(KeyboardInterrupt))

    monkeypatch.setattr(cli, "build_parser", lambda: Parser())
    monkeypatch.setattr(cli, "apply_tool_config_overrides", lambda args: args)
    monkeypatch.setattr(cli, "apply_config_overrides", lambda args: args)

    assert cli.main(["run-all"]) == KEYBOARD_INTERRUPT_EXIT_CODE

    captured = capsys.readouterr()
    assert "interrupted" in captured.err
    assert "Traceback" not in captured.err
