from kmap.render.likec4.relations import (
    likec4_relationship_kind,
    render_likec4_relation_files,
    render_likec4_relations,
)


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


def test_likec4_relations_focused_golden():
    assert render_likec4_relations(minimal_architecture()) == (
        "model {\n"
        "  // Generated relationships by kmap. Do not edit manually.\n"
        "\n"
        '  sys_demo_api_api.ctr_demo_api_api_app -[tcp]-> ext_database_mysql "MYSQL_DSN" {\n'
        '    description "Boundary: project_to_external"\n'
        "  }\n"
        "\n"
        "}\n"
    )


def test_likec4_relationship_kind_maps_known_protocols():
    assert likec4_relationship_kind("http") == "http_s"
    assert likec4_relationship_kind("HTTPS") == "http_s"
    assert likec4_relationship_kind("kafka") == "KafkaPub"
    assert likec4_relationship_kind("") == "tcp"


def test_render_likec4_relations_skips_self_edges_and_escapes_fields():
    rendered = render_likec4_relations(
        {
            "systems": [{"id": "sys.a"}, {"id": "sys.b"}],
            "containers": [{"id": "ctr.a", "system_id": "sys.a"}],
            "relationships": [
                {"id": "1", "source_id": "ctr.a", "target_id": "ctr.a"},
                {
                    "id": "2",
                    "source_id": "ctr.a",
                    "target_id": "sys.b",
                    "type": "https",
                    "title": 'calls "B"',
                    "technology": "HTTP",
                    "boundary": {"kind": "project_to_external"},
                    "metadata": {"database": {"engine": "mysql", "names": ["wallet"]}},
                },
            ],
        }
    )

    assert 'sys_a.ctr_a -[http_s]-> sys_b "calls \\"B\\""' in rendered
    assert 'technology "HTTP"' in rendered
    assert 'description "Boundary: project_to_external"' in rendered
    assert 'database_engine "mysql"' in rendered
    assert 'databases "wallet"' in rendered
    assert "ctr_a -[tcp]-> ctr_a" not in rendered


def test_render_likec4_relations_skips_blank_endpoints_and_defaults_title():
    rendered = render_likec4_relations(
        {
            "systems": [{"id": "sys.a"}, {"id": "sys.b"}],
            "relationships": [
                {"id": "1", "source_id": "", "target_id": "sys.b", "title": "ignored"},
                {"id": "2", "source_id": "sys.a", "target_id": "", "title": "ignored"},
                {"id": "3", "source_id": "sys.a", "target_id": "sys.b", "type": "kafka"},
            ],
        }
    )

    assert 'sys_a -[KafkaPub]-> sys_b "uses" {' in rendered
    assert "ignored" not in rendered
    assert "id -[tcp]" not in rendered


def test_render_likec4_relation_files_split_and_deduplicate_project_paths():
    architecture = {
        "projects": [
            {"id": "prj.api", "name": "api", "title": "API"},
            {"id": "api", "name": "api", "title": "API Duplicate"},
            {"id": "prj.worker", "name": "api", "title": "Worker"},
            {"id": "aaa", "name": "prj-api", "title": "Project API"},
        ],
        "systems": [
            {"id": "sys.api", "project_id": "prj.api", "title": "API"},
            {"id": "sys.api.duplicate", "project_id": "api", "title": "API Duplicate"},
            {"id": "sys.worker", "project_id": "prj.worker", "title": "Worker"},
            {"id": "sys.project.api", "project_id": "aaa", "title": "Project API"},
            {"id": "ext.docs", "title": "Docs", "tags": ["External"]},
        ],
        "containers": [
            {"id": "ctr.api", "system_id": "sys.api", "title": "API"},
            {"id": "ctr.api.duplicate", "system_id": "sys.api.duplicate", "title": "API Duplicate"},
            {"id": "ctr.worker", "system_id": "sys.worker", "title": "Worker"},
            {"id": "ctr.project.api", "system_id": "sys.project.api", "title": "Project API"},
            {"id": "ctr.detached", "project_id": "legacy-project", "title": "Detached"},
        ],
        "relationships": [
            {"id": "rel.1", "source_id": "ctr.api", "target_id": "ctr.worker", "type": "tcp"},
            {"id": "rel.2", "source_id": "ctr.api.duplicate", "target_id": "ctr.api", "type": "tcp"},
            {"id": "rel.3", "source_id": "ctr.worker", "target_id": "ctr.api", "type": "tcp"},
            {"id": "rel.4", "source_id": "ctr.detached", "target_id": "ctr.api", "type": "tcp"},
            {"id": "rel.5", "source_id": "ctr.api", "target_id": "ext.docs", "type": "http"},
            {"id": "rel.6", "source_id": "ctr.project.api", "target_id": "ctr.api", "type": "tcp"},
        ],
    }

    files = render_likec4_relation_files(architecture)

    assert "model/relations/api.c4" in files
    assert "model/relations/prj-api.c4" in files
    assert "model/relations/prj-api-2.c4" in files
    assert "model/relations/prj-worker.c4" in files
    assert "model/relations/legacy-project.c4" in files
    assert 'sys_api_duplicate.ctr_api_duplicate -[tcp]-> sys_api.ctr_api "uses"' in files["model/relations/api.c4"]
    assert 'sys_project_api.ctr_project_api -[tcp]-> sys_api.ctr_api "uses"' in files["model/relations/prj-api.c4"]
    assert 'sys_api.ctr_api -[tcp]-> sys_worker.ctr_worker "uses"' in files["model/relations/prj-api-2.c4"]
    assert 'sys_worker.ctr_worker -[tcp]-> sys_api.ctr_api "uses"' in files["model/relations/prj-worker.c4"]
    assert 'ctr_detached -[tcp]-> sys_api.ctr_api "uses"' in files["model/relations/legacy-project.c4"]
    assert 'sys_api.ctr_api -[http_s]-> ext_docs "uses"' in files["model/relations/00-external.c4"]
