from argparse import Namespace

from kmap.command.run_all.targets import resolve_run_all_targets, should_use_target_report_stems


def test_resolve_run_all_targets_uses_namespace_project_mapping():
    args = Namespace(
        product="demo",
        project="",
        kubeconfig="",
        discovery_config={"context": "default", "namespaces": {"api": {"context": "api-ctx"}}},
    )

    targets = resolve_run_all_targets(args, ["api"], {"api": "api-project"})

    assert len(targets) == 1
    assert targets[0].namespace == "api"
    assert targets[0].project == "api-project"
    assert targets[0].discovery["context"] == "api-ctx"


def test_resolve_run_all_targets_falls_back_to_cli_project():
    args = Namespace(
        product="demo",
        project="shared-project",
        kubeconfig="/cli/kubeconfig",
        discovery_config={"context": "default"},
    )

    targets = resolve_run_all_targets(args, ["worker"], {})

    assert targets[0].project == "shared-project"
    assert targets[0].discovery["kubeconfig"] == "/cli/kubeconfig"


def test_resolve_run_all_targets_preserves_config_kubeconfig_without_cli_override():
    args = Namespace(
        product="demo",
        project="shared-project",
        kubeconfig="",
        discovery_config={"context": "config-ctx", "kubeconfig": "/config/kubeconfig"},
    )

    targets = resolve_run_all_targets(args, ["worker"], {})

    assert targets[0].discovery == {"context": "config-ctx", "kubeconfig": "/config/kubeconfig"}


def test_should_use_target_report_stems_detects_multiple_targets():
    args = Namespace(
        product="demo",
        project="",
        kubeconfig="",
        discovery_config={
            "context": "default",
            "namespaces": {"api": {"context": "api-ctx"}, "worker": {"context": "worker-ctx"}},
        },
    )
    targets = resolve_run_all_targets(args, ["api", "worker"], {})

    assert should_use_target_report_stems(targets) is True


def test_should_use_target_report_stems_ignores_single_default_target():
    args = Namespace(product="demo", project="", kubeconfig="", discovery_config={})
    targets = resolve_run_all_targets(args, ["api", "worker"], {})

    assert should_use_target_report_stems(targets) is False
