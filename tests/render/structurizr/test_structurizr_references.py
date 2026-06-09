from kmap.render.structurizr.references import (
    containers_grouped_by_system,
    has_external_endpoint_containers,
    is_external_endpoint,
    register_container_reference,
    register_system_reference,
    structurizr_alias,
    structurizr_external_alias,
    structurizr_external_container_alias,
    structurizr_reference_map,
    structurizr_system_alias,
    workspace_names,
)


def test_structurizr_aliases_are_stable():
    assert structurizr_alias("sys.demo-api") == "sys_demo_api"
    assert structurizr_alias("123") == "_123"
    assert structurizr_system_alias({"id": "sys.pay"}) == "sys_pay"
    assert structurizr_system_alias({"name": "pay"}) == "pay"
    assert structurizr_system_alias({}) == "system"


def test_workspace_names_use_defaults_and_product_fallbacks():
    assert workspace_names({}) == ("org", "product")
    assert workspace_names({"workspace": {"org": "acme", "product": "legacy"}}) == ("acme", "legacy")
    assert workspace_names({"workspace": {"org": "acme"}, "product": {"name": "shop"}}) == ("acme", "shop")


def test_external_aliases_use_mapped_prefix_when_system_has_endpoint_containers():
    architecture = {"workspace": {"org": "acme"}, "product": {"name": "shop"}}
    system = {"id": "ext.search", "title": "Search"}

    assert structurizr_external_alias(system, architecture) == "ext_acme_shop_external_Search"
    assert structurizr_external_alias(system, architecture, {"ext.search": [{"id": "ctr.ext.search"}]}) == (
        "extsys_acme_shop_external_mapped_Search"
    )
    assert structurizr_external_container_alias({"name": "search-api"}, architecture) == (
        "extc_acme_shop_external_search_api"
    )


def test_external_endpoint_helpers_detect_missing_project_systems():
    systems_by_id = {
        "sys.api": {"project_id": "prj.api"},
        "ext.search": {},
    }

    assert is_external_endpoint({"system_id": "ext.search"}, systems_by_id)
    assert not is_external_endpoint({"system_id": "sys.api"}, systems_by_id)
    assert has_external_endpoint_containers({"id": "ext.search"}, {"ext.search": [{"id": "ctr.ext.search"}]})
    assert not has_external_endpoint_containers({"id": "ext.search"}, {})


def test_structurizr_reference_registration_helpers_skip_missing_ids():
    architecture = {"workspace": {"org": "acme"}, "product": {"name": "shop"}}
    refs = {}

    assert containers_grouped_by_system([{"id": "ctr.api", "system_id": "sys.api"}]) == {
        "sys.api": [{"id": "ctr.api", "system_id": "sys.api"}]
    }
    register_system_reference(refs, {}, architecture, {})
    register_container_reference(refs, {}, architecture, {})

    assert refs == {}


def test_structurizr_reference_map_covers_internal_external_and_endpoint_containers():
    architecture = {
        "workspace": {"org": "acme"},
        "product": {"name": "shop"},
        "projects": [{"id": "prj.api", "name": "api"}],
        "systems": [
            {"id": "sys.api", "project_id": "prj.api", "title": "API"},
            {"id": "sys.legacy", "project_id": "missing-project", "title": "Legacy"},
            {"id": "ext.search", "title": "Search"},
        ],
        "containers": [
            {"id": "ctr.api", "system_id": "sys.api", "title": "API"},
            {"id": "ctr.legacy", "system_id": "sys.legacy", "title": "Legacy"},
            {"id": "ctr.ext.search", "system_id": "ext.search", "title": "Search Endpoint"},
        ],
    }

    assert structurizr_reference_map(architecture) == {
        "sys.api": "sys_api",
        "sys.legacy": "sys_legacy",
        "ext.search": "extsys_acme_shop_external_mapped_Search",
        "ctr.api": "ctr_api",
        "ctr.legacy": "ctr_legacy",
        "ctr.ext.search": "extc_acme_shop_external_Search_Endpoint",
    }
