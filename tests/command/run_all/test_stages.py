from argparse import Namespace

from kmap.command.run_all.stages import (
    build_combine_args,
    build_inspect_args,
    build_normalize_args,
    build_render_args,
)
from kmap.command.run_all.targets import RunAllTarget


def test_build_inspect_args_maps_target_and_cli_options():
    args = Namespace(
        kubectl="kubectl",
        helm="helm",
        out_dir="/tmp/out",
        request_timeout="15s",
        exec_sleep=0.1,
        kubectl_qps_sleep=0.2,
        match_regex="main",
        no_exec=True,
        max_exec_pods_per_workload=2,
        inspect_format="json",
        data_mode="sanitized",
        mock_seed="seed",
    )
    target = RunAllTarget(
        namespace="api",
        project="api-project",
        discovery={"context": "api-ctx", "kubeconfig": "/clusters/api.yaml"},
    )

    inspect_args = build_inspect_args(args, target, use_target_report_stems=True)

    assert inspect_args.namespace == "api"
    assert inspect_args.project == "api-project"
    assert inspect_args.context == "api-ctx"
    assert inspect_args.kubeconfig == "/clusters/api.yaml"
    assert inspect_args.out_dir == "/tmp/out"
    assert inspect_args.format == "json"
    assert inspect_args.report_stem.startswith("api-ctx-")
    assert inspect_args.report_stem.endswith("__api")


def test_build_combine_args_maps_output_files():
    args = Namespace(
        out_dir="/tmp/out",
        dependencies_file="/tmp/out/dependencies.list",
        dependencies_json_output_file="/tmp/out/dependencies.json",
    )

    combine_args = build_combine_args(args)

    assert combine_args.reports_dir == "/tmp/out"
    assert combine_args.output_file == "/tmp/out/dependencies.list"
    assert combine_args.json_output_file == "/tmp/out/dependencies.json"


def test_build_normalize_args_maps_config_and_defaults_missing_optional_config():
    args = Namespace(
        out_dir="/tmp/out",
        architecture_output_file="/tmp/out/architecture.json",
        dependencies_file="/tmp/out/dependencies.list",
        dependencies_json_output_file=None,
        config="config.yaml",
        org="Example Org",
        product="demo",
        project="",
        env="prod",
    )

    normalize_args = build_normalize_args(args)

    assert normalize_args.reports_dir == "/tmp/out"
    assert normalize_args.output_file == "/tmp/out/architecture.json"
    assert normalize_args.dependencies_file == "/tmp/out/dependencies.list"
    assert normalize_args.product_metadata == {}
    assert normalize_args.project_metadata == {}
    assert normalize_args.discovery_config == {}
    assert normalize_args.system_naming_config["fallback"]["enabled"] is True
    assert normalize_args.dependency_hotspots_config["enabled"] is True


def test_build_render_args_maps_render_config():
    args = Namespace(
        architecture_output_file="/tmp/out/architecture.json",
        render="likec4",
        struct_output_dir="",
        likec4_output_dir="/tmp/LikeC4/demo",
        likec4_common_path="../common",
    )

    render_args = build_render_args(args)

    assert render_args.architecture_file == "/tmp/out/architecture.json"
    assert render_args.render == "likec4"
    assert render_args.struct_output_dir == ""
    assert render_args.likec4_output_dir == "/tmp/LikeC4/demo"
    assert render_args.likec4_common_path == "../common"
