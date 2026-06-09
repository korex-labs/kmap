from kmap.inspection.bucket_dedup import (
    bucket_candidate_dedupe_key,
    bucket_candidate_family,
    bucket_candidate_group_key,
    bucket_candidate_quality,
    bucket_candidate_sort_key,
    bucket_candidate_source_rank,
    dedupe_bucket_candidates,
    grouped_bucket_candidates,
    merge_bucket_candidate_group,
    merged_bucket_candidate,
    remaining_bucket_candidates,
)
from kmap.inspection.bucket_detection import (
    bucket_candidate_from_pair,
    bucket_candidates_from_map,
    bucket_confidence,
    bucket_endpoint_data,
    bucket_from_endpoint_or_value,
    bucket_from_host,
    bucket_from_path,
    bucket_from_plain_value,
    is_bucket_candidate_signal,
    looks_like_bucket_name,
    looks_like_object_storage_endpoint,
    should_consider_bucket_pair,
    should_parse_bucket_endpoint,
)
from kmap.inspection.bucket_sanitization import sanitize_bucket_candidate
from kmap.inspection.buckets import (
    bucket_candidates_from_sources,
    container_literal_bucket_env,
    referenced_configmap_bucket_values,
    referenced_secret_bucket_values,
    workload_bucket_candidates,
)


def test_bucket_candidate_from_pair_extracts_plain_and_virtual_hosted_buckets():
    assert bucket_candidate_from_pair("S3_BUCKET", "reports-prod", "Env", "spec") == {
        "source": "Env",
        "source_name": "spec",
        "var": "S3_BUCKET",
        "bucket": "reports-prod",
        "endpoint": "",
        "confidence": "high",
    }
    assert bucket_candidate_from_pair(
        "MESSAGES_HUB_S3_HOST_BUCKET",
        "demo-mediafiles-prod.s3.eu-central-1.amazonaws.com",
        "VaultEnv",
        "runtime",
    ) == {
        "source": "VaultEnv",
        "source_name": "runtime",
        "var": "MESSAGES_HUB_S3_HOST_BUCKET",
        "bucket": "demo-mediafiles-prod",
        "endpoint": "demo-mediafiles-prod.s3.eu-central-1.amazonaws.com",
        "confidence": "high",
    }


def test_bucket_candidate_from_pair_extracts_endpoint_without_bucket_with_low_confidence():
    assert bucket_candidate_from_pair("S3_ENDPOINT_URL", "https://s3.eu-central-1.amazonaws.com", "Env", "spec") == {
        "source": "Env",
        "source_name": "spec",
        "var": "S3_ENDPOINT_URL",
        "bucket": "",
        "endpoint": "s3.eu-central-1.amazonaws.com",
        "confidence": "low",
    }


def test_bucket_candidate_from_pair_accepts_long_ceph_bucket_names():
    assert bucket_candidate_from_pair(
        "S3_PRIVATE_BUCKET",
        "example-kube-web-portal-api-4639-portal-api-web-private",
        "VaultEnv",
        "runtime",
    ) == {
        "source": "VaultEnv",
        "source_name": "runtime",
        "var": "S3_PRIVATE_BUCKET",
        "bucket": "example-kube-web-portal-api-4639-portal-api-web-private",
        "endpoint": "",
        "confidence": "high",
    }


def test_bucket_candidate_from_pair_filters_numeric_noise_and_extracts_bucket_host_prefix():
    assert bucket_candidate_from_pair("S3_BUCKET", "9000", "Env", "spec") == {}
    assert bucket_candidate_from_pair("S3_BUCKET", "10.1.2.3", "Env", "spec") == {}
    assert bucket_candidate_from_pair("PPROF_DUMPER_S3_BUCKET_NAME", "prod", "Env", "spec") == {}
    assert bucket_candidate_from_pair("MAIN_BUCKET_PORT_9000_TCP_PROTO", "tcp", "Env", "spec") == {}
    assert bucket_candidate_from_pair("S3_ENDPOINT_URL", "https://api.internal:9000", "Env", "spec") == {}
    assert bucket_candidate_from_pair(
        "PPROF_DUMPER_S3_ENDPOING_URL",
        "https://main-bucket.ceph.example.internal",
        "Env",
        "runtime",
    ) == {
        "source": "Env",
        "source_name": "runtime",
        "var": "PPROF_DUMPER_S3_ENDPOING_URL",
        "bucket": "main-bucket",
        "endpoint": "main-bucket.ceph.example.internal",
        "confidence": "medium",
    }


