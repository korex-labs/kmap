from argparse import Namespace

import pytest

import kmap.command.run_all.core as run_all_core_module
from kmap.command import combine as combine_module
from kmap.command import normalize as normalize_module
from kmap.command import render as render_module
from kmap.command.inspect import namespace as inspect_namespace_module
from kmap.command.run_all import DEFAULT_ARCHITECTURE_FILE, DEFAULT_DEPENDENCIES_FILE, DEFAULT_REPORTS_DIR, run_all
from kmap.command.run_all.core import INTERRUPTED_EXIT_CODE, inventory_args
from kmap.command.run_all.discovery import (
    discovery_target_identity,
    parse_namespace_args,
    parse_namespace_project_args,
    report_stem_for_namespace,
)
from kmap.inventory import buckets as inventory_buckets_module
from kmap.inventory import namespaces as inventory_namespaces_module
from kmap.paths import SCHEMAS_ROOT


def _run_all_args():
    return Namespace(
        inspect_format="json",
        namespace=["payments"],
        namespace_project=[],
        out_dir="/tmp/out",
        dependencies_file="/tmp/out/dependencies.list",
        dependencies_json_output_file="/tmp/out/dependencies.json",
        architecture_output_file="/tmp/out/architecture.json",
        bucket_reports_dir="/tmp/buckets",
        inventory_output_dir="/tmp/Inventory",
        product="demo",
        project="",
        context="ctx",
        kubeconfig="",
        kubectl="kubectl",
        helm="helm",
        request_timeout="15s",
        exec_sleep=0,
        kubectl_qps_sleep=0,
        match_regex="main",
        no_exec=True,
        max_exec_pods_per_workload=1,
        data_mode="sanitized",
        mock_seed="",
        config="config.yaml",
        org="org",
        env="prod",
        product_metadata={},
        project_metadata={},
        discovery_config={"namespaces": {}},
        render="likec4",
        struct_output_dir="",
        likec4_output_dir="",
        likec4_common_path="../common",
        output="plain",
    )


def test_inventory_args_default_to_cwd_project_layout_when_no_config_is_given():
    args = _run_all_args()
    args.config = ""

    parsed = inventory_args(args)

    assert parsed.config_dir == str(SCHEMAS_ROOT / "config")
    assert parsed.bucket_artifacts_dir == "/tmp/buckets"
    assert parsed.output_dir == "/tmp/Inventory"


