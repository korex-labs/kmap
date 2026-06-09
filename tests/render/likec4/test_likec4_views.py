from kmap.render.likec4.views import (
    application_likec4_systems,
    internal_likec4_systems,
    internal_system_title_counts,
    major_external_system_refs,
    platform_likec4_systems,
    relationship_stats_by_system_id,
    render_likec4_views,
)
from kmap.render.likec4.views_dependencies import (
    external_category_lines,
    major_external_lines,
    major_external_source_systems,
)


def test_likec4_view_context_selection_helpers_group_systems_and_stats():
    architecture = {
        "systems": [
            {"id": "sys.pay", "name": "pay", "title": "Worker", "category": "App"},
            {"id": "sys.ops", "name": "ops", "title": "Worker", "category": "Gateway"},
            {"id": "sys.kafka", "name": "kafka", "title": "Kafka", "category": "Messaging"},
            {"id": "sys.logs", "name": "logs", "title": "Logs", "category": "Monitoring"},
            {"id": "ext.partner", "tags": ["External"], "category": "API"},
        ],
        "relationship_statistics": {
            "systems": [
                {"system_id": "ext.partner", "incoming_distinct_source_system_count": 3},
                {"system_id": "ext.minor", "incoming_relationship_count": 1},
            ]
        },
    }

    internal = internal_likec4_systems(architecture["systems"])
    stats_by_system = relationship_stats_by_system_id(architecture)

    assert [system["id"] for system in internal] == ["sys.pay", "sys.ops", "sys.kafka", "sys.logs"]
    assert internal_system_title_counts(internal)["Worker"] == 2
    assert [system["id"] for system in application_likec4_systems(internal)] == ["sys.pay", "sys.ops"]
    assert [system["id"] for system in platform_likec4_systems(internal)] == ["sys.kafka", "sys.logs"]
    assert set(stats_by_system) == {"ext.partner", "ext.minor"}
    assert major_external_system_refs({"ext.partner", "ext.minor"}, stats_by_system) == {"ext.partner"}


