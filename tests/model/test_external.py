from kmap.model.external import (
    append_metadata_value,
    external_identity_name,
    external_type_name,
    external_variable_title,
)


def test_external_identity_name_uses_aggregate_mapping_name():
    assert (
        external_identity_name(
            "api.example.com",
            "PARTNER_URL",
            {"name": "Partner API"},
            aggregate_mapping=True,
        )
        == "Partner API"
    )


def test_external_identity_name_falls_back_to_source_endpoint_and_default():
    assert external_identity_name("api.example.com:443", "", None, aggregate_mapping=False) == "api.example.com"
    assert external_identity_name("", "", None, aggregate_mapping=False) == "external"


def test_external_type_name_honors_aggregate_mapping_type_and_tag():
    assert (
        external_type_name(
            "Redis",
            "redis.example.com:6379",
            {"element_type": "Redis_DB", "tag": "Data"},
            aggregate_mapping=True,
            source_var="REDIS_URL",
        )
        == "Redis_DB"
    )


def test_external_type_name_uses_external_api_for_unmapped_source_vars():
    assert (
        external_type_name(
            "Partner",
            "https://api.example.com",
            {"element_type": "Website", "tag": "Website"},
            aggregate_mapping=False,
            source_var="PARTNER_URL",
        )
        == "External_API"
    )


def test_external_variable_title_preserves_common_acronyms_and_replacements():
    assert external_variable_title("PARTNER_AUTH_ADDR") == "Partner Auth Address"
    assert external_variable_title("PUBLIC_HTTP_URL") == "Public HTTP URL"


def test_append_metadata_value_deduplicates_and_preserves_existing_scalars():
    system = {"metadata": {"source_vars": "PARTNER_AUTH_ADDR"}}

    append_metadata_value(system, "source_vars", "PARTNER_AUTH_ADDR")
    append_metadata_value(system, "source_vars", "PARTNER_URL")
    append_metadata_value(system, "source_vars", "")

    assert system == {"metadata": {"source_vars": ["PARTNER_AUTH_ADDR", "PARTNER_URL"]}}
