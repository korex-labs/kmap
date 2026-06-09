import json

from kmap.command.validate_structurizr import _validate_include_targets, validate_structurizr


def _args(root, *products):
    return type("Args", (), {"root": str(root), "product": list(products)})()


def _write_common_workspace(root):
    (root / "common").mkdir(parents=True)
    (root / "common" / "workspace.dsl").write_text("workspace {}\n", encoding="utf-8")


def _write_workspace(product, lines=None):
    (product / "model").mkdir(parents=True, exist_ok=True)
    (product / "workspace.dsl").write_text(
        "\n".join(
            lines
            or [
                "workspace extends ../common/workspace.dsl {",
                "  model {",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )


def test_validate_structurizr_accepts_generated_workspace(tmp_path):
    root = tmp_path / "Structurizr"
    product = root / "demo"
    _write_common_workspace(root)
    for folder in ("model/projects", "model/external", "model/relations", "deployment", "view"):
        (product / folder).mkdir(parents=True, exist_ok=True)
        (product / folder / "generated.dsl").write_text("// generated\n", encoding="utf-8")
    (product / "model" / ".kmap-generated.json").write_text(
        json.dumps({"generator": "kmap", "files": ["model/projects/generated.dsl", "deployment/generated.dsl"]}),
        encoding="utf-8",
    )
    (product / "workspace.dsl").write_text(
        "\n".join(
            [
                "workspace extends ../common/workspace.dsl {",
                "  model {",
                "    !include model/projects/",
                "    !include model/external/",
                "    !include model/relations/",
                "    !include deployment/",
                "  }",
                "  views {",
                "    !include view/",
                "  }",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    assert validate_structurizr(_args(root, "demo")) == 0


def test_validate_structurizr_reports_missing_manifest_file(tmp_path):
    root = tmp_path / "Structurizr"
    product = root / "demo"
    _write_common_workspace(root)
    _write_workspace(product)
    (product / "model" / ".kmap-generated.json").write_text(
        json.dumps({"generator": "kmap", "files": ["model/projects/missing.dsl"]}),
        encoding="utf-8",
    )

    assert validate_structurizr(_args(root, "demo")) == 1


def test_validate_structurizr_reports_missing_workspace(tmp_path):
    root = tmp_path / "Structurizr"
    product = root / "demo"
    _write_common_workspace(root)
    (product / "model").mkdir(parents=True)
    (product / "model" / ".kmap-generated.json").write_text(
        json.dumps({"generator": "kmap", "files": []}),
        encoding="utf-8",
    )

    assert validate_structurizr(_args(root, "demo")) == 1


def test_validate_structurizr_reports_invalid_manifest_json(tmp_path):
    root = tmp_path / "Structurizr"
    product = root / "demo"
    _write_common_workspace(root)
    _write_workspace(product)
    (product / "model" / ".kmap-generated.json").write_text("{not-json", encoding="utf-8")

    assert validate_structurizr(_args(root, "demo")) == 1


def test_validate_structurizr_reports_workspace_contract_errors(tmp_path):
    root = tmp_path / "Structurizr"
    product = root / "demo"
    (product / "model" / "empty").mkdir(parents=True)
    (product / "model" / ".kmap-generated.json").write_text(
        json.dumps({"generator": "kmap", "files": []}),
        encoding="utf-8",
    )
    _write_workspace(
        product,
        [
            "workspace {",
            "  model {",
            "    !include model/missing.dsl",
            "    !include model/empty/",
            "  }",
            "}",
        ],
    )

    assert validate_structurizr(_args(root, "demo")) == 1


def test_validate_include_targets_reports_missing_and_empty_includes(tmp_path):
    product = tmp_path / "demo"
    empty_dir = product / "model" / "empty"
    empty_dir.mkdir(parents=True)
    workspace_file = product / "workspace.dsl"
    workspace_file.write_text(
        "\n".join(
            [
                "workspace extends ../common/workspace.dsl {",
                "  !include model/missing.dsl",
                "  !include model/empty/",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    assert _validate_include_targets(workspace_file) == [
        f"missing include target: {product / 'model' / 'missing.dsl'}",
        f"included directory has no .dsl files: {empty_dir}",
    ]


def test_validate_structurizr_discovers_generated_workspaces_and_ignores_empty_root(tmp_path):
    root = tmp_path / "Structurizr"

    assert validate_structurizr(_args(root)) == 0

    product = root / "demo"
    _write_common_workspace(root)
    _write_workspace(product)
    (product / "model" / ".kmap-generated.json").write_text(
        json.dumps({"generator": "kmap", "files": []}),
        encoding="utf-8",
    )

    assert validate_structurizr(_args(root)) == 0