def test_render_likec4_views_include_landscape_hotspots_and_deployment():
    rendered = render_likec4_views(
        {
            "product": {"name": "demo"},
            "projects": [{"id": "prj.pay", "name": "pay", "title": "Payments"}],
            "systems": [
                {"id": "sys.pay", "name": "pay", "title": "Pay", "project_id": "prj.pay", "category": "App"},
                {"id": "sys.docs", "name": "docs", "title": "Docs", "tags": ["External"], "category": "External"},
            ],
            "containers": [{"id": "ctr.pay.api", "system_id": "sys.pay"}],
            "relationships": [{"source_id": "ctr.pay.api", "target_id": "sys.docs"}],
            "relationship_statistics": {
                "systems": [
                    {
                        "system_id": "sys.docs",
                        "title": "Docs",
                        "incoming_distinct_source_container_count": 3,
                        "incoming_relationship_count": 3,
                        "incoming_source_system_ids": ["sys.pay"],
                    }
                ]
            },
            "dependency_hotspots": {"enabled": True, "min_count": 2, "max_hotspots": 5},
            "deployments": [
                {
                    "env": "prod",
                    "clusters": [
                        {
                            "id": "cluster-1",
                            "namespaces": [
                                {
                                    "id": "ns-pay",
                                    "instances": [
                                        {"id": "pod-api-app", "name": "api"},
                                        {"id": "pod-api-sidecar", "name": "api"},
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ],
        }
    )

    assert "view demo_landscape" in rendered
    assert "view demo_external_external_dependencies" in rendered
    assert 'title "External dependencies / External"' in rendered
    assert "view demo_dependency_hotspots" in rendered
    assert "deployment view demo_prod_deployment" in rendered
    assert "include demo_prod.cluster_1.ns_pay.pod_api_app" in rendered
    assert "include demo_prod.cluster_1.ns_pay.pod_api_sidecar" not in rendered
    assert "deployment view demo_prod_cluster_1_ns_pay_pod_api_app_containers" in rendered
    assert 'title "Deployments / demo / prod / api / Containers"' in rendered
    assert "include demo_prod.cluster_1.ns_pay.pod_api_app.*" in rendered
    assert "deployment view demo_prod_cluster_1_ns_pay_pod_api_sidecar_containers" not in rendered


def test_render_likec4_views_cover_platform_external_source_and_duplicate_titles():
    rendered = render_likec4_views(
        {
            "product": {"name": "demo"},
            "projects": [
                {"id": "prj.pay", "name": "pay", "title": "Payments"},
                {"id": "prj.ops", "name": "ops", "title": "Operations"},
            ],
            "systems": [
                {"id": "sys.pay.api", "name": "api", "title": "Worker", "project_id": "prj.pay", "category": "App"},
                {
                    "id": "sys.ops.worker",
                    "name": "worker",
                    "title": "Worker",
                    "project_id": "prj.ops",
                    "category": "App",
                },
                {"id": "sys.kafka", "name": "kafka", "title": "Kafka", "category": "Messaging"},
                {"id": "ext.partner", "name": "partner", "title": "Partner", "tags": ["External"], "category": "API"},
            ],
            "containers": [
                {"id": "ctr.pay.api", "system_id": "sys.pay.api"},
                {"id": "ctr.ops.worker", "system_id": "sys.ops.worker"},
                {"id": "ctr.kafka", "system_id": "sys.kafka"},
            ],
            "relationships": [
                {"source_id": "ctr.pay.api", "target_id": "sys.kafka"},
                {"source_id": "ctr.ops.worker", "target_id": "sys.kafka"},
                {"source_id": "ext.partner", "target_id": "ctr.pay.api"},
            ],
            "relationship_statistics": {
                "systems": [
                    {
                        "system_id": "ext.partner",
                        "title": "Partner",
                        "incoming_distinct_source_system_count": 0,
                        "incoming_relationship_count": 0,
                    }
                ]
            },
            "dependency_hotspots": {"enabled": False},
        }
    )

    assert "view demo_platform_support" in rendered
    assert "include sys_kafka" in rendered
    assert "view demo_api_external_dependencies" in rendered
    assert "include ext_partner" in rendered
    assert "include sys_pay_api" in rendered
    assert 'title "Systems / Worker (pay) / Dependencies"' in rendered
    assert "view demo_dependency_hotspots" not in rendered
    assert "view demo_external_dependencies" not in rendered


def test_render_likec4_views_handles_minimal_architecture_without_optional_sections():
    rendered = render_likec4_views({"product": {"name": "demo"}})

    assert rendered == (
        "views {\n"
        "\n"
        "  view demo_landscape {\n"
        '    title "Overview / demo / Product landscape"\n'
        "    // Product-level slice: internal systems plus high fan-in external dependencies.\n"
        "    autoLayout TopBottom\n"
        "  }\n"
        "\n"
        "}\n"
    )


def test_render_likec4_views_limits_dependency_hotspots_by_config():
    rendered = render_likec4_views(
        {
            "product": {"name": "demo"},
            "systems": [
                {"id": "sys.api", "name": "api", "title": "API", "category": "App"},
                {"id": "sys.worker", "name": "worker", "title": "Worker", "category": "App"},
                {"id": "sys.db", "name": "db", "title": "DB", "category": "Data"},
            ],
            "relationship_statistics": {
                "systems": [
                    {
                        "system_id": "sys.db",
                        "title": "DB",
                        "incoming_distinct_source_container_count": 10,
                        "incoming_relationship_count": 10,
                        "incoming_source_system_ids": ["sys.api"],
                    },
                    {
                        "system_id": "sys.worker",
                        "title": "Worker",
                        "incoming_distinct_source_container_count": 9,
                        "incoming_relationship_count": 9,
                        "incoming_source_system_ids": ["sys.api"],
                    },
                ]
            },
            "dependency_hotspots": {
                "enabled": True,
                "metric": "incoming_relationship_count",
                "min_count": 1,
                "max_hotspots": 1,
            },
        }
    )

    hotspot = rendered.split("view demo_dependency_hotspots", 1)[1]
    assert "include sys_db" in hotspot
    assert "include sys_api" in hotspot
    assert "include sys_worker" not in hotspot


def test_render_likec4_views_handles_external_to_external_relationships():
    rendered = render_likec4_views(
        {
            "product": {"name": "demo"},
            "systems": [
                {"id": "ext.source", "title": "Source", "tags": ["External"], "category": "API"},
                {"id": "ext.target", "title": "Target", "tags": ["External"], "category": "Data"},
            ],
            "relationships": [{"source_id": "ext.source", "target_id": "ext.target"}],
            "dependency_hotspots": {"enabled": False},
        }
    )

    assert "view demo_api_external_dependencies" in rendered
    assert "view demo_data_external_dependencies" in rendered
    assert "include ext_source" in rendered
    assert "include ext_target" in rendered
    assert "view demo_dependency_hotspots" not in rendered


def test_external_dependency_view_helpers_render_major_and_category_views():
    stats = {"ext.cache": {"incoming_source_system_ids": ["sys.api", "sys.worker"]}}
    systems_by_id = {"sys.api": {}, "sys.worker": {}}

    assert major_external_source_systems({"ext.cache"}, stats) == {"sys.api", "sys.worker"}

    major_lines = major_external_lines("demo", {"ext.cache"}, stats, systems_by_id)
    assert "  view demo_external_dependencies {" in major_lines
    assert '    title "Overview / demo / Major external dependencies"' in major_lines
    assert "    include sys_api" in major_lines
    assert "    include sys_worker" in major_lines
    assert "    include ext_cache" in major_lines

    category_lines = external_category_lines(
        "demo",
        {"Data Stores": {"ext.cache"}},
        {"Data Stores": {"sys.api", "sys.missing"}},
        systems_by_id,
    )
    assert "  view demo_data_stores_external_dependencies {" in category_lines
    assert '    title "External dependencies / Data Stores"' in category_lines
    assert "    include sys_api" in category_lines
    assert "    include sys_missing" not in category_lines
    assert "    include ext_cache" in category_lines


def test_major_external_lines_omits_empty_view():
    assert major_external_lines("demo", set(), {}, {}) == []
