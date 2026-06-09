from kmap.render.markdown import markdown_escape, markdown_table, short_join


def test_markdown_escape_replaces_pipes_and_newlines():
    assert markdown_escape("left|right\nnext") == "left\\|right next"


def test_markdown_table_wraps_long_cells_and_uses_placeholder_for_empty_rows():
    table = markdown_table(
        ["Name", "Description"],
        [["api", "very long description"]],
        max_widths=[8, 10],
        max_table_width=40,
    )

    assert table[0] == "| Name | Description |"
    assert "| api  | very long   |" in table
    assert "|      | description |" in table

    empty = markdown_table(["Only"], [])
    assert empty == ["| Only |", "| ---- |", "| -    |"]


def test_markdown_table_normalizes_row_lengths_and_width_limits():
    table = markdown_table(
        ["First", "Second"],
        [["one", "two", "ignored"], ["solo"]],
        max_widths=[0, 9],
        max_table_width=24,
    )

    assert "ignored" not in "\n".join(table)
    assert "| solo  | -      |" in table
    assert all(len(line) <= 24 for line in table)


def test_markdown_table_wraps_long_words_when_fitting_table_width():
    table = markdown_table(
        ["Identifier", "Description"],
        [["verylongidentifier", "compact"]],
        max_widths=[20, 20],
        max_table_width=30,
    )

    assert any("verylongiden" in line for line in table)
    assert any("tifier" in line for line in table)
    assert all(len(line) <= 30 for line in table)


def test_short_join_deduplicates_case_insensitively_and_applies_limit():
    assert short_join(["A", "a", "", None, "B", "C"], limit=2) == "A, B, +1 more"


def test_short_join_returns_all_unique_values_when_under_limit():
    assert short_join(["A", "b", "a"], limit=5) == "A, b"
