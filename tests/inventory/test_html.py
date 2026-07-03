from datetime import UTC, datetime

from kmap.inventory.html import (
    InventoryPageContext,
    render_cell,
    render_code_cell,
    render_filter_script,
    render_inventory_page,
    render_inventory_page_context,
    render_nav,
)


def test_render_nav_and_cells_escape_values():
    assert render_nav([("clusters.html?x=<bad>", "Clusters <All>")]) == (
        '<nav><a href="clusters.html?x=&lt;bad&gt;">Clusters &lt;All&gt;</a></nav>'
    )
    assert render_cell("Team <A>") == "Team &lt;A&gt;"
    assert render_cell("") == '<span class="missing">missing</span>'
    assert render_code_cell("ns <prod>") == "<code>ns &lt;prod&gt;</code>"


def test_render_filter_script_uses_supplied_element_ids():
    rendered = "\n".join(
        render_filter_script(input_id="inventory-filter", table_id="inventory-table", empty_id="inventory-empty")
    )

    assert "document.getElementById('inventory-filter')" in rendered
    assert "document.querySelectorAll('#inventory-table tbody tr')" in rendered
    assert "document.getElementById('inventory-empty')" in rendered


def test_render_inventory_page_builds_shared_page_shell():
    rendered = render_inventory_page(
        page_title="Inventory <All>",
        summary="2 rows <ok>",
        generated_at=datetime(2026, 5, 18, 9, 30, 0, tzinfo=UTC),
        nav_links=[("namespaces.html", "Namespaces")],
        extra_styles=["    main { width: 100%; }"],
        stats=[(2, "Rows"), (1, "Missing <things>")],
        stats_label="Summary <stats>",
        filter_id="page-filter",
        filter_placeholder="Filter <rows>",
        table_id="page-table",
        empty_id="page-empty",
        empty_text="No matching rows.",
        table_header="<tr><th>Name</th></tr>",
        table_rows=["          <tr><td>demo</td></tr>"],
    )

    assert "<title>Inventory &lt;All&gt;</title>" in rendered
    assert '<p class="summary">2 rows &lt;ok&gt;</p>' in rendered
    assert '<section class="stats" aria-label="Summary &lt;stats&gt;">' in rendered
    assert "<span>Missing &lt;things&gt;</span>" in rendered
    assert 'placeholder="Filter &lt;rows&gt;"' in rendered
    assert "Generated: 2026-05-18 09:30:00 UTC" in rendered
    assert "          <tr><td>demo</td></tr>" in rendered


def test_render_inventory_page_context_builds_same_page_shell():
    page_context = InventoryPageContext(
        page_title="Inventory",
        summary="1 row",
        generated_at=None,
        nav_links=[("namespaces.html", "Namespaces")],
        extra_styles=[],
        stats=[(1, "Rows")],
        stats_label="Summary",
        filter_id="filter",
        filter_placeholder="Filter",
        table_id="table",
        empty_id="empty",
        empty_text="No rows.",
        table_header="<tr><th>Name</th></tr>",
        table_rows=["          <tr><td>demo</td></tr>"],
    )
    rendered = render_inventory_page_context(page_context)
    rendered_from_wrapper = render_inventory_page(page_context=page_context)

    assert "<title>Inventory</title>" in rendered
    assert '<input id="filter" type="search" placeholder="Filter" autocomplete="off">' in rendered
    assert "          <tr><td>demo</td></tr>" in rendered
    assert rendered_from_wrapper == rendered
