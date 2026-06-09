from kmap.model.internal import (
    apply_project_element_type_override,
    apply_project_title_override,
    apply_single_system_project_overrides,
    internal_systems_by_project,
)


def test_apply_single_system_project_overrides_promotes_project_title_and_type():
    systems_by_id = {
        "sys.a": {
            "id": "sys.a",
            "kind": "internal",
            "project_id": "prj.a",
            "title": "Raw Service",
            "element_type": "component",
        }
    }
    projects_by_id = {"prj.a": {"id": "prj.a", "name": "demo", "title": "Demo Project"}}

    apply_single_system_project_overrides(
        systems_by_id,
        projects_by_id,
        {"demo": {"element_type": "Website"}},
    )

    assert systems_by_id["sys.a"]["title"] == "Demo Project"
    assert systems_by_id["sys.a"]["element_type"] == "Website"


def test_apply_single_system_project_overrides_ignores_multi_system_projects():
    systems_by_id = {
        "sys.a": {"id": "sys.a", "kind": "internal", "project_id": "prj.a", "title": "A"},
        "sys.b": {"id": "sys.b", "kind": "internal", "project_id": "prj.a", "title": "B"},
    }
    projects_by_id = {"prj.a": {"id": "prj.a", "name": "demo", "title": "Demo Project"}}

    apply_single_system_project_overrides(systems_by_id, projects_by_id, {})

    assert systems_by_id["sys.a"]["title"] == "A"
    assert systems_by_id["sys.b"]["title"] == "B"


def test_internal_systems_by_project_ignores_external_systems():
    grouped = internal_systems_by_project(
        {
            "sys.a": {"id": "sys.a", "kind": "internal", "project_id": "prj.a"},
            "ext.a": {"id": "ext.a", "kind": "external", "project_id": "prj.a"},
            "sys.orphan": {"id": "sys.orphan", "kind": "internal"},
        }
    )

    assert {project_id: [system["id"] for system in systems] for project_id, systems in grouped.items()} == {
        "prj.a": ["sys.a"],
        "": ["sys.orphan"],
    }


def test_project_overrides_ignore_empty_titles_and_internal_element_types():
    system = {"title": "Raw", "element_type": "component"}

    apply_project_title_override(system, {"title": ""})
    apply_project_element_type_override(system, {"name": "demo"}, {"demo": {"element_type": "component"}})

    assert system == {"title": "Raw", "element_type": "component"}
