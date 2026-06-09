from kmap.render.structurizr.relations import (
    deduplicated_structurizr_relationships,
    relationship_has_external_endpoint,
    relationship_project_id,
    render_structurizr_relationships,
    split_structurizr_relationships_by_file,
    structurizr_relationship_file_path,
    structurizr_relationship_line,
    structurizr_relationship_technology,
)


def test_structurizr_relationship_technology_prefers_evidence_and_marks_cross_project():
    assert (
        structurizr_relationship_technology(
            {
                "type": "https",
                "technology": "HTTP",
                "evidence": [{"kind": ""}, {"kind": "env"}],
                "boundary": {"kind": "cross_project"},
            }
        )
        == "env, cross-project"
    )
    assert structurizr_relationship_technology({"technology": "HTTP", "type": "https"}) == "HTTP"
    assert structurizr_relationship_technology({"type": "tcp"}) == "tcp"


def test_structurizr_relationship_line_renders_and_skips_missing_refs():
    refs = {"ctr.api": "ctr_api", "ext.search": "ext_search"}

    assert structurizr_relationship_line(
        {"source_id": "ctr.api", "target_id": "ext.search", "type": "https"}, refs
    ) == ('ctr_api -> ext_search "uses" "https"')
    assert structurizr_relationship_line({"source_id": "ctr.api", "target_id": "missing", "type": "https"}, refs) == ""


def test_deduplicated_structurizr_relationships_keeps_first_pair_and_skips_missing_refs():
    refs = {"a": "a", "b": "b", "c": "c"}
    relationships = [
        {"id": "1", "source_id": "a", "target_id": "b", "type": "env"},
        {"id": "2", "source_id": "a", "target_id": "b", "type": "vault"},
        {"id": "3", "source_id": "missing", "target_id": "b"},
        {"id": "4", "source_id": "b", "target_id": "c"},
    ]

    assert [relationship["id"] for relationship in deduplicated_structurizr_relationships(relationships, refs)] == [
        "1",
        "4",
    ]
    assert render_structurizr_relationships(relationships, refs) == (
        'a -> b "uses" "env"\na -> b "uses" "vault"\nb -> c "uses" ""\n'
    )


def test_relationship_project_id_uses_system_container_then_container_project():
    systems_by_id = {
        "sys.api": {"project_id": "prj.api"},
        "sys.detached": {},
    }
    containers_by_id = {
        "ctr.api": {"system_id": "sys.api"},
        "ctr.detached": {"system_id": "sys.detached", "project_id": "legacy-project"},
    }

    assert relationship_project_id({"source_id": "sys.api"}, systems_by_id, containers_by_id) == "prj.api"
    assert relationship_project_id({"source_id": "ctr.api"}, systems_by_id, containers_by_id) == "prj.api"
    assert relationship_project_id({"source_id": "ctr.detached"}, systems_by_id, containers_by_id) == "legacy-project"


def test_relationship_has_external_endpoint_detects_external_systems_and_containers():
    systems_by_id = {
        "sys.api": {"project_id": "prj.api"},
        "ext.search": {},
    }
    containers_by_id = {
        "ctr.api": {"system_id": "sys.api"},
        "ctr.ext.search": {"system_id": "ext.search"},
    }

    assert relationship_has_external_endpoint(
        {"source_id": "ctr.api", "target_id": "ext.search"},
        systems_by_id,
        containers_by_id,
    )
    assert relationship_has_external_endpoint(
        {"source_id": "ctr.api", "target_id": "ctr.ext.search"},
        systems_by_id,
        containers_by_id,
    )
    assert not relationship_has_external_endpoint(
        {"source_id": "sys.api", "target_id": "ctr.api"},
        systems_by_id,
        containers_by_id,
    )


def test_split_structurizr_relationships_by_file_deduplicates_and_groups():
    refs = {
        "ctr.api": "ctr_api",
        "ctr.worker": "ctr_worker",
        "ext.search": "ext_search",
        "missing": "",
    }
    systems_by_id = {
        "sys.api": {"project_id": "prj.api"},
        "sys.worker": {"project_id": "prj.worker"},
        "ext.search": {},
    }
    containers_by_id = {
        "ctr.api": {"system_id": "sys.api"},
        "ctr.worker": {"system_id": "sys.worker"},
    }
    architecture = {
        "relationships": [
            {"id": "rel.1", "source_id": "ctr.api", "target_id": "ctr.worker"},
            {"id": "rel.2", "source_id": "ctr.api", "target_id": "ctr.worker"},
            {"id": "rel.3", "source_id": "ctr.worker", "target_id": "ext.search"},
            {"id": "rel.ignored", "source_id": "ctr.api", "target_id": "missing"},
        ]
    }

    external_relationships, relationships_by_project = split_structurizr_relationships_by_file(
        architecture,
        refs,
        systems_by_id,
        containers_by_id,
    )

    assert [relationship["id"] for relationship in external_relationships] == ["rel.3"]
    assert {key: [relationship["id"] for relationship in value] for key, value in relationships_by_project.items()} == {
        "prj.api": ["rel.1"]
    }


def test_structurizr_relationship_file_path_deduplicates_with_shared_helper():
    used_paths: set[str] = set()

    assert structurizr_relationship_file_path({"id": "prj.api", "name": "api"}, used_paths) == (
        "model/relations/api.dsl"
    )
    assert structurizr_relationship_file_path({"id": "prj.worker", "name": "api"}, used_paths) == (
        "model/relations/prj-worker.dsl"
    )
