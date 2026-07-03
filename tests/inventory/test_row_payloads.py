from kmap.inventory.row_payloads import (
    bucket_key,
    bucket_sort_key,
    namespace_row_with_labels,
    normalize_row_value,
    normalize_string_dict,
    row_quality,
)


def test_normalize_string_dict_preserves_labels_as_string_mapping():
    assert normalize_string_dict(
        {
            "namespace": "api-prod",
            "labels": {"": "skip", "enabled": True, "revision": 3, "empty": None},
            "missing": None,
        }
    ) == {
        "namespace": "api-prod",
        "labels": {"enabled": "True", "revision": "3", "empty": ""},
        "missing": "",
    }


def test_normalize_row_value_stringifies_non_label_values():
    assert normalize_row_value("repository", None) == ""
    assert normalize_row_value("repository", 123) == "123"


def test_namespace_row_with_labels_carries_existing_labels_when_new_best_row_lacks_them():
    row = {"namespace": "api-prod", "repository": "https://git.example/api"}
    existing = {"namespace": "api-prod", "labels": {"app": "api"}}

    assert namespace_row_with_labels(row, existing) == {
        "namespace": "api-prod",
        "repository": "https://git.example/api",
        "labels": {"app": "api"},
    }


def test_row_quality_counts_metadata_and_repository_length():
    assert row_quality({"repository": "https://git.example/api", "owner_team": "Ops"}) > row_quality(
        {"repository": "api"}
    )


def test_bucket_key_is_case_insensitive_bucket_identity():
    assert bucket_key(
        {
            "namespace": "Api-Prod",
            "repository": "HTTPS://GIT.EXAMPLE/API",
            "bucket": "Reports",
            "endpoint": "S3.EXAMPLE.COM",
            "source_var": "S3_BUCKET",
        }
    ) == ("api-prod", "https://git.example/api", "reports", "s3.example.com", "s3_bucket")


def test_bucket_sort_key_orders_human_readable_bucket_rows():
    assert bucket_sort_key(
        {
            "namespace": "api-prod",
            "repository": "https://git.example/api",
            "bucket": "reports",
            "endpoint": "s3.example.com",
        }
    ) == ("reports", "s3.example.com", "api-prod", "https://git.example/api")
