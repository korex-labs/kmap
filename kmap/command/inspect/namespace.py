"""Namespace inspection orchestration."""

import argparse
from pathlib import Path
from typing import Any, Dict, List

from ...config import infer_project_from_namespace, resolve_discovery_target
from ...inspection.sanitization import sanitize_report_for_persistence
from ...io import dump_json, ensure_dir, write_text_atomic
from ...logging import eprint
from ..run_all.discovery import (
    discovery_target_identity,
    parse_namespace_args,
    parse_namespace_project_args,
    report_stem_for_namespace,
)
from .namespace_context import inspection_context, namespace_report, selected_workloads
from .namespace_workloads import build_inspected_workload_entry
from .report import summarize_text_report
from .runtime_cache import namespace_report_path


def _write_namespace_report(args: argparse.Namespace, out_dir: Path, report: Dict[str, Any]) -> None:
    persisted_report = sanitize_report_for_persistence(
        report,
        getattr(args, "data_mode", "sanitized"),
        getattr(args, "mock_seed", ""),
    )
    if args.format in {"json", "both"}:
        dump_json(namespace_report_path(args, out_dir), persisted_report)
    if args.format in {"text", "both"}:
        report_stem = getattr(args, "report_stem", "") or args.namespace
        write_text_atomic(out_dir / f"{report_stem}.report.txt", summarize_text_report(persisted_report))


def inspect_namespace(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    ensure_dir(out_dir)
    context = inspection_context(args, out_dir)
    workloads_raw = selected_workloads(context)

    workloads = [
        build_inspected_workload_entry(
            context=context,
            kind=kind,
            workload=workload,
        )
        for kind, workload in workloads_raw
    ]
    report = namespace_report(context, workloads)
    _write_namespace_report(args, out_dir, report)
    eprint(f"[kmap] wrote reports for namespace {args.namespace} into {out_dir}")
    return 0


def inspect_namespaces(args: argparse.Namespace) -> int:
    resolved_targets = _resolved_namespace_targets(args)
    use_target_report_stems = _use_target_report_stems(resolved_targets)

    from . import inspect_namespace as inspect_namespace_func

    for ns, project_name, discovery_target in resolved_targets:
        ns_args = _namespace_inspect_args(args, ns, project_name, discovery_target, use_target_report_stems)
        rc = inspect_namespace_func(ns_args)
        if rc != 0:
            return rc
    return 0


def _resolved_namespace_targets(args: argparse.Namespace) -> List[tuple[str, str, Dict[str, Any]]]:
    namespaces = parse_namespace_args(getattr(args, "namespace", []))
    ns_project_map = parse_namespace_project_args(getattr(args, "namespace_project", []))
    return [_namespace_target(args, ns, ns_project_map) for ns in namespaces]


def _namespace_target(
    args: argparse.Namespace,
    namespace: str,
    ns_project_map: Dict[str, str],
) -> tuple[str, str, Dict[str, Any]]:
    project_name = (
        ns_project_map.get(namespace)
        or getattr(args, "project", "")
        or infer_project_from_namespace(namespace, getattr(args, "product", ""))
    )
    discovery_target = resolve_discovery_target(
        getattr(args, "discovery_config", {}),
        namespace,
        project_name,
        getattr(args, "kubeconfig", ""),
    )
    return namespace, project_name, discovery_target


def _use_target_report_stems(resolved_targets: List[tuple[str, str, Dict[str, Any]]]) -> bool:
    distinct_targets = {discovery_target_identity(target) for _, _, target in resolved_targets}
    distinct_targets.discard("")
    return len(distinct_targets) > 1


def _namespace_inspect_args(
    args: argparse.Namespace,
    namespace: str,
    project_name: str,
    discovery_target: Dict[str, Any],
    use_target_report_stems: bool,
) -> argparse.Namespace:
    return argparse.Namespace(
        namespace=namespace,
        project=project_name,
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
        format=args.format,
        data_mode=args.data_mode,
        mock_seed=args.mock_seed,
        report_stem=report_stem_for_namespace(namespace, discovery_target, use_target_report_stems),
    )


__all__ = ["inspect_namespace", "inspect_namespaces"]
