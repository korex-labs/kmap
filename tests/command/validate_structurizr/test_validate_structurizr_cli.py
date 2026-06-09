from kmap.cli import build_parser


def test_validate_structurizr_parser_registers_command():
    args = build_parser().parse_args(["validate-structurizr", "--root", "Structurizr", "--product", "demo"])

    assert args.root == "Structurizr"
    assert args.product == ["demo"]
    assert callable(args.func)
