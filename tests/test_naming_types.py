from kmap.naming.types import generated_system_category, normalized_likec4_internal_system_type


def test_generated_system_category_classifies_common_operational_roles():
    assert generated_system_category("blackbox exporter") == "Monitoring"
    assert generated_system_category("orders topic") == "Messaging"
    assert generated_system_category("payments postgres") == "Data"
    assert generated_system_category("payment gateway") == "Gateway"
    assert generated_system_category("nightly scheduler") == "Support"
    assert generated_system_category("checkout") == "App"


def test_normalized_likec4_internal_system_type_matches_known_technology_tokens():
    assert normalized_likec4_internal_system_type("customer mobile app") == "Mobile_App"
    assert normalized_likec4_internal_system_type("frontend vue.js") == "VueJS_App"
    assert normalized_likec4_internal_system_type("orders-go") == "GoLang_App"
    assert normalized_likec4_internal_system_type("legacy php") == "PHP_App"
    assert normalized_likec4_internal_system_type("ory hydra consent") == "Hydra_Consent"
    assert normalized_likec4_internal_system_type("payments gateway") == "API"
    assert normalized_likec4_internal_system_type("session redis") == "Redis_DB"
    assert normalized_likec4_internal_system_type("orders mariadb") == "MySQL_DB"
    assert normalized_likec4_internal_system_type("analytics pgsql") == "PgSQL_DB"
    assert normalized_likec4_internal_system_type("profiles mongo") == "Mongo_DB"
    assert normalized_likec4_internal_system_type("events click house") == "ClickHouse_DB"
    assert normalized_likec4_internal_system_type("files object storage") == "bucket"
    assert normalized_likec4_internal_system_type("prod nats") == "NATS"
    assert normalized_likec4_internal_system_type("plain service") == "system"
