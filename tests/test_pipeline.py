from kmap.command import run_all
from kmap.command.run_all import discovery
from kmap.command.run_all.core import run_all as run_all_entrypoint


def test_run_all_command_package_exports_cli_reachable_helpers():
    assert run_all.DEFAULT_REPORTS_DIR
    assert run_all.DEFAULT_DEPENDENCIES_FILE
    assert run_all.DEFAULT_ARCHITECTURE_FILE
    assert run_all.run_all is run_all_entrypoint
    assert discovery.parse_namespace_args
    assert discovery.parse_namespace_project_args
    assert discovery.discovery_target_identity
    assert discovery.report_stem_for_namespace
