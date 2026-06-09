from kmap.command.normalize import normalize_architecture as command_normalize_architecture
from kmap.model.core import normalize_architecture
from kmap.model.inventory import architecture_container_inventory
from kmap.model.metadata import generator_metadata
from kmap.model.workloads import APP_SERVICE_ANNOTATION
from kmap.version import __version__


def test_generator_metadata_normalizes_source_context():
    assert APP_SERVICE_ANNOTATION == "app_service"
    assert generator_metadata(" config.yaml ", " likec4 ") == {
        "tool": "kmap",
        "version": __version__,
        "rules_file": "GENERATION_RULES.md",
        "config_file": "config.yaml",
        "renderer": "likec4",
    }


def test_architecture_container_inventory_falls_back_to_workload_name():
    assert architecture_container_inventory({"service_name": "api"}) == [{"name": "api", "kind": "workload"}]


def test_normalize_architecture_writes_builder_output(monkeypatch, tmp_path):
    import kmap.model as model_module

    monkeypatch.setattr(
        model_module,
        "architecture_model_from_reports",
        lambda args: {"schema_version": "test"},
    )
    output_file = tmp_path / "reports" / "architecture.json"

    rc = normalize_architecture(type("Args", (), {"output_file": str(output_file)})())

    assert rc == 0
    assert output_file.read_text(encoding="utf-8") == '{\n  "schema_version": "test"\n}\n'


def test_normalize_command_uses_model_compatibility_entrypoint():
    assert command_normalize_architecture is normalize_architecture


def test_package_version_falls_back_for_source_checkout(monkeypatch):
    import kmap.version as version_module

    monkeypatch.setattr(
        version_module, "version", lambda _name: (_ for _ in ()).throw(version_module.PackageNotFoundError)
    )

    assert version_module.package_version() == version_module.SOURCE_VERSION
