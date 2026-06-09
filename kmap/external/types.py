"""External dependency category and LikeC4 type inference."""

from typing import Tuple

from ..config import LIKEC4_EXTERNAL_ELEMENT_TYPES, clean_metadata_string

EXTERNAL_CATEGORY_TOKENS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("Messaging", ("kafka", "nats", "rabbit", "amqp", "topic", "queue")),
    (
        "Data",
        (
            "redis",
            "mysql",
            "postgres",
            "pgsql",
            "mongo",
            "clickhouse",
            "database",
            "bucket",
            "s3",
            "storage",
        ),
    ),
    ("Monitoring", ("redash", "grafana", "prometheus", "vmselect", "monitor")),
)

LIKEC4_EXTERNAL_TYPE_TOKENS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("Mobile_App", ("mobile app", "android", "ios", "iphone")),
    ("VueJS_App", ("vue", "vuejs", "vue.js")),
    ("GoLang_App", ("golang", "go lang", " go ", "-go", "_go")),
    ("PHP_App", ("php",)),
    ("Redis_DB", ("redis",)),
    ("MySQL_DB", ("mysql", "mariadb")),
    ("PgSQL_DB", ("postgres", "postgresql", "pgsql")),
    ("Mongo_DB", ("mongo",)),
    ("ClickHouse_DB", ("clickhouse", "click house", "database (ch)", " ch ")),
    ("Vault", ("vault",)),
    ("Kafka", ("kafka",)),
    ("NATS", ("nats",)),
    ("Hydra_Consent", ("hydra consent", "hydra-consent", "hydra_consent", "ory hydra")),
    ("External_API", ("external api", "api.", "-api", "_api", " api ", "api/", "gateway", "payment")),
    ("AWS_S3_Bucket", ("amazon s3", "aws s3", ".s3.", "s3.")),
    (
        "ServersCom_Object_Storage",
        ("servers.com object storage", "servers com object storage", ".cloud.servers.com", "files."),
    ),
    ("bucket", ("s3", "bucket", "object storage")),
    ("Website", ("website", "http://", "https://", ".com", ".net", ".org")),
)


def generated_external_category(name: str, tag: str = "") -> str:
    raw = f"{name} {tag}".lower()
    for category, tokens in EXTERNAL_CATEGORY_TOKENS:
        if any(token in raw for token in tokens):
            return category
    return "External"


def normalized_likec4_external_type(name: str, tag: str = "", configured_type: str = "") -> str:
    explicit = clean_metadata_string(configured_type)
    if explicit in LIKEC4_EXTERNAL_ELEMENT_TYPES:
        return explicit

    raw = f"{name} {tag}".lower()
    for element_type, tokens in LIKEC4_EXTERNAL_TYPE_TOKENS:
        if any(token in raw for token in tokens):
            return element_type
    return "system"


__all__ = [
    "EXTERNAL_CATEGORY_TOKENS",
    "LIKEC4_EXTERNAL_TYPE_TOKENS",
    "generated_external_category",
    "normalized_likec4_external_type",
]
