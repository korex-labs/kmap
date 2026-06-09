from kmap.command import inspect as command_inspect_module
from kmap.command.inspect.namespace import inspect_namespace, inspect_namespaces


def test_inspect_command_package_exports_cli_entrypoints_only():
    assert command_inspect_module.__all__ == ["inspect_namespace", "inspect_namespaces"]
    assert command_inspect_module.inspect_namespace is inspect_namespace
    assert command_inspect_module.inspect_namespaces is inspect_namespaces
