from kmap.validators import unknown_key_errors, unknown_keys


def test_unknown_keys_returns_sorted_extra_keys():
    assert unknown_keys({"a": 1, "b": 2, "extra": 3}, {"a", "b"}) == ["extra"]


def test_unknown_key_errors_formats_path_and_label():
    config = {"enabled": True, "cache_file": "cache.json", "token": "secret"}
    errors = unknown_key_errors(
        config,
        {"enabled", "cache_file"},
        "inventory.repositories",
        "repositories config key",
    )
    assert errors == ["inventory.repositories.token: unknown repositories config key"]
