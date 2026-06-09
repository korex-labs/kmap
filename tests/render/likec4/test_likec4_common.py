from kmap.render.likec4.common import likec4_alias, likec4_metadata_lines, likec4_reference_map
from kmap.render.likec4.model import likec4_link_label
from kmap.render.likec4.relations import likec4_relationship_kind


def test_likec4_alias_and_relationship_kind_are_stable():
    assert likec4_alias("sys.demo.payment-api") == "sys_demo_payment_api"
    assert likec4_relationship_kind("https") == "http_s"
    assert likec4_relationship_kind("kafka") == "KafkaPub"
    assert likec4_relationship_kind("redis") == "tcp"


def test_likec4_reference_map_nests_containers_under_systems():
    refs = likec4_reference_map(
        {
            "systems": [{"id": "sys.product.api"}],
            "containers": [{"id": "ctr.product.api.app", "system_id": "sys.product.api"}],
        }
    )

    assert refs == {
        "sys.product.api": "sys_product_api",
        "ctr.product.api.app": "sys_product_api.ctr_product_api_app",
    }


def test_likec4_metadata_lines_and_link_labels_escape_values():
    assert likec4_metadata_lines([("repo", 'https://example.com/"repo"\nnext\\path')], indent="  ") == [
        "  metadata {",
        '    repo "https://example.com/\\"repo\\"\\nnext\\\\path"',
        "  }",
    ]
    assert likec4_link_label("repo") == "Repository"
    assert likec4_link_label("service_tasks") == "Service Tasks"
