from kmap.render.structurizr.elements import (
    InternalSystemRenderContext,
    container_description,
    container_lines,
    container_technology,
    diagram_text,
    element_description,
    element_metadata_items,
    element_tags,
    internal_system_lines,
    internal_system_lines_from_context,
    project_property_lines,
    runtime_values,
    summary_values,
    system_lines,
    system_project_property_lines,
)


def test_diagram_text_and_element_description_normalize_literal_newlines():
    assert diagram_text("line 1\\nline 2") == "line 1\nline 2"
    assert element_description({"description": "explicit\\ntext"}, "fallback") == "explicit\ntext"
    assert element_description({}, "fallback") == "fallback"


def test_element_metadata_items_deduplicates_lists_and_skips_invalid_shapes():
    assert element_metadata_items(
        {
            "metadata": {
                "owner": "Payments",
                "tags": ["critical", "critical", "", "pci"],
                "blank": "",
            }
        }
    ) == [("owner", "Payments"), ("tags", "critical, pci")]
    assert element_metadata_items({"metadata": ["not", "a", "mapping"]}) == []


def test_element_tags_skips_blank_values():
    assert element_tags({"tags": ["public", "", "critical"]}) == "public,critical"


def test_runtime_values_and_container_technology_fallbacks():
    assert runtime_values({"runtime": {"workload_kinds": ["Deployment", None, ""]}}, "workload_kinds") == ["Deployment"]
    assert container_technology({"runtime": {"workload_kinds": ["Deployment", "StatefulSet"]}}) == (
        "Deployment, StatefulSet"
    )
    assert container_technology({"technology": "Go", "runtime": {"workload_kinds": ["Deployment"]}}) == "Go"
    assert container_technology({"kind": "sidecar"}) == "sidecar"
    assert container_technology({}) == "Container"


def test_summary_values_deduplicates_and_compacts_long_lists():
    assert summary_values(["api", "API", "", "worker"], "Workload", "Workloads") == "Workloads: api, worker"
    assert summary_values(["api"], "Workload", "Workloads") == "Workload: api"
    assert summary_values(["a", "b", "c", "d"], "Item", "Items") == "Items: 4 observed"
    assert summary_values([], "Item", "Items") == ""


def test_project_property_lines_emit_url_and_resource_properties():
    lines = project_property_lines(
        {
            "id": "prj.pay",
            "repo": "https://git.example/pay",
            "resources": {"runbook": 'https://docs.example/"quoted"'},
        },
        [],
    )

    assert lines[0] == "  url https://git.example/pay"
    assert '    "project_id" "prj.pay"' in lines
    assert '    "resource.repo" "https://git.example/pay"' in lines
    assert '    "resource.runbook" "https://docs.example/\\"quoted\\""' in lines


def test_system_project_property_lines_inserts_system_id():
    lines = system_project_property_lines({"id": "sys.pay"}, {"id": "prj.pay"}, [])

    assert lines[:3] == [
        "  properties {",
        '    "system_id" "sys.pay"',
        '    "project_id" "prj.pay"',
    ]


def test_container_description_prefers_explicit_and_summarizes_discovery():
    assert container_description({"description": "explicit\\ntext"}) == "explicit\ntext"
    assert (
        container_description(
            {
                "discovery": {
                    "namespaces": ["pay", "PAY", "audit"],
                    "workloads": ["api", "worker", "cron", "cleanup"],
                }
            },
            inbound_count=2,
        )
        == "Namespaces: pay, audit\nWorkloads: 4 observed\nUsed by: 2"
    )


def test_container_lines_render_tags_runtime_and_defaults():
    lines = container_lines(
        {
            "id": "ctr.pay.api",
            "title": "API",
            "tags": ["public"],
            "metadata": {"database": {"engine": "postgres", "names": ["pay"]}},
            "runtime": {"workload_kinds": ["Deployment"]},
        },
        refs={"ctr.pay.api": "ctr_pay_api"},
        inbound_counts={"ctr.pay.api": 3},
    )

    assert lines[0] == '  ctr_pay_api = container "API" "Used by: 3" "Deployment" {'
    assert '    tags "public"' in lines
    assert '      "database_engine" "postgres"' in lines
    assert '      "databases" "pay"' in lines


def test_system_lines_render_external_fallback_metadata_and_containers():
    lines = system_lines(
        {
            "id": "ext.search",
            "title": "Search",
            "tags": ["External"],
            "metadata": {"owner": "Search Team"},
        },
        [{"id": "ctr.ext.search", "title": "Endpoint"}],
        refs={"ext.search": "ext_search", "ctr.ext.search": "ctr_ext_search"},
        inbound_counts={},
    )

    assert lines[0] == 'ext_search = softwareSystem "Search" "External dependency" {'
    assert '  tags "External"' in lines
    assert '    "owner" "Search Team"' in lines
    assert '  ctr_ext_search = container "Endpoint" "" "Container" {' in lines


def test_internal_system_lines_render_product_project_title_and_properties():
    lines = internal_system_lines(
        {"id": "sys.pay.api", "title": "API"},
        {"id": "prj.pay", "name": "pay", "title": "Pay"},
        [{"id": "ctr.pay.api", "title": "API"}],
        refs={"sys.pay.api": "sys_pay_api", "ctr.pay.api": "ctr_pay_api"},
        architecture={"product": {"name": "Demo"}},
        inbound_counts={},
    )

    assert lines[0] == 'sys_pay_api = softwareSystem "Demo / Pay / API" "Product scope" {'
    assert '    "system_id" "sys.pay.api"' in lines
    assert '    "project_id" "prj.pay"' in lines
    assert '  ctr_pay_api = container "API" "" "Container" {' in lines


def test_internal_system_lines_from_context_matches_wrapper_output():
    context = InternalSystemRenderContext(
        system={"id": "sys.pay.api", "title": "API"},
        project={"id": "prj.pay", "name": "pay", "title": "Pay"},
        containers=[{"id": "ctr.pay.api", "title": "API"}],
        refs={"sys.pay.api": "sys_pay_api", "ctr.pay.api": "ctr_pay_api"},
        architecture={"product": {"name": "Demo"}},
        inbound_counts={},
    )

    assert internal_system_lines_from_context(context) == internal_system_lines(
        context.system,
        context.project,
        context.containers,
        context.refs,
        architecture=context.architecture,
        inbound_counts=context.inbound_counts,
    )
