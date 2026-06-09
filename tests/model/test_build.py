from types import SimpleNamespace


def test_architecture_model_from_reports_wires_config_and_dependency_inputs(monkeypatch, tmp_path):
    import kmap.model.build as build_module

    captured = {}
    project_metadata = {"single_system_projects": ["demo"]}
    namespace_projects = {"ns": "demo"}
    system_naming_config = {"mode": "configured"}
    dependency_hotspots_config = {"enabled": True}
    discovery_config = {"scan": "limited"}
    external_mappings = [{"name": "Redis"}]
    external_mapping_summaries = [{"name": "Redis", "match": ["redis"]}]
    dependency_relations = [{"source_service": "api", "dependency_key": "redis.local"}]
    workload = {"service_name": "api"}

    monkeypatch.setattr(
        build_module, "load_workloads_from_reports", lambda reports_dir: ([tmp_path / "api.json"], [workload])
    )
    monkeypatch.setattr(
        build_module, "naming_context_from_args", lambda args: SimpleNamespace(product="demo", env="stage")
    )
    monkeypatch.setattr(build_module, "load_external_mappings", lambda config_path: external_mappings)
    monkeypatch.setattr(build_module, "load_external_mapping_summaries", lambda config_path: external_mapping_summaries)
    monkeypatch.setattr(build_module, "load_dependency_relations", lambda dependencies_file: dependency_relations)

    def fake_process_workload(**kwargs):
        assert kwargs["project_metadata"] == project_metadata
        assert kwargs["config_namespace_projects"] == namespace_projects
        assert kwargs["system_naming_config"] == system_naming_config
        kwargs["workload_primary_container_ids"]["api"] = "ctr.api"
        kwargs["workload_primary_instance_ids"]["api"] = "inst.api"
        kwargs["workload_project_ids"]["api"] = "prj.demo"
        kwargs["workloads_by_service_id"]["api"] = workload

    def fake_build_dependency_relationships(**kwargs):
        assert kwargs["dependency_relations"] is dependency_relations
        assert kwargs["external_mappings"] is external_mappings
        assert kwargs["workload_primary_container_ids"] == {"api": "ctr.api"}
        assert kwargs["workload_project_ids"] == {"api": "prj.demo"}
        return [{"id": "rel.redis"}]

    def fake_architecture_document_from_context(context):
        captured.update(context.__dict__)
        return {"schema_version": "test"}

    monkeypatch.setattr(build_module, "process_workload", fake_process_workload)
    monkeypatch.setattr(build_module, "build_dependency_relationships", fake_build_dependency_relationships)
    monkeypatch.setattr(build_module, "architecture_document_from_context", fake_architecture_document_from_context)

    architecture = build_module.architecture_model_from_reports(
        SimpleNamespace(
            reports_dir=str(tmp_path),
            config="config.yaml",
            dependencies_file="dependencies.json",
            product_metadata={},
            project_metadata=project_metadata,
            config_namespace_projects=namespace_projects,
            system_naming_config=system_naming_config,
            dependency_hotspots_config=dependency_hotspots_config,
            discovery_config=discovery_config,
        )
    )

    assert architecture == {"schema_version": "test"}
    assert captured["product_name"] == "demo"
    assert captured["config_file"] == "config.yaml"
    assert captured["discovery_config"] == discovery_config
    assert captured["relationships"] == [{"id": "rel.redis"}]
    assert captured["external_mapping_summaries"] is external_mapping_summaries
    assert captured["dependency_hotspots_config"] == dependency_hotspots_config
    assert captured["report_count"] == 1
    assert captured["workload_count"] == 1