def test_run_all_wires_stages_and_derives_default_outputs(monkeypatch):
    calls = []

    monkeypatch.setattr(
        inspect_namespace_module, "inspect_namespace", lambda args: calls.append(("inspect", args)) or 0
    )
    monkeypatch.setattr(combine_module, "combine_reports", lambda args: calls.append(("combine", args)) or 0)
    monkeypatch.setattr(normalize_module, "normalize_architecture", lambda args: calls.append(("normalize", args)) or 0)
    monkeypatch.setattr(render_module, "render_outputs", lambda args: calls.append(("render", args)) or 0)
    monkeypatch.setattr(
        inventory_buckets_module, "write_bucket_report", lambda **kwargs: calls.append(("buckets", kwargs))
    )
    monkeypatch.setattr(
        inventory_namespaces_module, "render_inventory", lambda args: calls.append(("inventory", args)) or 0
    )

    args = Namespace(
        inspect_format="json",
        namespace=["payments"],
        namespace_project=["payments=pay"],
        out_dir=DEFAULT_REPORTS_DIR,
        dependencies_file=DEFAULT_DEPENDENCIES_FILE,
        dependencies_json_output_file=None,
        architecture_output_file=DEFAULT_ARCHITECTURE_FILE,
        bucket_reports_dir="/tmp/buckets",
        inventory_output_dir="/tmp/Inventory",
        product="demo",
        project="",
        context="ctx",
        kubeconfig="/tmp/kubeconfig",
        kubectl="kubectl",
        helm="helm",
        request_timeout="15s",
        exec_sleep=0.1,
        kubectl_qps_sleep=0.2,
        match_regex="main",
        no_exec=True,
        max_exec_pods_per_workload=1,
        data_mode="sanitized",
        mock_seed="seed",
        config="config.yaml",
        org="org",
        env="prod",
        product_metadata={"title": "Demo"},
        project_metadata={"pay": {"title": "Payments"}},
        discovery_config={
            "context": "config-ctx",
            "kubeconfig": "/config/kubeconfig",
            "namespaces": {},
        },
        render="both",
        struct_output_dir="",
        likec4_output_dir="/tmp/likec4",
        likec4_common_path="../common",
    )

    assert run_all(args) == 0

    assert [name for name, _ in calls] == ["inspect", "combine", "normalize", "render", "buckets", "inventory"]
    inspect_args = calls[0][1]
    assert inspect_args.namespace == "payments"
    assert inspect_args.project == "pay"
    assert inspect_args.kubeconfig == "/tmp/kubeconfig"
    assert inspect_args.context == "config-ctx"
    assert inspect_args.report_stem == "payments"
    assert inspect_args.out_dir.endswith("/payments")

    combine_args = calls[1][1]
    assert combine_args.reports_dir == inspect_args.out_dir
    assert combine_args.output_file.endswith("/payments/dependencies.list")
    assert combine_args.json_output_file.endswith("/payments/dependencies.json")

    normalize_args = calls[2][1]
    assert normalize_args.output_file.endswith("/payments/architecture.json")
    assert normalize_args.dependencies_file.endswith("/payments/dependencies.json")
    assert normalize_args.product_metadata == {"title": "Demo"}

    render_args = calls[3][1]
    assert render_args.architecture_file.endswith("/payments/architecture.json")
    assert render_args.render == "both"
    assert render_args.struct_output_dir == ""
    assert render_args.likec4_output_dir == "/tmp/likec4"
    bucket_args = calls[4][1]
    assert str(bucket_args["reports_dir"]).endswith("/payments")
    assert str(bucket_args["output_dir"]) == "/tmp/buckets"
    assert bucket_args["config_path"] == "config.yaml"
    assert bucket_args["product"] == "demo"
    inventory_args = calls[5][1]
    assert inventory_args.config_dir == "."
    assert inventory_args.bucket_artifacts_dir == "/tmp/buckets"
    assert inventory_args.output_dir == "/tmp/Inventory"


def test_run_all_stops_when_cluster_preflight_fails(monkeypatch):
    calls = []

    monkeypatch.setattr(run_all_core_module, "preflight_run_all_targets", lambda args, targets: 7)
    monkeypatch.setattr(
        inspect_namespace_module, "inspect_namespace", lambda args: calls.append(("inspect", args)) or 0
    )
    args = _run_all_args()
    args.cluster_preflight = True

    assert run_all(args) == 7
    assert calls == []


def test_run_all_can_render_structurizr_only(monkeypatch):
    calls = []

    monkeypatch.setattr(
        inspect_namespace_module, "inspect_namespace", lambda args: calls.append(("inspect", args)) or 0
    )
    monkeypatch.setattr(combine_module, "combine_reports", lambda args: calls.append(("combine", args)) or 0)
    monkeypatch.setattr(normalize_module, "normalize_architecture", lambda args: calls.append(("normalize", args)) or 0)
    monkeypatch.setattr(render_module, "render_outputs", lambda args: calls.append(("render", args)) or 0)
    monkeypatch.setattr(
        inventory_buckets_module, "write_bucket_report", lambda **kwargs: calls.append(("buckets", kwargs))
    )
    monkeypatch.setattr(
        inventory_namespaces_module, "render_inventory", lambda args: calls.append(("inventory", args)) or 0
    )

    args = Namespace(
        inspect_format="json",
        namespace=["payments"],
        namespace_project=[],
        out_dir=DEFAULT_REPORTS_DIR,
        dependencies_file=DEFAULT_DEPENDENCIES_FILE,
        dependencies_json_output_file=None,
        architecture_output_file=DEFAULT_ARCHITECTURE_FILE,
        bucket_reports_dir="/tmp/buckets",
        inventory_output_dir="/tmp/Inventory",
        product="pay",
        project="",
        context="ctx",
        kubeconfig="",
        kubectl="kubectl",
        helm="helm",
        request_timeout="15s",
        exec_sleep=0.1,
        kubectl_qps_sleep=0.2,
        match_regex="main",
        no_exec=True,
        max_exec_pods_per_workload=1,
        data_mode="sanitized",
        mock_seed="",
        config="config.yaml",
        org="org",
        env="prod",
        product_metadata={},
        project_metadata={},
        discovery_config={"namespaces": {}},
        render="structurizr",
        struct_output_dir="/tmp/Structurizr/pay",
        likec4_output_dir="",
        likec4_common_path="../common",
    )

    assert run_all(args) == 0

    assert [name for name, _ in calls] == ["inspect", "combine", "normalize", "render", "buckets", "inventory"]
    render_args = calls[3][1]
    assert render_args.architecture_file.endswith("/payments/architecture.json")
    assert render_args.render == "structurizr"
    assert render_args.struct_output_dir == "/tmp/Structurizr/pay"


