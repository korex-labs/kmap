from kmap.identifiers import architecture_id
from kmap.model.relationships import (
    build_relationship_statistics,
    relation_origin_label,
    relationship_type_from_dependency,
)


def test_relationship_helpers_and_statistics_group_by_systems():
    assert architecture_id("sys", "Demo", "Payment Gateway") == "sys.demo.payment_gateway"
    assert relationship_type_from_dependency("redis.local", "CACHE_URL") == "redis"
    assert relation_origin_label("VaultEnv") == "vault"

    stats = build_relationship_statistics(
        systems=[
            {"id": "sys.a", "title": "A", "kind": "internal", "project_id": "prj.a"},
            {"id": "sys.b", "title": "B", "kind": "external", "project_id": ""},
        ],
        containers=[
            {"id": "ctr.a", "system_id": "sys.a"},
        ],
        relationships=[
            {
                "id": "rel.1",
                "source_id": "ctr.a",
                "target_id": "sys.b",
                "type": "https",
                "boundary": {"kind": "project_to_external"},
            }
        ],
    )

    assert stats["summary"] == {
        "raw_relationship_count": 1,
        "system_relationship_group_count": 1,
    }
    system_b = next(item for item in stats["systems"] if item["system_id"] == "sys.b")
    assert system_b["incoming_relationship_count"] == 1
    assert system_b["incoming_source_container_ids"] == ["ctr.a"]


def test_relationship_statistics_tracks_outgoing_aggregates_and_ignores_unknown_elements():
    stats = build_relationship_statistics(
        systems=[
            {"id": "sys.a", "title": "A", "kind": "internal", "project_id": "prj.a"},
            {"id": "sys.b", "title": "B", "kind": "external", "project_id": ""},
        ],
        containers=[
            {"id": "ctr.a", "system_id": "sys.a"},
            {"id": "ctr.b", "system_id": "sys.b"},
        ],
        relationships=[
            {
                "id": "rel.1",
                "source_id": "ctr.a",
                "target_id": "ctr.b",
                "type": "https",
                "boundary": {"kind": "project_to_external"},
            },
            {
                "id": "rel.2",
                "source_id": "ctr.a",
                "target_id": "ctr.b",
                "type": "https",
                "boundary": {"kind": "project_to_external"},
            },
            {
                "id": "rel.ignored",
                "source_id": "ctr.missing",
                "target_id": "ctr.b",
                "type": "https",
                "boundary": {"kind": "project_to_external"},
            },
        ],
    )

    assert stats["summary"] == {
        "raw_relationship_count": 3,
        "system_relationship_group_count": 1,
    }

    duplicate_relationship_count = 2
    system_a = next(item for item in stats["systems"] if item["system_id"] == "sys.a")
    assert system_a["outgoing_relationship_count"] == duplicate_relationship_count
    assert system_a["outgoing_target_system_ids"] == ["sys.b"]
    assert system_a["outgoing_target_container_ids"] == ["ctr.b"]
    assert system_a["outgoing_by_type"] == {"https": 2}
    assert system_a["outgoing_by_boundary"] == {"project_to_external": 2}

    aggregate = stats["system_relationship_groups"][0]
    assert aggregate["relationship_count"] == duplicate_relationship_count
    assert aggregate["source_container_ids"] == ["ctr.a"]
    assert aggregate["target_container_ids"] == ["ctr.b"]
    assert aggregate["source_container_count"] == 1
    assert aggregate["target_container_count"] == 1
    assert aggregate["relationship_ids"] == ["rel.1", "rel.2"]
