from kmap.render.structurizr.views import render_structurizr_views


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


def test_structurizr_views_include_deployment_view_when_deployments_exist():
    architecture = minimal_architecture()
    architecture["deployments"] = [{"env": "prod", "clusters": []}]

    rendered = render_structurizr_views(architecture)

    assert 'deployment * "prod" "deployment_demo_prod" "Deployments - demo / prod" {' in rendered
    assert "  include *\n" in rendered
    assert "  autoLayout tb\n" in rendered


def test_structurizr_views_focused_golden():
    assert render_structurizr_views(minimal_architecture()) == (
        "systemLandscape landscape {\n"
        "  include sys_demo_api_api\n"
        "  include ext_org_demo_external_Database\n"
        "  autoLayout lr\n"
        "}\n"
        "\n"
        'systemContext sys_demo_api_api system_context_sys_demo_api_api "System Context - API" {\n'
        "  include sys_demo_api_api\n"
        "  include ext_org_demo_external_Database\n"
        "  autoLayout lr\n"
        "}\n"
        'container sys_demo_api_api containers_sys_demo_api_api "Containers - API" {\n'
        "  include ctr_demo_api_api_app\n"
        "  include ext_org_demo_external_Database\n"
        "  autoLayout lr\n"
        "}\n"
    )


def test_structurizr_container_view_includes_external_endpoint_containers():
    architecture = minimal_architecture()
    architecture["containers"].append(
        {
            "id": "extc.database_mysql.primary",
            "system_id": "ext.database_mysql",
            "name": "primary",
            "title": "Primary MySQL",
            "technology": "External dependency",
        }
    )
    architecture["relationships"][0]["target_id"] = "extc.database_mysql.primary"

    rendered = render_structurizr_views(architecture)

    assert "  include extsys_org_demo_external_mapped_Database\n" in rendered
    assert "  include extc_org_demo_external_primary\n" in rendered


def test_structurizr_views_skip_duplicate_or_unknown_refs():
    architecture = minimal_architecture()
    architecture["systems"].append(dict(architecture["systems"][0]))
    architecture["relationships"].append(
        {
            "id": "rel.missing",
            "source_id": "ctr.demo.api.api.app",
            "target_id": "missing.system",
            "type": "http",
            "boundary": {"kind": "project_to_external"},
        }
    )

    rendered = render_structurizr_views(architecture)

    assert rendered.count("  include sys_demo_api_api\n") == 2
    assert "missing" not in rendered
