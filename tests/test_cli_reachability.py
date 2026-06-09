from kmap.cli import build_parser


def test_all_cli_subcommands_dispatch_to_importable_callables():
    parser = build_parser()
    subparsers_action = next(action for action in parser._actions if action.dest == "command")

    assert subparsers_action.choices
    for command, subparser in subparsers_action.choices.items():
        defaults = getattr(subparser, "_defaults", {})
        func = defaults.get("func")
        assert callable(func), command
        assert func.__module__.startswith("kmap."), command
