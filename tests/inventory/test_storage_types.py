from kmap.inventory.storage_types import storage_type_label, storage_type_rules_from_config


def test_storage_type_label_uses_first_configured_match():
    assert (
        storage_type_label(
            endpoint="reports.ceph-primary.example.com",
            bucket="reports",
            source_var="S3_ENDPOINT",
            storage_type_rules=[
                {"match": "ceph-primary", "label": "Ceph New"},
                {"match": "ceph", "label": "Ceph Old"},
            ],
        )
        == "Ceph New"
    )


def test_storage_type_label_formats_named_match_groups():
    assert (
        storage_type_label(
            endpoint="s3.eu-central-1.amazonaws.com",
            bucket="reports",
            source_var="S3_ENDPOINT",
            storage_type_rules=[{"match": r"s3[.-](?P<region>[a-z0-9-]+)[.]amazonaws[.]com", "label": "S3 ({region})"}],
        )
        == "S3 (eu-central-1)"
    )


def test_storage_type_label_falls_back_when_configured_label_format_is_invalid():
    assert (
        storage_type_label(
            endpoint="reports.ceph-primary.example.com",
            bucket="reports",
            source_var="S3_ENDPOINT",
            storage_type_rules=[{"match": "ceph-primary", "label": "Ceph {missing}"}],
        )
        == "Ceph {missing}"
    )
    assert (
        storage_type_label(
            endpoint="reports.ceph-primary.example.com",
            bucket="reports",
            source_var="S3_ENDPOINT",
            storage_type_rules=[{"match": "ceph-primary", "label": "Ceph {region"}],
        )
        == "Ceph {region"
    )


def test_storage_type_label_uses_builtin_fallbacks():
    assert storage_type_label(endpoint="auth.servers.com", bucket="files", source_var="FILES_OS_AUTH_URL") == (
        "Servers.com"
    )
    assert storage_type_label(endpoint="s3.us-east-1.amazonaws.com", bucket="reports", source_var="S3_ENDPOINT") == (
        "S3 (us-east-1)"
    )
    assert storage_type_label(endpoint="storage.openstack.example", bucket="files", source_var="OS_AUTH_URL") == (
        "OpenStack"
    )
    assert storage_type_label(endpoint="reports.ceph.example.com", bucket="reports", source_var="S3_ENDPOINT") == "Ceph"
    assert storage_type_label(endpoint="minio.internal", bucket="reports", source_var="S3_ENDPOINT") == "MinIO"
    assert storage_type_label(endpoint="bucket.s3.internal", bucket="reports", source_var="S3_ENDPOINT") == "S3"
    assert storage_type_label(endpoint="", bucket="", source_var="") == ""


def test_storage_type_rules_from_config_reads_inventory_rules():
    assert storage_type_rules_from_config(
        {"inventory": {"storage_type_labels": [{"match": "ceph-primary", "label": "Ceph New"}, "ignored", None]}}
    ) == [{"match": "ceph-primary", "label": "Ceph New"}]


def test_storage_type_rules_from_config_stringifies_values_and_handles_missing_config():
    assert storage_type_rules_from_config({"inventory": {"storage_type_labels": [{"match": 123, "label": 456}]}}) == [
        {"match": "123", "label": "456"}
    ]
    assert storage_type_rules_from_config(None) == []
