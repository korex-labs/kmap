from kmap.external.mappings import (
    external_dependency_tag,
    external_mapping_configs,
    external_mapping_for_key,
    external_mapping_items,
    external_mapping_should_aggregate,
    generated_external_category,
    load_external_mapping_summaries,
    load_external_mappings,
    normalized_likec4_external_type,
)


def test_load_external_mappings_reads_product_and_common_files(tmp_path):
    config_dir = tmp_path / "config"
    common_dir = config_dir / "common"
    common_dir.mkdir(parents=True)
    product_config = config_dir / "product.yaml"
    product_config.write_text(
        """
external_mappings:
  - name: Redis
    match: [redis.local]
    element_type: Redis_DB
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (common_dir / "external_mappings.yaml").write_text(
        """
external_mappings:
  - name: Kafka
    match_regex: ['kafka[.]example']
    tag: Messaging
""".strip()
        + "\n",
        encoding="utf-8",
    )

    mappings = load_external_mappings(str(product_config))
    summaries = load_external_mapping_summaries(str(product_config))

    assert [item["name"] for item in mappings] == ["Redis", "Kafka"]
    assert external_mapping_for_key("redis.local:6379", mappings)["name"] == "Redis"
    assert external_mapping_for_key("kafka.example:9092", mappings)["name"] == "Kafka"
    assert [item["name"] for item in summaries] == ["Redis", "Kafka"]


def test_external_mapping_type_category_and_aggregate_defaults():
    assert normalized_likec4_external_type("Primary Redis", "Data") == "Redis_DB"
    assert generated_external_category("Kafka topic", "External System") == "Messaging"
    assert external_mapping_should_aggregate({"name": "Website", "tag": "External System"}) is False
    assert external_mapping_should_aggregate({"name": "Redis", "aggregate": "false"}) is False


def test_external_mapping_configs_and_items_handle_empty_and_malformed_inputs(tmp_path):
    assert external_mapping_configs(None) == []
    assert external_mapping_items(None) == []
    assert load_external_mappings(None) == []
    assert load_external_mapping_summaries(None) == []

    config = tmp_path / "product.yaml"
    config.write_text(
        """
external_mappings:
  - ignored-string
  - name: ""
    match: [ignored]
  - name: S3
    match: [" s3.example "]
    match_regex: ["[invalid", "files[.]example"]
    likec4_type: AWS_S3_Bucket
  - name: Empty Patterns
    match: ["", "   "]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    configs = external_mapping_configs(str(config))
    mappings = load_external_mappings(str(config))
    summaries = load_external_mapping_summaries(str(config))

    assert [source for source, _ in configs] == [str(config), str(tmp_path / "common" / "external_mappings.yaml")]
    assert [item["name"] for item in mappings] == ["S3", "Empty Patterns"]
    assert mappings[0]["patterns"] == ["s3.example"]
    assert len(mappings[0]["regexes"]) == 1
    assert mappings[0]["element_type"] == "AWS_S3_Bucket"
    assert external_mapping_for_key("", mappings) is None
    assert external_mapping_for_key("https://files.example/report", mappings)["name"] == "S3"
    assert summaries[0]["match"] == ["s3.example"]
    assert summaries[0]["match_regex"] == ["[invalid", "files[.]example"]


def test_external_type_detection_covers_known_external_kinds():
    cases = {
        "customer mobile app": "Mobile_App",
        "frontend vue.js": "VueJS_App",
        "payments-go": "GoLang_App",
        "legacy php": "PHP_App",
        "mysql primary": "MySQL_DB",
        "postgresql dwh": "PgSQL_DB",
        "mongo cluster": "Mongo_DB",
        "click house analytics": "ClickHouse_DB",
        "vault prod": "Vault",
        "kafka broker": "Kafka",
        "nats streaming": "NATS",
        "ory hydra": "Hydra_Consent",
        "gateway public": "External_API",
        "amazon s3 bucket": "AWS_S3_Bucket",
        "files.cloud.servers.com": "ServersCom_Object_Storage",
        "object storage": "bucket",
        "https://example.com": "Website",
        "unknown dependency": "system",
    }

    for name, expected_type in cases.items():
        assert normalized_likec4_external_type(name) == expected_type

    assert normalized_likec4_external_type("anything", configured_type="Redis_DB") == "Redis_DB"


def test_generated_external_category_and_aggregate_edge_cases():
    assert external_dependency_tag("anything") == "External System"
    assert generated_external_category("primary storage", "") == "Data"
    assert generated_external_category("redash prod", "") == "Monitoring"
    assert generated_external_category("plain dependency", "") == "External"
    assert external_mapping_should_aggregate(None) is False
    assert external_mapping_should_aggregate({"name": "website", "tag": "Website"}) is False
    assert external_mapping_should_aggregate({"name": "custom api", "tag": "External API"}) is True
