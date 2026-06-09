from kmap.render.likec4.specification import generated_likec4_tag_names, render_likec4_specification


def test_render_likec4_specification_declares_config_tags():
    architecture = {
        "product": {"tags": ["demo", "External"]},
        "projects": [
            {"tags": ["Backend", "team one", ""]},
            {"tags": ["team one", "K8s"]},
        ],
    }

    assert generated_likec4_tag_names(architecture) == ["demo", "Backend", "team_one"]
    assert render_likec4_specification(architecture) == (
        "specification {\n"
        "  // Generated config tags by kmap. Do not edit manually.\n"
        "  tag demo\n"
        "  tag Backend\n"
        "  tag team_one\n"
        "}\n"
    )
