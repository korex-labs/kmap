"""Combine command orchestration."""

import argparse
from pathlib import Path
from typing import Any, Dict, List

from ...io import dump_json, load_required_json_file
from ...logging import eprint
from .io import write_dependency_relations
from .relations import build_dependency_rows


def combine_reports(args: argparse.Namespace) -> int:
    reports_dir = Path(args.reports_dir)
    services = load_report_workloads(reports_dir)
    final_rows = build_dependency_rows(services, getattr(args, "system_naming_config", None))

    out_path = Path(args.output_file)
    write_dependency_relations(out_path, final_rows)

    if args.json_output_file:
        dump_json(Path(args.json_output_file), final_rows)

    eprint(f"[kmap] wrote dependency map: {out_path}")
    return 0


def load_report_workloads(reports_dir: Path) -> List[Dict[str, Any]]:
    json_files = sorted(reports_dir.glob("*.report.json"))
    if not json_files:
        raise SystemExit(f"No *.report.json found in {reports_dir}")

    services = []
    for path in json_files:
        report = load_required_json_file(path)
        services.extend(report.get("workloads", []))
    return services


__all__ = ["combine_reports", "load_report_workloads"]
