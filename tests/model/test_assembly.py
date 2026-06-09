from kmap.model.assembly import (
    ArchitectureDocumentContext,
    architecture_document,
    architecture_document_from_context,
    deployment_entries_from_envs,
    traffic_flows_from_workloads,
)


def test_traffic_flows_from_workloads_uses_primary_container_and_instance():
    flows = traffic_flows_from_workloads(
        workloads_by_service_id={
            "svc-a": {
                "cluster": "cluster-a",
                "namespace": "ns-a",
                "traffic_routes": [
                    {
                        "direction": "outbound",
                        "hops": [{"kind": "service"}],
                        "source": {"kind": "pod"},
                        "target": {"kind": "service"},
                    }
                ],
            }
        },
        workload_primary_container_ids={"svc-a": "ctr.a"},
        workload_primary_instance_ids={"svc-a": "inst.a"},
    )

    assert flows[0] == {
        "id": flows[0]["id"],
        "direction": "outbound",
        "service_id": "svc-a",
        "container_id": "ctr.a",
        "instance_id": "inst.a",
        "cluster": "cluster-a",
        "namespace": "ns-a",
        "source": {"kind": "pod"},
        "hops": [{"kind": "service"}],
        "target": {"kind": "service"},
        "confidence": 0.8,
    }
    assert flows[0]["id"].startswith("flow.")


def test_deployment_entries_from_envs_sorts_clusters_and_namespaces():
    deployments = deployment_entries_from_envs(
        {
            "prod": {
                "env": "prod",
                "clusters": {
                    "cluster.z": {
                        "id": "cluster.z",
                        "name": "z",
                        "namespaces": {
                            "ns.b": {"id": "ns.b", "name": "b"},
                            "ns.a": {"id": "ns.a", "name": "a"},
                        },
                    },
                    "cluster.a": {
                        "id": "cluster.a",
                        "name": "a",
                        "namespaces": {},
                    },
                },
            }
        }
    )

    assert [cluster["name"] for cluster in deployments[0]["clusters"]] == ["a", "z"]
    assert [namespace["name"] for namespace in deployments[0]["clusters"][1]["namespaces"]] == ["a", "b"]


def test_architecture_document_sorts_entries_and_writes_generation_hints():
    naming = type("Naming", (), {"org": "DemoOrg", "env": "dev"})()
    architecture = architecture_document(
        naming=naming,
        product_id="prod.demo",
        product_name="demo",
        product_metadata={"title": "Demo", "owner_team": "Platform"},
        generated_at="2026-05-11T00:00:00Z",
        generator={"tool": "kmap", "version": "0.1.0", "rules_file": "GENERATION_RULES.md"},
        config_file="config/demo.yaml",
        discovery_config={"mode": "test"},
        projects_by_id={"prj.b": {"id": "prj.b"}, "prj.a": {"id": "prj.a"}},
        systems_by_id={"sys.b": {"id": "sys.b"}, "sys.a": {"id": "sys.a"}},
        containers_by_id={},
        relationships=[],
        traffic_flows=[{"id": "flow.b"}, {"id": "flow.a"}],
        deployments=[],
        external_mapping_summaries=[],
        dependency_hotspots_config={"enabled": True},
        report_count=2,
        workload_count=3,
    )

    assert architecture["workspace"]["default_env"] == "dev"
    assert architecture["workspace"]["source"]["config_file"] == "config/demo.yaml"
    assert [project["id"] for project in architecture["projects"]] == ["prj.a", "prj.b"]
    assert [system["id"] for system in architecture["systems"]] == ["sys.a", "sys.b"]
    assert [flow["id"] for flow in architecture["traffic_flows"]] == ["flow.a", "flow.b"]
    assert architecture["generation_hints"] == {
        "report_count": 2,
        "workload_count": 3,
        "relationships_included": False,
        "relationship_count": 0,
        "traffic_flow_count": 2,
    }


def test_architecture_document_from_context_matches_wrapper():
    naming = type("Naming", (), {"org": "DemoOrg", "env": "dev"})()
    context = ArchitectureDocumentContext(
        naming=naming,
        product_id="prod.demo",
        product_name="demo",
        product_metadata={"title": "Demo", "owner_team": "Platform"},
        generated_at="2026-05-11T00:00:00Z",
        generator={"tool": "kmap", "version": "0.1.0", "rules_file": "GENERATION_RULES.md"},
        config_file="config/demo.yaml",
        discovery_config={"mode": "test"},
        projects_by_id={"prj.b": {"id": "prj.b"}, "prj.a": {"id": "prj.a"}},
        systems_by_id={"sys.b": {"id": "sys.b"}, "sys.a": {"id": "sys.a"}},
        containers_by_id={},
        relationships=[],
        traffic_flows=[{"id": "flow.b"}, {"id": "flow.a"}],
        deployments=[],
        external_mapping_summaries=[],
        dependency_hotspots_config={"enabled": True},
        report_count=2,
        workload_count=3,
    )

    assert architecture_document_from_context(context) == architecture_document(
        naming=naming,
        product_id="prod.demo",
        product_name="demo",
        product_metadata={"title": "Demo", "owner_team": "Platform"},
        generated_at="2026-05-11T00:00:00Z",
        generator={"tool": "kmap", "version": "0.1.0", "rules_file": "GENERATION_RULES.md"},
        config_file="config/demo.yaml",
        discovery_config={"mode": "test"},
        projects_by_id={"prj.b": {"id": "prj.b"}, "prj.a": {"id": "prj.a"}},
        systems_by_id={"sys.b": {"id": "sys.b"}, "sys.a": {"id": "sys.a"}},
        containers_by_id={},
        relationships=[],
        traffic_flows=[{"id": "flow.b"}, {"id": "flow.a"}],
        deployments=[],
        external_mapping_summaries=[],
        dependency_hotspots_config={"enabled": True},
        report_count=2,
        workload_count=3,
    )
