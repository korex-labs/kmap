"""Run-all command orchestration."""

import argparse
from pathlib import Path

from ...inventory.namespaces import DEFAULT_CONFIG_DIR
from .discovery import parse_namespace_args, parse_namespace_project_args
from .paths import apply_default_output_paths
from .preflight import preflight_run_all_targets
from .progress import run_all_progress
from .stages import build_combine_args, build_inspect_args, build_normalize_args, build_render_args
from .targets import resolve_run_all_targets, should_use_target_report_stems

INTERRUPTED_EXIT_CODE = 130


def run_all(args: argparse.Namespace) -> int:
    from ...inventory.buckets import write_bucket_report
    from ...inventory.namespaces import render_inventory
    from ..combine import combine_reports
    from ..inspect import namespace as inspect_namespace_module
    from ..normalize import normalize_architecture
    from ..render import render_outputs

    validate_run_all_inspect_format(args)
    namespaces = parse_namespace_args(getattr(args, "namespace", []))
    ns_project_map = parse_namespace_project_args(getattr(args, "namespace_project", []))
    apply_default_output_paths(args, namespaces)
    resolved_targets = resolve_run_all_targets(args, namespaces, ns_project_map)
    use_target_report_stems = should_use_target_report_stems(resolved_targets)
    preflight_rc = preflight_run_all_targets(args, resolved_targets)
    if preflight_rc != 0:
        return preflight_rc

    render_steps = 3
    progress_enabled = getattr(args, "output", "progress") == "progress"
    with run_all_progress(enabled=progress_enabled, total=len(resolved_targets) + 2 + render_steps) as progress:
        try:
            rc = run_inspection_targets(
                args,
                resolved_targets,
                progress,
                inspect_namespace_module.inspect_namespace,
                use_target_report_stems=use_target_report_stems,
            )
            if rc == 0:
                rc = run_progress_stage(
                    progress, combine_reports, build_combine_args(args), "combine failed", "combined dependencies"
                )
            if rc == 0:
                rc = run_progress_stage(
                    progress,
                    normalize_architecture,
                    build_normalize_args(args),
                    "normalize failed",
                    "normalized architecture",
                )
            if rc == 0:
                rc = run_progress_stage(
                    progress, render_outputs, build_render_args(args), "render failed", "rendered outputs"
                )
            if rc == 0:
                write_bucket_report(**bucket_report_kwargs(args))
                progress.advance("wrote bucket artifact")
                rc = run_progress_stage(
                    progress,
                    render_inventory,
                    inventory_args(args),
                    "inventory render failed",
                    "rendered inventory",
                )
            if rc == 0:
                progress.done("done")
            return rc
        except KeyboardInterrupt:
            progress.fail("interrupted")
            return INTERRUPTED_EXIT_CODE


def validate_run_all_inspect_format(args: argparse.Namespace) -> None:
    if args.inspect_format not in {"json", "both"}:
        raise SystemExit("--inspect-format must be json or both when using run-all")


def run_inspection_targets(
    args: argparse.Namespace,
    resolved_targets: list,
    progress,
    inspect_namespace,
    *,
    use_target_report_stems: bool,
) -> int:
    for target in resolved_targets:
        inspect_args = build_inspect_args(args, target, use_target_report_stems=use_target_report_stems)
        rc = inspect_namespace(inspect_args)
        if rc != 0:
            progress.fail(f"inspect failed: {target.namespace}")
            return rc
        progress.advance(f"inspected {target.namespace}")
    return 0


def run_progress_stage(
    progress, stage_func, stage_args: argparse.Namespace, failure_message: str, success_message: str
) -> int:
    rc = stage_func(stage_args)
    if rc != 0:
        progress.fail(failure_message)
        return rc
    progress.advance(success_message)
    return 0


def bucket_report_kwargs(args: argparse.Namespace) -> dict:
    return {
        "reports_dir": Path(args.out_dir),
        "config_dir": config_dir_for_args(args),
        "config_path": getattr(args, "config", ""),
        "product": getattr(args, "product", ""),
        "output_dir": Path(args.bucket_reports_dir),
    }


def inventory_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        config_dir=str(config_dir_for_args(args) if getattr(args, "config", "") else DEFAULT_CONFIG_DIR),
        bucket_artifacts_dir=args.bucket_reports_dir,
        output_dir=args.inventory_output_dir,
        kmap_tool_config=getattr(args, "kmap_tool_config", {}),
    )


def config_dir_for_args(args: argparse.Namespace) -> Path:
    return Path(args.config).parent if getattr(args, "config", "") else Path()


__all__ = [
    "INTERRUPTED_EXIT_CODE",
    "bucket_report_kwargs",
    "config_dir_for_args",
    "inventory_args",
    "run_all",
    "run_inspection_targets",
    "run_progress_stage",
    "validate_run_all_inspect_format",
]