def test_bucket_predicate_and_extraction_helpers_cover_edge_shapes():
    assert should_consider_bucket_pair("S3_BUCKET", "reports") is True
    assert should_consider_bucket_pair("S3_SECRET_KEY", "reports") is False
    assert should_consider_bucket_pair("MAIN_BUCKET_PORT_9000_TCP_PROTO", "tcp") is False
    assert should_parse_bucket_endpoint("S3_ENDPOINT_URL", "s3.example.com") is True
    assert should_parse_bucket_endpoint("S3_BUCKET", "reports") is False

    endpoint_data = bucket_endpoint_data("S3_ENDPOINT_URL", "https://reports.s3.example.com/path")
    assert endpoint_data == {
        "host": "reports.s3.example.com",
        "port": None,
        "path": "/path",
        "endpoint": "reports.s3.example.com",
    }
    assert bucket_from_endpoint_or_value(endpoint_data, "reports", "S3_BUCKET") == "reports"
    assert bucket_from_host("reports.s3.example.com") == "reports"
    assert bucket_from_path("/reports/prefix", "S3_BUCKET") == "reports"
    assert bucket_from_plain_value("reports", "S3_BUCKET") == "reports"
    assert bucket_from_plain_value("https://reports.s3.example.com", "S3_BUCKET") == ""


def test_bucket_signal_confidence_and_name_helpers_reject_noise():
    assert is_bucket_candidate_signal("reports", "") is True
    assert is_bucket_candidate_signal("", "s3.example.com") is True
    assert is_bucket_candidate_signal("", "api.internal") is False
    assert looks_like_object_storage_endpoint("https://minio.example.com") is True
    assert looks_like_bucket_name("reports-prod") is True
    assert looks_like_bucket_name("10.1.2.3") is False
    assert looks_like_bucket_name("prod") is False
    assert bucket_confidence("S3_BUCKET", "reports", "") == "high"
    assert bucket_confidence("S3_HOST", "reports", "") == "medium"
    assert bucket_confidence("S3_ENDPOINT_URL", "", "s3.example.com") == "low"


def test_bucket_candidates_from_map_filters_sensitive_keys():
    rows = bucket_candidates_from_map(
        {
            "S3_BUCKET": "reports",
            "S3_ACCESS_KEY": "not-a-bucket",
            "MODE": "ignored",
        },
        "Env",
        "spec",
    )

    assert [row["bucket"] for row in rows] == ["reports"]


def test_bucket_source_value_helpers_collect_referenced_data_in_sorted_order():
    assert referenced_configmap_bucket_values(
        {"b-config", "a-config"},
        {
            "a-config": {"data": {"S3_BUCKET": "reports"}},
            "b-config": {"data": {"S3_ENDPOINT_URL": "https://s3.example.com"}},
        },
    ) == {"S3_BUCKET": "reports", "S3_ENDPOINT_URL": "https://s3.example.com"}
    assert referenced_secret_bucket_values(
        {"api-secret"},
        {"api-secret": {"data": {"CEPH_BUCKET": "YXJjaGl2ZQ=="}}},
    ) == {"CEPH_BUCKET": "archive"}
    assert container_literal_bucket_env(
        [
            {"env": [{"name": "S3_BUCKET", "value": "reports"}]},
            {"env": [{"name": "CEPH_BUCKET", "value": "archive"}]},
        ]
    ) == {"S3_BUCKET": "reports", "CEPH_BUCKET": "archive"}


def test_bucket_candidates_from_sources_preserves_source_order():
    rows = bucket_candidates_from_sources(
        [
            ({"S3_BUCKET": "reports"}, "ConfigMap", "app-config"),
            ({"CEPH_BUCKET": "archive"}, "VaultEnv", "runtime"),
        ]
    )

    assert [(row["source"], row["source_name"], row["bucket"]) for row in rows] == [
        ("ConfigMap", "app-config", "reports"),
        ("VaultEnv", "runtime", "archive"),
    ]


def test_bucket_dedupe_helpers_define_source_precedence_and_identity():
    configmap_candidate = {
        "source": "ConfigMap",
        "source_name": "app-config",
        "var": "S3_BUCKET",
        "bucket": "reports",
        "endpoint": "",
        "confidence": "high",
    }
    runtime_candidate = {
        **configmap_candidate,
        "source": "Env",
        "source_name": "runtime",
    }

    assert bucket_candidate_dedupe_key(configmap_candidate) == ("S3_BUCKET", "reports", "")
    assert bucket_candidate_sort_key(configmap_candidate) == ("reports", "", "S3_BUCKET")
    assert bucket_candidate_source_rank(runtime_candidate) > bucket_candidate_source_rank(configmap_candidate)
    assert dedupe_bucket_candidates([configmap_candidate, runtime_candidate]) == [runtime_candidate]


