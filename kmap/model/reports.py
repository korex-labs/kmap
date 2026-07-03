"""Input report loading for normalized architecture model construction."""

from pathlib import Path
from typing import Any

from ..io import load_required_json_file


def load_workloads_from_reports(reports_dir: Path) -> tuple[list[Path], list[dict[str, Any]]]:
    json_files = sorted(reports_dir.glob("*.report.json"))
    if not json_files:
        raise SystemExit(f"No *.report.json found in {reports_dir}")

    workloads: list[dict[str, Any]] = []
    for path in json_files:
        workloads.extend(workloads_from_report(load_required_json_file(path)))

    return json_files, workloads


def workloads_from_report(report: dict[str, Any]) -> list[dict[str, Any]]:
    report_discovery = dict(report.get("discovery") or {})
    report_workloads = report.get("workloads", [])
    if not isinstance(report_workloads, list):
        raise SystemExit("Invalid report workloads: expected list")
    workloads = []
    for workload in report_workloads:
        if not isinstance(workload, dict):
            raise SystemExit("Invalid report workload: expected object")
        item = dict(workload)
        if report_discovery:
            item["discovery"] = report_discovery
        workloads.append(item)
    return workloads


__all__ = ["load_workloads_from_reports", "workloads_from_report"]
