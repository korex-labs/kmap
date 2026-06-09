from kmap.model.dependencies import (
    DependencyRelationshipContext,
    build_dependency_relationships,
    dependency_relationship,
    dependency_relationship_from_context,
)


def test_dependency_relationship_marks_same_project_as_generated_only():
    relationship = dependency_relationship(
        source_id="ctr.source",
        target_id="ctr.target",
        dep_key="redis.local",
        source_var="REDIS_URL",
        mapping=None,
        match_type="env",
        category="internal",
        boundary_kind="same_project",
        source_project_id="prj.a",
        target_project_id="prj.a",
        rel_metadata={},
        evidence="redis.local",
        source_origin="Env",
    )

    assert relationship["type"] == "redis"
    assert relationship["tags"] == ["Generated"]
    assert relationship["boundary"]["kind"] == "same_project"
    assert relationship["evidence"][0]["kind"] == "env"


def test_dependency_relationship_marks_cross_project_boundary():
    relationship = dependency_relationship(
        source_id="ctr.source",
        target_id="ctr.target",
        dep_key="redis.local",
        source_var="REDIS_URL",
        mapping=None,
        match_type="env",
        category="internal",
        boundary_kind="cross_project",
        source_project_id="prj.a",
        target_project_id="prj.b",
        rel_metadata={"database": {"engine": "redis"}},
        evidence="redis.local",
        source_origin="Env",
    )

    assert relationship["tags"] == ["Generated", "CrossBoundary"]
    assert relationship["boundary"] == {
        "source_project_id": "prj.a",
        "target_project_id": "prj.b",
        "kind": "cross_project",
    }
    assert relationship["metadata"] == {"database": {"engine": "redis"}}


def test_dependency_relationship_from_context_matches_wrapper():
    context = DependencyRelationshipContext(
        source_id="ctr.source",
        target_id="ctr.target",
        dep_key="redis.local",
        source_var="REDIS_URL",
        mapping=None,
        match_type="env",
        category="internal",
        boundary_kind="same_project",
        source_project_id="prj.a",
        target_project_id="prj.a",
        rel_metadata={},
        evidence="redis.local",
        source_origin="Env",
    )

    assert dependency_relationship_from_context(context) == dependency_relationship(
        source_id="ctr.source",
        target_id="ctr.target",
        dep_key="redis.local",
        source_var="REDIS_URL",
        mapping=None,
        match_type="env",
        category="internal",
        boundary_kind="same_project",
        source_project_id="prj.a",
        target_project_id="prj.a",
        rel_metadata={},
        evidence="redis.local",
        source_origin="Env",
    )


def test_build_dependency_relationships_creates_internal_relationship():
    relationships = build_dependency_relationships(
        dependency_relations=[
            {
                "source_service": "api",
                "target_service": "redis",
                "dependency_type": "INTERNAL",
                "dependency_key": "redis.local",
                "source_var": "REDIS_URL",
                "source_origin": "Env",
            }
        ],
        workload_primary_container_ids={"api": "ctr.api", "redis": "ctr.redis"},
        workload_project_ids={"api": "prj.demo", "redis": "prj.demo"},
        external_mappings=[],
        systems_by_id={},
        containers_by_id={},
    )

    assert len(relationships) == 1
    assert relationships[0]["source_id"] == "ctr.api"
    assert relationships[0]["target_id"] == "ctr.redis"
    assert relationships[0]["category"] == "internal"
    assert relationships[0]["boundary"]["kind"] == "same_project"


def test_build_dependency_relationships_creates_external_variable_system_metadata():
    systems_by_id = {}
    containers_by_id = {}

    relationships = build_dependency_relationships(
        dependency_relations=[
            {
                "source_service": "api",
                "dependency_type": "EXTERNAL",
                "dependency_key": "https://example.test",
                "source_var": "PARTNER_AUTH_ADDR",
                "source_origin": "VaultEnv",
                "evidence": "https://example.test",
            }
        ],
        workload_primary_container_ids={"api": "ctr.api"},
        workload_project_ids={"api": "prj.demo"},
        external_mappings=[],
        systems_by_id=systems_by_id,
        containers_by_id=containers_by_id,
    )

    external = next(iter(systems_by_id.values()))
    assert len(relationships) == 1
    assert relationships[0]["target_id"] == external["id"]
    assert external["name"] == "PARTNER_AUTH_ADDR"
    assert external["title"] == "Partner Auth Address"
    assert external["metadata"] == {
        "source_var": ["PARTNER_AUTH_ADDR"],
        "endpoint": ["https://example.test"],
        "source_origin": ["vault"],
    }
