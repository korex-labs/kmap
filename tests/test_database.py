from kmap.database import clean_database_name, database_metadata_for_candidate, parse_database_url


def test_parse_database_url_extracts_jdbc_and_dsn_database_names():
    assert parse_database_url("jdbc:postgresql://pg.example.com:5432/app_db?ssl=true") == (
        "postgresql",
        "pg.example.com",
        ["app_db"],
    )
    assert parse_database_url("mysql://user:pass@mysql.example.com:3306/payments") == (
        "mysql",
        "mysql.example.com",
        ["payments"],
    )


def test_parse_database_url_handles_quoted_jdbc_and_hostish_fallbacks():
    assert parse_database_url("'jdbc:mysql://mysql.example.com:3306/orders'") == (
        "mysql",
        "mysql.example.com",
        ["orders"],
    )
    assert parse_database_url("postgresql://pg.example.com:5432") == (
        "postgresql",
        "pg.example.com",
        [],
    )


def test_parse_database_url_ignores_unknown_or_empty_values():
    assert parse_database_url("") == ("", None, [])
    assert parse_database_url("redis://redis.example.com/0") == ("", "redis.example.com", [])


def test_clean_database_name_rejects_placeholders_and_numeric_indexes():
    assert clean_database_name("/") == ""
    assert clean_database_name(".") == ""
    assert clean_database_name("..") == ""
    assert clean_database_name("0") == ""
    assert clean_database_name("orders/public") == "orders"


def test_database_metadata_for_candidate_uses_companion_database_vars():
    metadata = database_metadata_for_candidate(
        {
            "MYSQL_HOST": "mysql.example.com",
            "MYSQL_DATABASE": "wallet",
            "POSTGRES_DB": "ignored",
        },
        "MYSQL_HOST",
        "mysql.example.com",
        "mysql.example.com",
    )

    assert metadata == {
        "engine": "mysql",
        "names": ["wallet"],
        "source_vars": ["MYSQL_DATABASE"],
        "sources": ["companion_var"],
    }


def test_database_metadata_ignores_database_index_companion_vars():
    metadata = database_metadata_for_candidate(
        {
            "MYSQL_HOST": "mysql.example.com",
            "MYSQL_DATABASE": "wallet",
            "REDIS_DB": "0",
            "DB": "0",
        },
        "MYSQL_HOST",
        "mysql.example.com",
        "mysql.example.com",
    )

    assert metadata == {
        "engine": "mysql",
        "names": ["wallet"],
        "source_vars": ["MYSQL_DATABASE"],
        "sources": ["companion_var"],
    }
