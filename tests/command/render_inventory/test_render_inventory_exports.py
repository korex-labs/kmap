from kmap.command import render_inventory
from kmap.inventory import namespaces


def test_render_inventory_reexports_namespace_inventory_api():
    exported_names = set(render_inventory.__all__)

    assert exported_names == {
        "DEFAULT_CONFIG_DIR",
        "DEFAULT_INVENTORY_DIR",
        "DEFAULT_NAMESPACES_INVENTORY_FILE",
        "InventoryRow",
        "collect_inventory_rows",
        "config_files",
        "inventory_rows_for_config",
        "render_inventory",
        "render_inventory_html",
    }
    for name in exported_names:
        assert getattr(render_inventory, name) is getattr(namespaces, name)
