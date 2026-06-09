from kmap.render.structurizr.model_content import (
    render_external_model,
    render_project_model,
    render_structurizr_model,
    structurizr_model_context,
)


def test_structurizr_model_context_builds_refs_containers_and_inbound_counts():
    context = structurizr_model_context(
        {
            "projects": [{"id": "prj.api"}],
            "systems": [{"id": "sys.api", "project_id": "prj.api"}, {"id": "ext.search"}],
            "containers": [
                {"id": "ctr.api", "system_id": "sys.api"},
                {"id": "ctr.search", "system_id": "ext.search"},
            ],
            "relationships": [
                {"source_id": "ctr.api", "target_id": "ext.search"},
                {"source_id": "ext.search", "target_id": "ctr.api"},
                {"source_id": "ctr.api", "target_id": ""},
            ],
        }
    )

    assert context["refs"]["sys.api"] == "sys_api"
    assert context["systems_by_id"]["ext.search"] == {"id": "ext.search"}
    assert context["projects_by_id"]["prj.api"] == {"id": "prj.api"}
    assert context["containers_by_system"]["sys.api"] == [{"id": "ctr.api", "system_id": "sys.api"}]
    assert context["inbound_counts"] == {"ext.search": 1, "ctr.api": 1}


def test_render_project_and_external_model_use_context():
    architecture = {
        "product": {"name": "shop"},
        "projects": [{"id": "prj.api", "name": "api", "title": "API"}],
        "systems": [
            {"id": "sys.api", "project_id": "prj.api", "title": "API"},
            {"id": "sys.worker", "project_id": "prj.api", "title": "Worker"},
            {"id": "ext.search", "title": "Search"},
        ],
        "containers": [{"id": "ctr.api", "system_id": "sys.api", "title": "API"}],
        "relationships": [],
    }
    context = structurizr_model_context(architecture)

    assert render_project_model(architecture, architecture["projects"][0], context).count("softwareSystem") == 2
    assert 'sys_api = softwareSystem "shop / API"' in render_project_model(
        architecture, architecture["projects"][0], context
    )
    assert render_external_model(architecture, [architecture["systems"][2]], context).startswith(
        'ext_org_shop_external_Search = softwareSystem "Search" "External dependency"'
    )


def test_render_structurizr_model_covers_metadata_summaries_and_relationship_fallbacks():
    architecture = {
        "workspace": {"org": "acme"},
        "product": {"name": "shop"},
        "projects": [{"id": "prj.shop.api", "name": "api", "title": "API"}],
        "systems": [
            {"id": "sys.shop.api", "project_id": "prj.shop.api", "title": "API"},
            {"id": "sys.shop.worker", "project_id": "prj.shop.api", "title": "Worker"},
            {"id": "sys.shop.missing", "project_id": "prj.missing", "title": "Missing Project"},
            {
                "id": "ext.search",
                "title": "Search",
                "metadata": {
                    "owner": "Search Team",
                    "zones": ["eu", "", "eu", "us"],
                    "blank": "",
                },
            },
            {"id": "ext.logs", "title": "Logs", "metadata": ["not", "a", "mapping"]},
        ],
        "containers": [
            {
                "id": "ctr.shop.api",
                "system_id": "sys.shop.api",
                "title": "API",
                "technology": "",
                "tags": ["public", "", "critical"],
                "discovery": {
                    "namespaces": ["api-prod", "API-PROD", "api-stage"],
                    "workloads": ["api", "worker"],
                },
                "runtime": {"workload_kinds": ["Deployment"]},
            },
            {"id": "ctr.shop.worker", "system_id": "sys.shop.worker", "title": "Worker"},
        ],
        "relationships": [
            {
                "id": "rel.1",
                "source_id": "sys.shop.api",
                "target_id": "ctr.shop.worker",
                "technology": "HTTP",
                "boundary": {"kind": "cross_project"},
            },
            {
                "id": "rel.2",
                "source_id": "ctr.shop.api",
                "target_id": "ext.search",
                "type": "https",
                "evidence": [{"kind": ""}],
            },
            {"id": "rel.ignored", "source_id": "ctr.shop.api", "target_id": "missing"},
            {"id": "rel.no_target", "source_id": "ctr.shop.api", "target_id": ""},
        ],
    }

    rendered = render_structurizr_model(architecture)

    assert 'sys_shop_api = softwareSystem "shop / API" "Product scope" {' in rendered
    assert 'sys_shop_worker = softwareSystem "shop / API / Worker" "Product scope" {' in rendered
    assert "Missing Project" not in rendered
    assert (
        'ctr_shop_api = container "API" "Namespaces: api-prod, api-stage\\nWorkloads: api, worker" "Deployment"'
        in rendered
    )
    assert '  tags "public,critical"' in rendered
    assert 'ext_acme_shop_external_Search = softwareSystem "Search" "External dependency" {' in rendered
    assert '    "owner" "Search Team"' in rendered
    assert '    "zones" "eu, us"' in rendered
    assert "blank" not in rendered
    assert 'ext_acme_shop_external_Logs = softwareSystem "Logs" "External dependency" {' in rendered
    assert 'sys_shop_api -> ctr_shop_worker "uses" "HTTP, cross-project"' in rendered
    assert 'ctr_shop_api -> ext_acme_shop_external_Search "uses" "https"' in rendered
    assert "rel.ignored" not in rendered
    assert "missing" not in rendered


