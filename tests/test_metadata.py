from kmap.metadata import merge_database_metadata, merge_database_metadata_values, resource_property_key


def test_merge_database_metadata_deduplicates_and_preserves_existing_engine():
    target = {"metadata": {"database": {"engine": "mysql", "names": ["app"]}}}

    merge_database_metadata(
        target,
        {
            "engine": "postgres",
            "names": ["app", "audit", ""],
            "source_vars": ["MYSQL_DSN", "MYSQL_DSN"],
            "sources": ["env"],
        },
    )

    assert target["metadata"]["database"] == {
        "engine": "mysql",
        "names": ["app", "audit"],
        "source_vars": ["MYSQL_DSN"],
        "sources": ["env"],
    }


def test_resource_property_key_is_safe_for_renderer_metadata():
    assert resource_property_key("123 link") == "resource_123_link"
    assert resource_property_key("Run Book") == "Run_Book"
    assert resource_property_key("") == "unknown"


def test_merge_database_metadata_values_deduplicates_and_removes_empty_lists():
    db_meta = {"names": ["app"]}

    merge_database_metadata_values(db_meta, "names", ["app", "audit"])
    merge_database_metadata_values(db_meta, "source_vars", [])

    assert db_meta == {"names": ["app", "audit"]}
