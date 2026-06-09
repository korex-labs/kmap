"""Markdown table rendering helpers."""

import textwrap
from typing import Any, Iterable, List, Optional

from ...config import clean_metadata_string


def markdown_escape(value: Any) -> str:
    text = clean_metadata_string(value)
    if not text:
        return ""
    return text.replace("|", "\\|").replace("\n", " ")


def markdown_table(
    headers: List[str],
    rows: List[List[Any]],
    max_widths: Optional[List[int]] = None,
    max_table_width: int = 118,
) -> List[str]:
    escaped_headers = [markdown_escape(header) or "-" for header in headers]
    normalized_rows = _normalized_table_rows(headers, rows)
    widths = _markdown_table_widths(escaped_headers, normalized_rows, max_widths, max_table_width)

    def padded_row(values: List[str]) -> str:
        return "| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(values)) + " |"

    lines = [
        padded_row(escaped_headers),
        "| " + " | ".join("-" * widths[index] for index in range(len(widths))) + " |",
    ]
    lines.extend(padded_row(wrapped) for row in normalized_rows for wrapped in _wrapped_table_row(row, widths))
    return lines


def _normalized_table_rows(headers: List[str], rows: List[List[Any]]) -> List[List[str]]:
    normalized_rows = []
    for row in rows or []:
        normalized = list(row)[: len(headers)]
        normalized.extend([""] * (len(headers) - len(normalized)))
        normalized_rows.append([markdown_escape(cell) or "-" for cell in normalized])
    return normalized_rows or [["-" for _ in headers]]


def _markdown_table_widths(
    escaped_headers: List[str],
    normalized_rows: List[List[str]],
    max_widths: Optional[List[int]],
    max_table_width: int,
) -> List[int]:
    min_col_width = 8
    widths = [
        max(len(escaped_headers[index]), *(len(row[index]) for row in normalized_rows))
        for index in range(len(escaped_headers))
    ]
    if max_widths:
        for index, max_width in enumerate(max_widths[: len(widths)]):
            if not max_width:
                continue
            min_width = max(len(escaped_headers[index]), min_col_width)
            widths[index] = min(widths[index], max(min_width, int(max_width)))
    return _fit_markdown_table_widths(widths, escaped_headers, min_col_width, max_table_width)


def _fit_markdown_table_widths(
    widths: List[int],
    escaped_headers: List[str],
    min_col_width: int,
    max_table_width: int,
) -> List[int]:
    total_width = sum(widths) + (3 * len(widths)) + 1
    overflow = total_width - max_table_width
    if overflow <= 0:
        return widths

    for index in sorted(range(len(widths)), key=lambda i: widths[i], reverse=True):
        if overflow <= 0:
            break
        reducible = max(0, widths[index] - max(len(escaped_headers[index]), min_col_width))
        if reducible <= 0:
            continue
        reduction = min(reducible, overflow)
        widths[index] -= reduction
        overflow -= reduction
    return widths


def _wrapped_table_row(values: List[str], widths: List[int]) -> List[List[str]]:
    wrapped_columns = [
        textwrap.wrap(
            value,
            width=widths[index],
            break_long_words=True,
            break_on_hyphens=False,
        )
        or [""]
        for index, value in enumerate(values)
    ]
    row_count = max(len(column) for column in wrapped_columns)
    return [
        [
            wrapped_columns[index][row_index] if row_index < len(wrapped_columns[index]) else ""
            for index in range(len(values))
        ]
        for row_index in range(row_count)
    ]


def short_join(values: Iterable[Any], limit: int = 5) -> str:
    cleaned = [clean_metadata_string(value) for value in values if clean_metadata_string(value)]
    unique = []
    seen = set()
    for value in cleaned:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(value)
    if len(unique) <= limit:
        return ", ".join(unique)
    return ", ".join(unique[:limit]) + f", +{len(unique) - limit} more"


__all__ = [
    "markdown_escape",
    "markdown_table",
    "short_join",
]
