"""Shared HTML helpers for inventory pages."""

from dataclasses import dataclass
from datetime import datetime
from html import escape

from .html_filter import render_filter_script
from .html_styles import BASE_PAGE_STYLES


@dataclass(frozen=True)
class InventoryPageContext:
    page_title: str
    summary: str
    generated_at: datetime | None
    nav_links: list[tuple[str, str]]
    extra_styles: list[str]
    stats: list[tuple[int, str]]
    stats_label: str
    filter_id: str
    filter_placeholder: str
    table_id: str
    empty_id: str
    empty_text: str
    table_header: str
    table_rows: list[str]
    generated_class: str = "summary generated"
    repository_archive_filter: bool = False


def render_nav(links: list[tuple[str, str]]) -> str:
    return "<nav>" + "".join(f'<a href="{escape(href)}">{escape(label)}</a>' for href, label in links) + "</nav>"


def generated_label(generated_at: datetime | None) -> str:
    return generated_at.strftime("%Y-%m-%d %H:%M:%S %Z") if generated_at else ""


def render_stats_cards(stats: list[tuple[int, str]], *, aria_label: str) -> list[str]:
    lines = [f'    <section class="stats" aria-label="{escape(aria_label)}">']
    lines.extend(
        f'      <div class="stat"><strong>{value}</strong><span>{escape(label)}</span></div>' for value, label in stats
    )
    lines.append("    </section>")
    return lines


def render_inventory_page(**page_options: object) -> str:
    return render_inventory_page_context(inventory_page_context(page_options))


def inventory_page_context(page_options: dict[str, object]) -> InventoryPageContext:
    context = page_options.get("page_context")
    if isinstance(context, InventoryPageContext):
        return context
    return InventoryPageContext(
        page_title=str(page_options["page_title"]),
        summary=str(page_options["summary"]),
        generated_at=page_options["generated_at"],
        nav_links=page_options["nav_links"],
        extra_styles=page_options["extra_styles"],
        stats=page_options["stats"],
        stats_label=str(page_options["stats_label"]),
        filter_id=str(page_options["filter_id"]),
        filter_placeholder=str(page_options["filter_placeholder"]),
        table_id=str(page_options["table_id"]),
        empty_id=str(page_options["empty_id"]),
        empty_text=str(page_options["empty_text"]),
        table_header=str(page_options["table_header"]),
        table_rows=page_options["table_rows"],
        generated_class=str(page_options.get("generated_class", "summary generated")),
        repository_archive_filter=bool(page_options.get("repository_archive_filter", False)),
    )


def render_inventory_page_context(context: InventoryPageContext) -> str:
    label = generated_label(context.generated_at)
    lines = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"  <title>{escape(context.page_title)}</title>",
        "  <style>",
        *BASE_PAGE_STYLES,
        *context.extra_styles,
        "  </style>",
        "</head>",
        "<body>",
        "  <main>",
        f"    {render_nav(context.nav_links)}",
        "    <header>",
        "      <div>",
        f"        <h1>{escape(context.page_title)}</h1>",
        f'        <p class="summary">{escape(context.summary)}</p>',
        "      </div>",
    ]
    if label:
        lines.append(f'      <p class="{escape(context.generated_class)}">Generated: {escape(label)}</p>')
    lines.extend(
        [
            "    </header>",
            *render_stats_cards(context.stats, aria_label=context.stats_label),
            '    <div class="toolbar">',
            f'      <input id="{escape(context.filter_id)}" type="search" placeholder="{escape(context.filter_placeholder)}" autocomplete="off">',
            *render_repository_archive_filter(context),
            "    </div>",
            '    <div class="table-wrap">',
            f'      <table id="{escape(context.table_id)}">',
            "        <thead>",
            f"          {context.table_header}",
            "        </thead>",
            "        <tbody>",
            *context.table_rows,
            "        </tbody>",
            "      </table>",
            f'      <div id="{escape(context.empty_id)}" class="empty">{escape(context.empty_text)}</div>',
            "    </div>",
            "  </main>",
            *render_filter_script(input_id=context.filter_id, table_id=context.table_id, empty_id=context.empty_id),
            "</body>",
            "</html>",
            "",
        ]
    )
    return "\n".join(lines)


def render_repository_archive_filter(context: InventoryPageContext) -> list[str]:
    if not context.repository_archive_filter:
        return []
    return [f'      <label><input id="{escape(context.filter_id)}-archived" type="checkbox"> Archived only</label>']


def render_cell(value: str) -> str:
    return escape(value) if value else '<span class="missing">missing</span>'


def render_code_cell(value: str) -> str:
    return f"<code>{escape(value)}</code>" if value else '<span class="missing">missing</span>'


__all__ = [
    "BASE_PAGE_STYLES",
    "InventoryPageContext",
    "generated_label",
    "inventory_page_context",
    "render_cell",
    "render_code_cell",
    "render_filter_script",
    "render_inventory_page",
    "render_inventory_page_context",
    "render_nav",
    "render_repository_archive_filter",
    "render_stats_cards",
]