def test_workload_bucket_candidates_collects_all_sources_and_dedupes_by_source_rank():
    rows = workload_bucket_candidates(
        containers=[
            {
                "env": [
                    {"name": "S3_BUCKET", "value": "reports"},
                    {"name": "FROM_CM", "valueFrom": {"configMapKeyRef": {"name": "app-config"}}},
                ]
            }
        ],
        referenced_configmaps={"app-config"},
        referenced_secrets={"app-secret"},
        configmaps={"app-config": {"data": {"S3_ENDPOINT_URL": "https://s3.example.com"}}},
        secrets={"app-secret": {"data": {"S3_BUCKET": "cmVwb3J0cw=="}}},
        runtime_env={"S3_BUCKET": "reports"},
        vault_env={"CEPH_BUCKET": "archive"},
    )

    by_var = {row["var"]: row for row in rows}
    assert sorted(by_var) == ["CEPH_BUCKET", "S3_BUCKET", "S3_ENDPOINT_URL"]
    assert by_var["S3_BUCKET"]["source"] == "Env"
    assert by_var["S3_ENDPOINT_URL"]["endpoint"] == "s3.example.com"
    assert by_var["CEPH_BUCKET"]["bucket"] == "archive"


def test_workload_bucket_candidates_merges_openstack_bucket_with_auth_url():
    rows = workload_bucket_candidates(
        containers=[
            {
                "env": [
                    {"name": "FILES_OS_BUCKET_NAME", "value": "payment-files"},
                    {"name": "FILES_OS_AUTH_URL", "value": "https://auth.servers.com/v3"},
                ]
            }
        ],
        referenced_configmaps=set(),
        referenced_secrets=set(),
        configmaps={},
        secrets={},
        runtime_env={},
        vault_env={},
    )

    assert rows == [
        {
            "source": "Env",
            "source_name": "spec",
            "var": "FILES_OS_AUTH_URL, FILES_OS_BUCKET_NAME",
            "bucket": "payment-files",
            "endpoint": "auth.servers.com",
            "confidence": "high",
        }
    ]


def test_bucket_grouping_helpers_split_mergeable_and_passthrough_candidates():
    mergeable = {
        "source": "Env",
        "source_name": "spec",
        "var": "FILES_OS_BUCKET_NAME",
        "bucket": "payment-files",
        "endpoint": "",
    }
    endpoint = {
        "source": "Env",
        "source_name": "spec",
        "var": "FILES_OS_AUTH_URL",
        "bucket": "",
        "endpoint": "auth.servers.com",
    }
    passthrough = {"source": "Env", "source_name": "spec", "var": "BUCKET", "bucket": "reports", "endpoint": ""}

    grouped, passthrough_rows = grouped_bucket_candidates([mergeable, endpoint, passthrough])

    assert bucket_candidate_group_key(mergeable) == ("Env", "spec", "FILES_OS")
    assert bucket_candidate_group_key(passthrough) == ()
    assert grouped == {("Env", "spec", "FILES_OS"): [mergeable, endpoint]}
    assert passthrough_rows == [passthrough]
    assert bucket_candidate_family("FILES_OS_AUTH_URL") == "FILES_OS"


def test_bucket_merge_helpers_combine_best_pair_and_keep_remaining_candidates():
    best_bucket = {
        "source": "Env",
        "source_name": "spec",
        "var": "FILES_OS_BUCKET_NAME",
        "bucket": "payment-files",
        "endpoint": "",
        "confidence": "high",
    }
    best_endpoint = {
        "source": "Env",
        "source_name": "spec",
        "var": "FILES_OS_AUTH_URL",
        "bucket": "",
        "endpoint": "auth.servers.com",
        "confidence": "low",
    }
    remaining = {
        "source": "Env",
        "source_name": "spec",
        "var": "FILES_OTHER_BUCKET",
        "bucket": "other-files",
        "endpoint": "",
        "confidence": "high",
    }
    expected = {
        "source": "Env",
        "source_name": "spec",
        "var": "FILES_OS_AUTH_URL, FILES_OS_BUCKET_NAME",
        "bucket": "payment-files",
        "endpoint": "auth.servers.com",
        "confidence": "high",
    }

    assert merged_bucket_candidate(best_bucket, best_endpoint) == expected
    assert bucket_candidate_quality(best_bucket) == (1, 0)
    assert bucket_candidate_quality(best_endpoint) == (0, 1)
    assert remaining_bucket_candidates(
        [best_bucket, best_endpoint, remaining], {id(best_bucket), id(best_endpoint)}
    ) == [remaining]
    assert merge_bucket_candidate_group([best_bucket, best_endpoint, remaining]) == [expected, remaining]


def test_sanitize_bucket_candidate_redacts_secret_source_and_mocks_values():
    candidate = {
        "source": "Secret",
        "source_name": "app-secret",
        "var": "S3_BUCKET",
        "bucket": "reports",
        "endpoint": "reports.s3.example.com",
        "confidence": "high",
    }

    sanitized = sanitize_bucket_candidate(candidate, "sanitized")
    assert sanitized["source_name"] == "referenced"
    assert sanitized["bucket"] == "reports"

    mocked = sanitize_bucket_candidate(candidate, "mocked", "seed")
    assert mocked["source_name"] == "referenced"
    assert mocked["var"] != "S3_BUCKET"
    assert mocked["bucket"] != "reports"
    assert mocked["endpoint"] != "reports.s3.example.com"
