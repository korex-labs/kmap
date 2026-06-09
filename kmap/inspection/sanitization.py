"""Report sanitization helpers for persisted inspection artifacts."""

from typing import Any, Dict

from .bucket_sanitization import sanitize_bucket_candidate
from .dependency_sanitization import sanitize_dependency_candidate
from .sanitization_mocking import (
    mock_entrypoint,
    mock_selector,
    mock_traffic_route,
    mocked_report_identity_fields,
    mocked_workload_identity_fields,
    mocked_workload_runtime_reference_fields,
    sanitize_name_list,
)


def sanitize_report_for_persistence(report: Dict[str, Any], data_mode: str, mock_seed: str = "") -> Dict[str, Any]:
    if data_mode == "raw":
        return raw_report_for_persistence(report)
    return sanitized_report_for_persistence(report, data_mode, mock_seed)


def raw_report_for_persistence(report: Dict[str, Any]) -> Dict[str, Any]:
    return report


def sanitized_report_for_persistence(report: Dict[str, Any], data_mode: str, mock_seed: str = "") -> Dict[str, Any]:
    sanitized = sanitized_report_shell(report)
    if data_mode == "mocked":
        sanitized.update(mocked_report_identity_fields(report, mock_seed))
    for workload in report.get("workloads", []):
        sanitized["workloads"].append(sanitize_workload_for_persistence(workload, data_mode, mock_seed))
    return sanitized


def sanitized_report_shell(report: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "cluster": report.get("cluster", ""),
        "namespace": report.get("namespace", ""),
        "discovery": dict(report.get("discovery") or {}),
        "helm_releases": list(report.get("helm_releases", [])),
        "workloads": [],
    }


def sanitize_workload_for_persistence(workload: Dict[str, Any], data_mode: str, mock_seed: str) -> Dict[str, Any]:
    workload_copy = workload_copy_for_persistence(workload, data_mode)
    if data_mode == "mocked":
        workload_copy.update(mocked_workload_identity_fields(workload, mock_seed))
        workload_copy.update(mocked_workload_runtime_reference_fields(workload, mock_seed))
    workload_copy.update(sensitive_workload_fields(workload, data_mode, mock_seed))
    return workload_copy


def workload_copy_for_persistence(workload: Dict[str, Any], data_mode: str) -> Dict[str, Any]:
    workload_copy = dict(workload)
    if data_mode != "mocked":
        workload_copy["referenced_configmaps"] = list(workload.get("referenced_configmaps", []))
    return workload_copy


def sensitive_workload_fields(workload: Dict[str, Any], data_mode: str, mock_seed: str = "") -> Dict[str, Any]:
    return {
        "referenced_secrets": sanitize_name_list(
            workload.get("referenced_secrets", []), "secret", data_mode, mock_seed
        ),
        "runtime": dict(workload.get("runtime") or {}),
        "dependency_candidates": [
            sanitize_dependency_candidate(dep, data_mode, mock_seed)
            for dep in (workload.get("dependency_candidates") or [])
        ],
        "bucket_candidates": [
            sanitize_bucket_candidate(bucket, data_mode, mock_seed)
            for bucket in (workload.get("bucket_candidates") or [])
        ],
    }


__all__ = [
    "mock_entrypoint",
    "mock_selector",
    "mock_traffic_route",
    "mocked_report_identity_fields",
    "mocked_workload_identity_fields",
    "mocked_workload_runtime_reference_fields",
    "raw_report_for_persistence",
    "sanitize_name_list",
    "sanitize_report_for_persistence",
    "sanitized_report_for_persistence",
    "sensitive_workload_fields",
    "workload_copy_for_persistence",
]