def test_run_all_uses_context_report_stems_only_for_multi_context(monkeypatch):
    calls = []

    monkeypatch.setattr(
        inspect_namespace_module, "inspect_namespace", lambda args: calls.append(("inspect", args)) or 0
    )
    monkeypatch.setattr(combine_module, "combine_reports", lambda args: calls.append(("combine", args)) or 0)
    monkeypatch.setattr(normalize_module, "normalize_architecture", lambda args: calls.append(("normalize", args)) or 0)
    monkeypatch.setattr(render_module, "render_outputs", lambda args: calls.append(("render", args)) or 0)
    monkeypatch.setattr(
        inventory_buckets_module, "write_bucket_report", lambda **kwargs: calls.append(("buckets", kwargs))
    )
    monkeypatch.setattr(
        inventory_namespaces_module, "render_inventory", lambda args: calls.append(("inventory", args)) or 0
    )

    args = Namespace(
        inspect_format="json",
        namespace=["api-prod", "worker-prod"],
        namespace_project=["api-prod=api", "worker-prod=worker"],
        out_dir="/tmp/out",
        dependencies_file="/tmp/out/dependencies.list",
        dependencies_json_output_file="/tmp/out/dependencies.json",
        architecture_output_file="/tmp/out/architecture.json",
        bucket_reports_dir="/tmp/buckets",
        inventory_output_dir="/tmp/Inventory",
        product="demo",
        project="",
        kubeconfig="",
        kubectl="kubectl",
        helm="helm",
        request_timeout="15s",
        exec_sleep=0,
        kubectl_qps_sleep=0,
        match_regex="main",
        no_exec=True,
        max_exec_pods_per_workload=1,
        data_mode="sanitized",
        mock_seed="",
        config="config.yaml",
        org="org",
        env="prod",
        product_metadata={},
        project_metadata={},
        discovery_config={
            "context": "default",
            "namespaces": {
                "api-prod": {"context": "api-ctx"},
                "worker-prod": {"context": "worker-ctx"},
            },
        },
        render="likec4",
        struct_output_dir="",
        likec4_output_dir="",
        likec4_common_path="../common",
    )

    assert run_all(args) == 0

    inspect_calls = [call[1] for call in calls if call[0] == "inspect"]
    assert [call.context for call in inspect_calls] == ["api-ctx", "worker-ctx"]
    assert [call.report_stem for call in inspect_calls] == ["api-ctx__api-prod", "worker-ctx__worker-prod"]


def test_discovery_target_identity_includes_kubeconfig_when_context_repeats():
    first = discovery_target_identity({"context": "shared", "kubeconfig": "/clusters/a.yaml"})
    second = discovery_target_identity({"context": "shared", "kubeconfig": "/clusters/b.yaml"})

    assert first != second
    assert first.startswith("shared@")
    assert report_stem_for_namespace(
        "api-prod", {"context": "shared", "kubeconfig": "/clusters/a.yaml"}, True
    ).startswith("shared-")


