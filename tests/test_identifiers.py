from kmap.identifiers import (
    architecture_id,
    architecture_id_part,
    architecture_id_parts,
    dsl_url,
    ident,
    q,
    short_hash,
    sq,
)
from kmap.naming import architecture_id as naming_architecture_id


def test_identifier_helpers_are_stable():
    assert ident("9 Payment/API") == "_9_Payment_API"
    assert q('say "hello"') == 'say \\"hello\\"'
    assert short_hash("payment", 6) == "e86256"
    assert architecture_id_part("Payment Gateway GO") == "payment_gateway_go"
    assert architecture_id("sys", "Demo", "Payment Gateway") == "sys.demo.payment_gateway"
    assert architecture_id_parts(["sys", "", "Demo"]) == ["sys", "unknown", "demo"]


def test_naming_package_reexports_identifier_helper_for_display_code():
    assert naming_architecture_id("sys", "Demo") == "sys.demo"


def test_dsl_string_helpers_escape_control_characters_and_backslashes():
    assert q('a "quoted"\npath\\value\t') == 'a \\"quoted\\"\\npath\\\\value\\t'
    assert sq("label 'quoted'\npath\\value") == "label \\'quoted\\'\\npath\\\\value"


def test_dsl_url_rejects_values_that_can_break_statement_syntax():
    assert dsl_url("https://example.com/path?x=1") == "https://example.com/path?x=1"
    assert dsl_url('https://example.com/"bad"') == ""
    assert dsl_url("https://example.com/path\ninclude hacked") == ""
    assert dsl_url("javascript:alert(1)") == ""
