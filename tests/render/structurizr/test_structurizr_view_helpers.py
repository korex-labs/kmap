from kmap.render.structurizr.view_helpers import (
    connected_element_ids,
    connected_system_ids,
    containers_by_system,
    deployment_view_key,
    internal_project_views,
    internal_systems,
    project_view_connection_ids,
    system_project_ids,
    view_key,
)


def test_view_keys_are_stable_and_use_defaults():
    assert view_key("system_context", "sys.demo-api") == "system_context_sys_demo_api"
    assert view_key("containers", "") == "containers_view"
    assert deployment_view_key("shop", "prod") == "deployment_shop_prod"


def test_internal_project_views_group_systems_and_fill_missing_project_titles():
    architecture = {
        "projects": [{"id": "prj.api", "title": "API"}],
        "systems": [
            {"id": "sys.api", "project_id": "prj.api"},
            {"id": "sys.worker", "project_id": "prj.api"},
            {"id": "sys.legacy", "project_id": "legacy-project"},
            {"id": "ext.search"},
        ],
    }

    assert internal_systems(architecture) == architecture["systems"][:3]
    assert internal_project_views(architecture) == [
        {"id": "prj.api", "title": "API", "system_ids": ["sys.api", "sys.worker"]},
        {"id": "legacy-project", "title": "legacy-project", "system_ids": ["sys.legacy"]},
    ]


def test_connection_helpers_normalize_containers_to_systems_and_skip_self_edges():
    containers_by_id = {
        "ctr.api": {"id": "ctr.api", "system_id": "sys.api"},
        "ctr.worker": {"id": "ctr.worker", "system_id": "sys.api"},
        "ctr.search": {"id": "ctr.search", "system_id": "ext.search"},
    }
    relationships = [
        {"source_id": "ctr.api", "target_id": "ctr.worker"},
        {"source_id": "ctr.api", "target_id": "ctr.search"},
        {"source_id": "ext.queue", "target_id": "ctr.api"},
        {"source_id": "ctr.api", "target_id": ""},
    ]

    assert connected_system_ids("sys.api", {"ctr.api", "ctr.worker"}, containers_by_id, relationships) == {
        "ext.queue",
        "ext.search",
    }
    assert connected_element_ids("sys.api", {"ctr.api", "ctr.worker"}, containers_by_id, relationships) == {
        "ctr.search",
        "ext.queue",
    }
    assert project_view_connection_ids(["sys.api"], {"ctr.api", "ctr.worker"}, containers_by_id, relationships) == (
        {"ext.queue", "ext.search"},
        {"ctr.search", "ext.queue"},
    )


def test_grouping_helpers_index_containers_and_system_project_ids():
    containers = [{"id": "ctr.api", "system_id": "sys.api"}, {"id": "ctr.detached"}]
    systems = [{"id": "sys.api", "project_id": "prj.api"}, {"id": "ext.search"}]

    assert containers_by_system(containers) == {"sys.api": [containers[0]], "": [containers[1]]}
    assert system_project_ids(systems) == {"sys.api": "prj.api", "ext.search": ""}