def minimal_architecture():
    return {
        "workspace": {
            "generated_at": "2026-04-28T10:00:00Z",
            "generator": {
                "tool": "kmap",
                "version": "0.1.0",
                "config_file": "config/demo.yaml",
                "rules_file": "GENERATION_RULES.md",
            },
        },
        "product": {"name": "demo", "title": "Demo"},
        "projects": [
            {"id": "prj.demo.api", "name": "api", "title": "API", "owner_team": "Team"},
        ],
        "systems": [
            {"id": "sys.demo.api.api", "project_id": "prj.demo.api", "name": "api", "title": "API"},
            {"id": "ext.database_mysql", "name": "Database", "title": "Database", "element_type": "MySQL_DB"},
        ],
        "containers": [
            {
                "id": "ctr.demo.api.api.app",
                "system_id": "sys.demo.api.api",
                "name": "app",
                "title": "App",
                "technology": "Go",
            }
        ],
        "relationships": [
            {
                "id": "rel.1",
                "source_id": "ctr.demo.api.api.app",
                "target_id": "ext.database_mysql",
                "type": "mysql",
                "title": "MYSQL_DSN",
                "evidence": [{"kind": "env", "source": "MYSQL_DSN", "value": "MYSQL_DSN=mysql://demo"}],
                "boundary": {"kind": "project_to_external"},
            }
        ],
    }


def test_structurizr_model_focused_golden():
    assert render_structurizr_model(minimal_architecture()) == (
        'sys_demo_api_api = softwareSystem "demo / API" "Product scope" {\n'
        "  properties {\n"
        '    "system_id" "sys.demo.api.api"\n'
        '    "project_id" "prj.demo.api"\n'
        "  }\n"
        '  ctr_demo_api_api_app = container "App" "" "Go" {\n'
        "  }\n"
        "}\n"
        "\n"
        'ext_org_demo_external_Database = softwareSystem "Database" "External dependency" {\n'
        "}\n"
        'ctr_demo_api_api_app -> ext_org_demo_external_Database "uses" "env"\n'
    )


def test_structurizr_model_includes_project_resource_metadata():
    architecture = minimal_architecture()
    architecture["projects"][0]["repo"] = "https://gitlab.example/demo/api"
    architecture["projects"][0]["discovery"] = {"namespaces": ["api-prod"]}
    architecture["containers"][0]["discovery"] = {"clusters": ["cluster-a"], "namespaces": ["api-prod"]}
    architecture["containers"][0]["runtime"] = {"images": ["example/api:1"], "container_ports": ["8080/TCP"]}

    rendered = render_structurizr_model(architecture)

    assert "  url https://gitlab.example/demo/api\n" in rendered
    assert '    "resource.repo" "https://gitlab.example/demo/api"\n' in rendered
    assert '    "resource.clusters" "cluster-a"\n' not in rendered
    assert '    "resource.namespaces" "api-prod"\n' not in rendered
    assert '    "clusters" "cluster-a"\n' not in rendered
    assert '    "container_images" "example/api:1"\n' not in rendered
    assert '    "container_ports" "8080/TCP"\n' not in rendered


def test_structurizr_model_derives_container_description_and_technology():
    architecture = minimal_architecture()
    architecture["containers"][0]["technology"] = ""
    architecture["containers"][0]["discovery"] = {
        "namespaces": ["api-prod"],
        "workloads": ["prod-api"],
    }
    architecture["containers"][0]["runtime"] = {"workload_kinds": ["Deployment"]}
    architecture["relationships"].append(
        {
            "id": "rel.2",
            "source_id": "ext.database_mysql",
            "target_id": "ctr.demo.api.api.app",
            "type": "tcp",
        }
    )

    rendered = render_structurizr_model(architecture)

    assert (
        'ctr_demo_api_api_app = container "App" "Namespace: api-prod\\nWorkload: prod-api\\nUsed by: 1" "Deployment" {'
        in rendered
    )


def test_structurizr_model_keeps_discovery_descriptions_compact():
    architecture = minimal_architecture()
    architecture["containers"][0]["description"] = ""
    architecture["containers"][0]["discovery"] = {
        "namespaces": ["kafka-exporter"],
        "workloads": [
            "dev-kafka-exporter",
            "kafka-exporter-dev-kafka-exporter",
            "kafka-exporter-dev-pd-18636-kafka-exporter",
            "kafka-exporter-dev-wpdo-7650-kafka-exporter",
        ],
    }

    rendered = render_structurizr_model(architecture)

    assert 'container "App" "Namespace: kafka-exporter\\nWorkloads: 4 observed" "Go"' in rendered


def test_structurizr_model_normalizes_literal_newlines_in_descriptions():
    architecture = minimal_architecture()
    architecture["containers"].append(
        {
            "id": "extc.database_mysql.primary",
            "system_id": "ext.database_mysql",
            "name": "mysql-primary",
            "title": "MySQL Primary",
            "technology": "External dependency",
            "description": "External dependency\\nEndpoint: mysql-primary",
        }
    )

    rendered = render_structurizr_model(architecture)

    assert '"External dependency\\nEndpoint: mysql-primary"' in rendered
    assert '"External dependency\\\\nEndpoint: mysql-primary"' not in rendered


def test_structurizr_model_deduplicates_relationships_between_same_elements():
    architecture = minimal_architecture()
    architecture["relationships"].append(
        {
            "id": "rel.2",
            "source_id": "ctr.demo.api.api.app",
            "target_id": "ext.database_mysql",
            "type": "mysql",
            "evidence": [{"kind": "vault", "source": "MYSQL_DSN"}],
        }
    )

    rendered = render_structurizr_model(architecture)

    assert rendered.count('ctr_demo_api_api_app -> ext_org_demo_external_Database "uses"') == 1
    assert 'ctr_demo_api_api_app -> ext_org_demo_external_Database "uses" "env"' in rendered
