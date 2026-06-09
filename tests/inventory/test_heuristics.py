from kmap.inventory.heuristics import (
    inferred_inventory_row,
    namespace_parts,
    namespace_product,
    namespace_project_id,
    namespace_stage,
    namespace_without_project_id_suffix,
    project_id_suffix_config,
    repository_identity,
)
from kmap.inventory.namespaces import InventoryRow

HEURISTICS = {
    "inventory": {
        "namespace_heuristics": {
            "project_id_suffix": {
                "enabled": True,
                "pattern": r"[-](?P<project_id>\d+)$",
                "repository_format": "repository:{project_id}",
            },
            "strip_project_id_suffix": True,
            "stage_tokens": ["prod", "review", "dev"],
        }
    }
}


def test_namespace_project_id_and_repository_identity_are_configurable():
    heuristics = HEURISTICS["inventory"]["namespace_heuristics"]

    assert namespace_project_id("payment-api-prod-1234", heuristics) == "1234"
    assert repository_identity("1234", heuristics) == "repository:1234"


def test_namespace_project_id_requires_enabled_pattern_and_supports_numbered_groups():
    assert namespace_project_id("payment-api-prod-1234", {}) == ""
    assert project_id_suffix_config({"project_id_suffix": "bad"}) == {}
    assert namespace_project_id("payment-api-prod-1234", {"project_id_suffix": "bad"}) == ""
    assert namespace_project_id("payment-api-prod-1234", {"project_id_suffix": {"enabled": False}}) == ""
    assert (
        namespace_project_id(
            "payment-api-prod-1234",
            {"project_id_suffix": {"enabled": True, "pattern": r"-(\d+)$"}},
        )
        == "1234"
    )


def test_namespace_product_strips_configured_project_id_suffix_and_stage_tokens():
    heuristics = HEURISTICS["inventory"]["namespace_heuristics"]

    assert namespace_parts("payment_api-prod-1234", heuristics) == ["payment", "api", "prod"]
    assert namespace_without_project_id_suffix("payment-api-prod-1234", heuristics) == "payment-api-prod"
    assert namespace_without_project_id_suffix("payment-api-prod", heuristics) == "payment-api-prod"
    assert namespace_product("payment-api-prod-1234", heuristics) == "payment-api"
    assert namespace_product("payment-api-review-1234", heuristics) == "payment-api"
    assert namespace_stage("payment-api-review-1234", heuristics) == "review"


def test_inferred_inventory_row_uses_configured_metadata_first_and_fills_missing_repository():
    configured = InventoryRow(
        cluster="old",
        product="payments",
        product_title="Payments",
        namespace="payment-api-prod-1234",
        repository="",
        owner_team="Ops",
        stage="prod",
    )

    assert inferred_inventory_row(
        cluster="cluster-a",
        namespace="payment-api-prod-1234",
        configured=configured,
        tool_config=HEURISTICS,
    ) == InventoryRow(
        cluster="cluster-a",
        product="payments",
        product_title="Payments",
        namespace="payment-api-prod-1234",
        repository="repository:1234",
        owner_team="Ops",
        stage="prod",
    )


def test_inferred_inventory_row_rewrites_namespace_for_related_configured_row():
    configured = InventoryRow(
        cluster="old",
        product="payments",
        product_title="Payments",
        namespace="payment-api-prod-1234",
        repository="https://git.example/payments/payment-api",
        owner_team="Ops",
        stage="",
    )

    assert inferred_inventory_row(
        cluster="cluster-a",
        namespace="payment-api-review-1234",
        configured=configured,
        tool_config=HEURISTICS,
    ) == InventoryRow(
        cluster="cluster-a",
        product="payments",
        product_title="Payments",
        namespace="payment-api-review-1234",
        repository="https://git.example/payments/payment-api",
        owner_team="Ops",
        stage="review",
    )


def test_inferred_inventory_row_populates_unknown_namespace_from_heuristics():
    assert inferred_inventory_row(
        cluster="cluster-a",
        namespace="payment-api-review-1234",
        configured=None,
        tool_config=HEURISTICS,
    ) == InventoryRow(
        cluster="cluster-a",
        product="",
        product_title="",
        namespace="payment-api-review-1234",
        repository="repository:1234",
        owner_team="",
        stage="review",
    )