def test_run_all_uses_target_report_stems_for_same_context_different_kubeconfig(monkeypatch):
    calls = []

    monkeypatch.setattr(
        inspect_namespace_module, "inspect_namespace", lambda args: calls.append(("inspect", args)) or 0
    )
    monkeypatch.setattr(combine_module, "combine_reports", lambda args: calls.append(("combine", args)) or 0)
    monkeypatch.setattr(normalize_module, "normalize_architecture", lambda args: calls.append(("normalize", args)) or 0)
    monkeypatch.setattr(render_module, "render_outputs", lambda args: calls.append(("render", args)) or 0)
    monkeypatch.setattr(
        inventory_buckets_module, "write_bucket_report", lambda **kwargs: calls.append(("buckets", kwargs))
    )
    monkeypatch.setattr(
        inventory_namespaces_module, "render_inventory", lambda args: calls.append(("inventory", args)) or 0
    )

    args = Namespace(
        inspect_format="json",
        namespace=["api-prod", "worker-prod"],
        namespace_project=[],
        out_dir="/tmp/out",
        dependencies_file="/tmp/out/dependencies.list",
        dependencies_json_output_file="/tmp/out/dependencies.json",
        architecture_output_file="/tmp/out/architecture.json",
        bucket_reports_dir="/tmp/buckets",
        inventory_output_dir="/tmp/Inventory",
        product="demo",
        project="",
        kubeconfig="",
        kubectl="kubectl",
        helm="helm",
        request_timeout="15s",
        exec_sleep=0,
        kubectl_qps_sleep=0,
        match_regex="main",
        no_exec=True,
        max_exec_pods_per_workload=1,
        data_mode="sanitized",
        mock_seed="",
        config="config.yaml",
        org="org",
        env="prod",
        product_metadata={},
        project_metadata={},
        discovery_config={
            "context": "shared",
            "namespaces": {
                "api-prod": {"kubeconfig": "/clusters/a.yaml"},
                "worker-prod": {"kubeconfig": "/clusters/b.yaml"},
            },
        },
        render="likec4",
        struct_output_dir="",
        likec4_output_dir="",
        likec4_common_path="../common",
    )

    assert run_all(args) == 0

    inspect_calls = [call[1] for call in calls if call[0] == "inspect"]
    stems = [call.report_stem for call in inspect_calls]
    assert stems[0].endswith("__api-prod")
    assert stems[1].endswith("__worker-prod")
    assert stems[0] != "shared__api-prod"
    assert stems[1] != "shared__worker-prod"
    assert stems[0].split("__", 1)[0] != stems[1].split("__", 1)[0]


def test_parse_namespace_args_accepts_repeated_and_comma_values():
    assert parse_namespace_args(["one,two", "three"]) == ["one", "two", "three"]


def test_parse_namespace_args_deduplicates_and_ignores_blanks():
    assert parse_namespace_args(["one, two", "", "two, ,three", "one"]) == ["one", "two", "three"]


def test_parse_namespace_project_args_accepts_mapping_values():
    assert parse_namespace_project_args(["ns-a=project-a", "ns-b=project-b"]) == {
        "ns-a": "project-a",
        "ns-b": "project-b",
    }


def test_parse_namespace_project_args_ignores_blank_values():
    assert parse_namespace_project_args(["", " , ", "ns-a=project-a"]) == {"ns-a": "project-a"}


@pytest.mark.parametrize(
    ("failing_stage", "expected_rc", "expected_calls"),
    [
        ("inspect", 11, ["inspect"]),
        ("combine", 12, ["inspect", "combine"]),
        ("normalize", 13, ["inspect", "combine", "normalize"]),
        ("render", 14, ["inspect", "combine", "normalize", "render"]),
    ],
)
def test_run_all_returns_first_failing_stage(monkeypatch, failing_stage, expected_rc, expected_calls):
    calls = []

    def stage(name, rc=0):
        def _run(args):
            calls.append(name)
            return expected_rc if name == failing_stage else rc

        return _run

    monkeypatch.setattr(inspect_namespace_module, "inspect_namespace", stage("inspect"))
    monkeypatch.setattr(combine_module, "combine_reports", stage("combine"))
    monkeypatch.setattr(normalize_module, "normalize_architecture", stage("normalize"))
    monkeypatch.setattr(render_module, "render_outputs", stage("render"))

    assert run_all(_run_all_args()) == expected_rc
    assert calls == expected_calls


def test_run_all_returns_interrupted_status_and_stops_later_stages(monkeypatch):
    calls = []

    def interrupt(args):
        calls.append("inspect")
        raise KeyboardInterrupt

    monkeypatch.setattr(inspect_namespace_module, "inspect_namespace", interrupt)
    monkeypatch.setattr(combine_module, "combine_reports", lambda args: calls.append("combine") or 0)

    assert run_all(_run_all_args()) == INTERRUPTED_EXIT_CODE
    assert calls == ["inspect"]


def test_run_all_rejects_text_only_inspect_format():
    args = _run_all_args()
    args.inspect_format = "text"

    with pytest.raises(SystemExit, match="--inspect-format must be json or both"):
        run_all(args)
