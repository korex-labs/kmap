from kmap.render.likec4.readme import render_likec4_readme


def test_render_likec4_readme_summarizes_projects_and_dependencies():
    rendered = render_likec4_readme(
        {
            "workspace": {
                "default_env": "prod",
                "generated_at": "2026-01-01T00:00:00Z",
                "source": {"config_file": "config/demo.yaml"},
            },
            "product": {"name": "demo", "title": "Demo", "owner_team": "Platform"},
            "projects": [{"id": "prj.pay", "name": "pay", "title": "Payments", "owner_team": "Team"}],
            "systems": [
                {"id": "sys.pay", "title": "Pay", "project_id": "prj.pay"},
                {"id": "ext.docs", "title": "docs.example.com", "tags": ["External"], "element_type": "Website"},
            ],
            "containers": [{"id": "ctr.pay.api", "system_id": "sys.pay", "project_id": "prj.pay"}],
            "relationships": [
                {
                    "source_id": "ctr.pay.api",
                    "target_id": "ext.docs",
                    "type": "https",
                    "title": "GET docs.example.com",
                    "boundary": {"kind": "project_to_external"},
                }
            ],
            "relationship_statistics": {
                "systems": [
                    {
                        "system_id": "ext.docs",
                        "title": "docs.example.com",
                        "kind": "external",
                        "category": "External",
                        "incoming_distinct_source_container_count": 1,
                        "incoming_relationship_count": 1,
                        "outgoing_relationship_count": 0,
                        "outgoing_distinct_target_system_count": 0,
                    }
                ]
            },
            "deployments": [{"env": "prod", "clusters": []}],
        }
    )

    assert "# Demo LikeC4" in rendered
    assert "## External Dependencies" in rendered
    assert "docs.example.com" in rendered
    assert "GET docs.example.com" in rendered
    assert "`model/.kmap-generated.json` tracks generated model fragments" in rendered


def test_render_likec4_readme_includes_resources_database_evidence_and_flows():
    rendered = render_likec4_readme(
        {
            "workspace": {
                "product": "workspace-demo",
                "default_env": "stage",
                "generation": "ignored",
            },
            "product": {"domain": "Commerce"},
            "generation_hints": {"report_count": 2, "workload_count": 3},
            "projects": [
                {
                    "id": "prj.pay",
                    "name": "pay",
                    "title": "Payments",
                    "owner_team": "Team",
                    "discovery": {"namespaces": ["pay-prod", "pay-stage", "pay-dev", "pay-qa"]},
                    "resources": {"repo": "https://git.example/pay"},
                },
                {"id": "prj.ops", "name": "ops", "title": "Operations"},
            ],
            "systems": [
                {"id": "sys.pay", "title": "Pay", "project_id": "prj.pay", "element_type": "GoLang_App"},
                {"id": "sys.ops", "title": "Ops", "project_id": "prj.ops"},
                {"id": "ext.mysql", "title": "MySQL", "tags": ["External"], "element_type": "MySQL_DB"},
                {"id": "ext.generic", "title": "Generic External", "tags": ["External"]},
            ],
            "containers": [
                {"id": "ctr.pay.api", "system_id": "sys.pay", "project_id": "prj.pay"},
                {"id": "ctr.ops.app", "system_id": "sys.ops", "project_id": "prj.ops"},
            ],
            "relationships": [
                {
                    "source_id": "ctr.pay.api",
                    "target_id": "ext.mysql",
                    "type": "mysql",
                    "title": "MYSQL_DSN",
                    "metadata": {"database": {"names": ["wallet", "ledger"]}},
                    "boundary": {
                        "kind": "project_to_external",
                        "source_project_id": "prj.pay",
                        "target_project_id": "external",
                    },
                },
                {
                    "source_id": "ctr.pay.api",
                    "target_id": "ctr.ops.app",
                    "type": "https",
                    "title": "Ops API",
                    "boundary": {
                        "kind": "cross_project",
                        "source_project_id": "prj.pay",
                        "target_project_id": "prj.ops",
                    },
                },
            ],
            "relationship_statistics": {
                "systems": [
                    {
                        "system_id": "sys.pay",
                        "title": "Pay",
                        "kind": "internal",
                        "category": "App",
                        "incoming_distinct_source_container_count": 0,
                        "incoming_relationship_count": 0,
                        "outgoing_relationship_count": 2,
                        "outgoing_distinct_target_system_count": 2,
                    },
                    {
                        "system_id": "ext.mysql",
                        "title": "MySQL",
                        "kind": "external",
                        "category": "Data",
                        "incoming_distinct_source_container_count": 1,
                        "incoming_relationship_count": 1,
                        "outgoing_relationship_count": 0,
                        "outgoing_distinct_target_system_count": 0,
                    },
                ]
            },
            "deployments": [
                {
                    "env": "",
                    "clusters": [
                        {
                            "namespaces": [
                                {"instances": [{"id": "pod-api"}, {"id": "pod-worker"}]},
                                {"instances": []},
                            ]
                        }
                    ],
                }
            ],
            "traffic_flows": [
                {
                    "id": "flow.1",
                    "direction": "",
                    "source": {},
                    "namespace": "pay-prod",
                    "hops": [{"type": "Ingress", "name": "pay"}, {"type": "Service", "name": "pay-svc"}],
                }
            ],
        }
    )

    assert "# workspace-demo LikeC4" in rendered
    assert "Domain" in rendered
    assert "Commerce" in rendered
    assert "Inspect reports" in rendered
    assert "Workloads" in rendered
    assert "https://git.example/pay" in rendered
    assert "databases: wallet, ledger" in rendered
    assert "pay" in rendered
    assert "ops" in rendered
    assert "stage" in rendered
    assert "Ingress:pay -> Service:pay-svc" in rendered
    assert "Projects without `owner_team`" in rendered
    assert "External systems still using generic `system` type" in rendered
    assert "Generic External" in rendered
    assert "Internal systems still using generic `system` type" in rendered
    assert "Ops" in rendered


def test_render_likec4_readme_uses_defaults_and_skips_optional_sections_when_empty():
    rendered = render_likec4_readme({})

    assert "# product LikeC4" in rendered
    assert "| Product" in rendered
    assert "| Environment" in rendered
    assert "| Config" in rendered
    assert "product" in rendered
    assert "prod" in rendered
    assert "config/product.yaml" in rendered
    assert "## Project Resources" not in rendered
    assert "## Traffic Flows" not in rendered
    assert "Projects without `owner_team`" in rendered
