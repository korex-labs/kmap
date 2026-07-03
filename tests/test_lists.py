from kmap.lists import (
    append_clean_unique,
    append_clean_unique_string,
    append_truthy_unique,
    append_unique,
)


def test_append_unique_keeps_first_occurrence():
    items = ["a"]
    append_unique(items, "a")
    append_unique(items, "b")
    assert items == ["a", "b"]


def test_append_truthy_unique_skips_falsy_values():
    items: list[str] = []
    append_truthy_unique(items, "")
    append_truthy_unique(items, "bucket")
    assert items == ["bucket"]


def test_append_clean_unique_normalizes_strings():
    items: list[str] = []
    append_clean_unique(items, "  demo  ")
    append_clean_unique(items, None)
    append_clean_unique(items, "   ")
    assert items == ["demo"]


def test_append_clean_unique_string_flattens_lists():
    items: list[str] = []
    append_clean_unique_string(items, [" alpha ", "beta"])
    append_clean_unique_string(items, " gamma ")
    assert items == ["alpha", "beta", "gamma"]
