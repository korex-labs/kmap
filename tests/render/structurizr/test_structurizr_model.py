from kmap.render.structurizr.model import (
    render_structurizr_model,
    render_structurizr_model_files,
    structurizr_alias,
    structurizr_external_alias,
    structurizr_external_container_alias,
    structurizr_reference_map,
    structurizr_system_alias,
)


def test_structurizr_model_facade_reexports_public_api():
    assert callable(render_structurizr_model)
    assert callable(render_structurizr_model_files)
    assert structurizr_alias("sys.demo-api") == "sys_demo_api"
    assert structurizr_system_alias({"id": "sys.pay"}) == "sys_pay"
    assert structurizr_external_alias({"title": "Search"}, {"product": {"name": "shop"}}) == (
        "ext_org_shop_external_Search"
    )
    assert structurizr_external_container_alias({"title": "Search"}, {"product": {"name": "shop"}}) == (
        "extc_org_shop_external_Search"
    )
    assert structurizr_reference_map({}) == {}
