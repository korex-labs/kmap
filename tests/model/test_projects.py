from kmap.model.projects import (
    namespace_metadata_from_project_meta,
    project_entry,
    record_project_namespace_discovery,
)


def test_project_entry_prefers_product_owner_and_project_title():
    project = project_entry(
        project_id="prj.demo",
        product_id="prod.demo",
        project_name="demo-project",
        product_metadata={"owner_team": "Platform", "tags": ["Product"]},
        project_meta={
            "title": "Demo",
            "owner_team": "Local",
            "domain_team": "Payments",
            "resources": {"runbook": "https://example.test"},
            "tags": ["Critical", "Product"],
        },
    )

    assert project["title"] == "Demo"
    assert project["owner_team"] == "Platform"
    assert project["domain_team"] == "Payments"
    assert project["resources"] == {"runbook": "https://example.test"}
    assert project["tags"] == ["Product", "Critical"]


def test_project_entry_uses_project_owner_and_humanized_title_fallbacks():
    project = project_entry(
        project_id="prj.demo",
        product_id="prod.demo",
        project_name="demo-project",
        product_metadata={},
        project_meta={"owner_team": "Local"},
    )

    assert project["title"] == "Demo Project"
    assert project["owner_team"] == "Local"


def test_record_project_namespace_discovery_keeps_metadata_and_context():
    project = project_entry(
        project_id="prj.demo",
        product_id="prod.demo",
        project_name="demo-project",
        product_metadata={},
        project_meta={},
    )

    record_project_namespace_discovery(
        project,
        namespace="demo-prod",
        cluster="cluster-a",
        project_meta={"title": "Demo", "domain_team": "Payments", "repo": "ignored"},
        report_discovery={"context": "prod-context"},
    )

    assert project["discovery"]["namespaces"] == ["demo-prod"]
    assert project["discovery"]["namespace_metadata"]["demo-prod"] == {
        "title": "Demo",
        "domain_team": "Payments",
        "cluster": "cluster-a",
        "context": "prod-context",
    }


def test_record_project_namespace_discovery_ignores_empty_namespace():
    project = {"discovery": {"namespaces": []}}

    record_project_namespace_discovery(
        project,
        namespace="",
        cluster="cluster-a",
        project_meta={"title": "Demo"},
        report_discovery={"context": "prod-context"},
    )

    assert project == {"discovery": {"namespaces": []}}


def test_namespace_metadata_from_project_meta_keeps_supported_fields_only():
    assert namespace_metadata_from_project_meta(
        {
            "title": "Demo",
            "domain_team": "Payments",
            "description": "Payment services",
            "tags": ["Critical"],
            "resources": {"runbook": "https://example.test"},
            "repo": "ignored",
        }
    ) == {
        "title": "Demo",
        "domain_team": "Payments",
        "description": "Payment services",
        "tags": ["Critical"],
        "resources": {"runbook": "https://example.test"},
    }
