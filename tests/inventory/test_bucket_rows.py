from kmap.inventory.bucket_rows import (
    BucketUsageRow,
    best_confidence,
    bucket_row_dict,
    bucket_rows_for_report,
    bucket_rows_from_artifact,
    looks_like_false_positive_bucket,
    looks_like_object_storage_endpoint,
    merge_bucket_usage_rows,
    workload_bucket_rows,
)
from kmap.inventory.namespaces import InventoryRow


def test_workload_bucket_rows_prefers_bucket_candidates_and_falls_back_to_dependencies():
    assert workload_bucket_rows(
        {
            "bucket_candidates": [
                {
                    "source": "Env",
                    "var": "S3_BUCKET",
                    "bucket": "reports",
                    "endpoint": "",
                    "confidence": "high",
                }
            ],
            "dependency_candidates": [{"var": "S3_BUCKET", "key": "ignored.s3.example.com"}],
        }
    ) == [
        {
            "source": "Env",
            "var": "S3_BUCKET",
            "bucket": "reports",
            "endpoint": "",
            "confidence": "high",
        }
    ]

    fallback = workload_bucket_rows(
        {
            "dependency_candidates": [
                {
                    "source": "VaultEnv",
                    "source_name": "runtime",
                    "var": "MESSAGES_HUB_S3_HOST_BUCKET",
                    "key": "media.s3.example.com",
                }
            ]
        }
    )

    assert fallback[0]["bucket"] == "media"
    assert fallback[0]["endpoint"] == "media.s3.example.com"


def test_bucket_rows_for_report_joins_inventory_metadata():
    rows = bucket_rows_for_report(
        {
            "cluster": "ctx",
            "namespace": "payments",
            "workloads": [
                {
                    "cluster": "ctx",
                    "namespace": "payments",
                    "project": "pay",
                    "service_name": "api",
                    "bucket_candidates": [
                        {
                            "source": "Env",
                            "var": "S3_BUCKET",
                            "bucket": "reports",
                            "endpoint": "",
                            "confidence": "high",
                        }
                    ],
                }
            ],
        },
        {
            ("ctx", "payments"): InventoryRow(
                cluster="ctx",
                product="demo",
                product_title="Demo Product",
                namespace="payments",
                repository="https://git.example/pay",
                owner_team="Ops",
            )
        },
    )

    assert rows == [
        BucketUsageRow(
            bucket="reports",
            endpoint="",
            confidence="high",
            cluster="ctx",
            product="demo",
            namespace="payments",
            project="pay",
            workload="api",
            source="Env",
            source_var="S3_BUCKET",
            repository="https://git.example/pay",
            owner_team="Ops",
            product_title="Demo Product",
        )
    ]


def test_bucket_row_dict_keeps_repository_and_owner_metadata():
    assert bucket_row_dict(
        BucketUsageRow(
            bucket="reports",
            endpoint="",
            confidence="high",
            cluster="ctx",
            product="demo",
            namespace="payments",
            project="pay",
            workload="api",
            source="Env",
            source_var="S3_BUCKET",
            repository="https://git.example/pay",
            owner_team="Ops",
            product_title="Demo Product",
        )
    ) == {
        "bucket": "reports",
        "endpoint": "",
        "confidence": "high",
        "cluster": "ctx",
        "product": "demo",
        "namespace": "payments",
        "project": "pay",
        "workload": "api",
        "source": "Env",
        "source_var": "S3_BUCKET",
        "repository": "https://git.example/pay",
        "owner_team": "Ops",
        "report_key": "",
        "product_title": "Demo Product",
    }


def test_bucket_rows_from_artifact_enriches_endpoint_and_falls_back_to_item_metadata():
    rows = bucket_rows_from_artifact(
        {
            "schema_version": 1,
            "report_key": "demo",
            "product": "demo-product",
            "rows": [
                {
                    "bucket": "",
                    "endpoint": "main-bucket.ceph.example.internal",
                    "confidence": "low",
                    "cluster": "ctx",
                    "namespace": "payments",
                    "project": "pay",
                    "workload": "api",
                    "source": "Env",
                    "source_var": "PPROF_DUMPER_S3_ENDPOINT_URL",
                    "repository": "https://git.example/pay",
                    "owner_team": "Ops",
                    "product_title": "Demo Product",
                }
            ],
        },
        {},
        fallback_report_key="fallback",
    )

    assert rows == [
        BucketUsageRow(
            bucket="main-bucket",
            endpoint="main-bucket.ceph.example.internal",
            confidence="medium",
            cluster="ctx",
            product="demo-product",
            namespace="payments",
            project="pay",
            workload="api",
            source="Env",
            source_var="PPROF_DUMPER_S3_ENDPOINT_URL",
            repository="https://git.example/pay",
            owner_team="Ops",
            report_key="demo",
            product_title="Demo Product",
        )
    ]


def test_bucket_rows_from_artifact_prefers_inventory_metadata():
    inventory = {
        ("ctx", "payments"): InventoryRow(
            cluster="ctx",
            product="inventory-product",
            product_title="Inventory Product",
            namespace="payments",
            repository="https://git.example/inventory",
            owner_team="Inventory Ops",
        )
    }

    rows = bucket_rows_from_artifact(
        {
            "schema_version": 1,
            "rows": [
                {
                    "bucket": "reports",
                    "endpoint": "",
                    "confidence": "high",
                    "cluster": "ctx",
                    "namespace": "payments",
                    "repository": "https://git.example/item",
                    "owner_team": "Item Ops",
                }
            ],
        },
        inventory,
        fallback_report_key="fallback",
    )

    assert rows[0].product == "inventory-product"
    assert rows[0].repository == "https://git.example/inventory"
    assert rows[0].owner_team == "Inventory Ops"
    assert rows[0].report_key == "fallback"


def test_bucket_signal_helpers_and_merge_precedence():
    assert looks_like_false_positive_bucket("prod") is True
    assert looks_like_false_positive_bucket("1.2.3") is True
    assert looks_like_false_positive_bucket("reports") is False
    assert looks_like_object_storage_endpoint("minio.internal") is True
    assert looks_like_object_storage_endpoint("api.internal") is False
    assert best_confidence("low", "high") == "high"

    rows = merge_bucket_usage_rows(
        [
            BucketUsageRow(
                bucket="reports",
                endpoint="",
                confidence="low",
                cluster="ctx",
                product="demo",
                namespace="payments",
                project="pay",
                workload="api",
                source="Env",
                source_var="S3_BUCKET_NAME",
                repository="https://git.example/pay",
                owner_team="Ops",
            ),
            BucketUsageRow(
                bucket="reports",
                endpoint="reports.s3.example.com",
                confidence="high",
                cluster="ctx",
                product="demo",
                namespace="payments",
                project="pay",
                workload="api",
                source="Env",
                source_var="S3_HOST_BUCKET",
                repository="https://git.example/pay",
                owner_team="Ops",
            ),
        ]
    )

    assert len(rows) == 1
    assert rows[0].endpoint == "reports.s3.example.com"
    assert rows[0].confidence == "high"
    assert rows[0].source_var == "S3_BUCKET_NAME, S3_HOST_BUCKET"
