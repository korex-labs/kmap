from kmap.render.structurizr import structurizr_properties_lines


def test_structurizr_properties_quote_reserved_like_keys():
    lines = structurizr_properties_lines(
        [
            ("source", "api"),
            ("storage", "configMap"),
            ("target", "db"),
        ],
        indent="  ",
    )

    assert lines == [
        "  properties {",
        '    "source" "api"',
        '    "storage" "configMap"',
        '    "target" "db"',
        "  }",
    ]
