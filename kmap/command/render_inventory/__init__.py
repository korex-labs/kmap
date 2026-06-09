"""Compatibility exports for the render-inventory command."""

from ...inventory.namespaces import (
    DEFAULT_CONFIG_DIR,
    DEFAULT_INVENTORY_DIR,
    DEFAULT_NAMESPACES_INVENTORY_FILE,
    InventoryRow,
    collect_inventory_rows,
    config_files,
    inventory_rows_for_config,
    render_inventory,
    render_inventory_html,
)

__all__ = [
    "DEFAULT_CONFIG_DIR",
    "DEFAULT_INVENTORY_DIR",
    "DEFAULT_NAMESPACES_INVENTORY_FILE",
    "InventoryRow",
    "collect_inventory_rows",
    "config_files",
    "inventory_rows_for_config",
    "render_inventory",
    "render_inventory_html",
]
