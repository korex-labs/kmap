import json

from kmap.render.likec4.config import likec4_write_config


def test_likec4_write_config_preserves_existing_title_when_product_title_is_generic(tmp_path):
    output_dir = tmp_path / "likec4"
    output_dir.mkdir()
    (output_dir / "likec4.config.json").write_text(
        json.dumps({"title": "Existing Title", "metadata": {"owner": "Team", "domain": "Payments"}}),
        encoding="utf-8",
    )

    likec4_write_config(
        output_dir,
        {
            "workspace": {
                "generator": {"tool": "kmap", "version": "0.1.0", "rules_file": "GENERATION_RULES.md"},
            },
            "product": {"name": "demo", "title": "demo"},
        },
        common_path="../shared",
    )

    data = json.loads((output_dir / "likec4.config.json").read_text(encoding="utf-8"))
    assert data["title"] == "Existing Title"
    assert data["metadata"]["owner"] == "Team"
    assert data["include"]["paths"] == ["../shared"]


def test_likec4_write_config_handles_invalid_existing_config_and_product_metadata(tmp_path):
    output_dir = tmp_path / "likec4"
    output_dir.mkdir()
    (output_dir / "likec4.config.json").write_text(json.dumps(["bad"]), encoding="utf-8")

    likec4_write_config(
        output_dir,
        {
            "workspace": {"source": {"config_file": "config/demo.yaml"}},
            "product": {
                "name": "demo",
                "title": "Demo Docs",
                "owner_team": "Platform",
                "domain": "Commerce",
            },
        },
        common_path="../common-model",
    )

    data = json.loads((output_dir / "likec4.config.json").read_text(encoding="utf-8"))
    assert data["name"] == "demo"
    assert data["title"] == "Demo Docs"
    assert data["metadata"]["owner"] == "Platform"
    assert data["metadata"]["domain"] == "Commerce"
    assert data["metadata"]["generatedBy"] == "kmap"
    assert data["include"]["paths"] == ["../common-model"]

    (output_dir / "likec4.config.json").write_text(
        json.dumps({"title": "Existing", "metadata": "bad"}),
        encoding="utf-8",
    )
    likec4_write_config(output_dir, {"product": {"name": "demo"}})

    data = json.loads((output_dir / "likec4.config.json").read_text(encoding="utf-8"))
    assert data["title"] == "Existing"
    assert data["metadata"]["owner"] == ""
    assert data["metadata"]["domain"] == ""
