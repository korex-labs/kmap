"""Stage argument builders for run-all."""

import argparse

from ...config import normalize_dependency_hotspots_config, normalize_system_naming_config
from .discovery import report_stem_for_namespace
from .targets import RunAllTarget


def build_inspect_args(
    args: argparse.Namespace,
    target: RunAllTarget,
    *,
    use_target_report_stems: bool,
) -> argparse.Namespace:
    discovery_target = target.discovery
    return argparse.Namespace(
        namespace=target.namespace,
        project=target.project,
        context=discovery_target.get("context", ""),
        kubeconfig=discovery_target.get("kubeconfig", ""),
        kubectl=args.kubectl,
        helm=args.helm,
        out_dir=args.out_dir,
        request_timeout=args.request_timeout,
        exec_sleep=args.exec_sleep,
        kubectl_qps_sleep=args.kubectl_qps_sleep,
        match_regex=args.match_regex,
        no_exec=args.no_exec,
        max_exec_pods_per_workload=args.max_exec_pods_per_workload,
        format=args.inspect_format,
        data_mode=args.data_mode,
        mock_seed=args.mock_seed,
        report_stem=report_stem_for_namespace(target.namespace, discovery_target, use_target_report_stems),
    )


def build_combine_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        reports_dir=args.out_dir,
        output_file=args.dependencies_file,
        json_output_file=args.dependencies_json_output_file,
        system_naming_config=getattr(args, "system_naming_config", normalize_system_naming_config({})),
    )


def build_normalize_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        reports_dir=args.out_dir,
        output_file=args.architecture_output_file,
        dependencies_file=args.dependencies_json_output_file or args.dependencies_file,
        config=args.config,
        org=args.org,
        product=args.product,
        project=args.project,
        env=args.env,
        product_metadata=getattr(args, "product_metadata", {}),
        project_metadata=getattr(args, "project_metadata", {}),
        discovery_config=getattr(args, "discovery_config", {}),
        system_naming_config=getattr(args, "system_naming_config", normalize_system_naming_config({})),
        dependency_hotspots_config=getattr(
            args, "dependency_hotspots_config", normalize_dependency_hotspots_config({})
        ),
    )


def build_render_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        architecture_file=args.architecture_output_file,
        render=args.render,
        struct_output_dir=args.struct_output_dir,
        likec4_output_dir=args.likec4_output_dir,
        likec4_common_path=args.likec4_common_path,
    )
