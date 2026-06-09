"""Generated system category and LikeC4 type inference."""

from typing import Tuple

INTERNAL_SYSTEM_TYPE_TOKENS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("Mobile_App", ("mobile app", "android", "ios", "iphone")),
    ("VueJS_App", ("vue", "vuejs", "vue.js")),
    ("GoLang_App", ("golang", "go lang", " go ", "-go", "_go")),
    ("PHP_App", ("php",)),
    ("Hydra_Consent", ("hydra consent", "hydra-consent", "hydra_consent", "ory hydra")),
    ("API", (" api", "-api", "_api", "gateway", "proxy")),
    ("Redis_DB", ("redis",)),
    ("MySQL_DB", ("mysql", "mariadb")),
    ("PgSQL_DB", ("postgres", "postgresql", "pgsql")),
    ("Mongo_DB", ("mongo",)),
    ("ClickHouse_DB", ("clickhouse", "click house")),
    ("bucket", ("bucket", "minio", "object storage")),
    ("NATS", ("nats",)),
)


def generated_system_category(name: str, project_name: str = "") -> str:
    raw = f"{name} {project_name}".lower()
    if any(token in raw for token in ("monitor", "exporter", "blackbox", "prometheus", "grafana", "redash")):
        return "Monitoring"
    if any(token in raw for token in ("kafka", "nats", "rabbit", "amqp", "topic", "queue")):
        return "Messaging"
    if any(
        token in raw
        for token in ("redis", "mysql", "postgres", "pgsql", "mongo", "clickhouse", "bucket", "minio", "s3")
    ):
        return "Data"
    if any(token in raw for token in ("gateway", "proxy", "balancer", "ingress", "nginx")):
        return "Gateway"
    if any(token in raw for token in ("scheduler", "cron", "worker", "admin", "bot")):
        return "Support"
    return "App"


def normalized_likec4_internal_system_type(name: str, project_name: str = "") -> str:
    raw = name.lower()
    for element_type, tokens in INTERNAL_SYSTEM_TYPE_TOKENS:
        if any(token in raw for token in tokens):
            return element_type
    return "system"


__all__ = [
    "INTERNAL_SYSTEM_TYPE_TOKENS",
    "generated_system_category",
    "normalized_likec4_internal_system_type",
]
