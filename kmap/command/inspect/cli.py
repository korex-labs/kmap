"""CLI wiring for the inspect command."""

import argparse
import os
from typing import Callable

from . import inspect_namespaces


def add_inspect_parser(
    subparsers: argparse._SubParsersAction,
    *,
    default_reports_dir: str,
    default_match_re: str,
    parse_non_negative_float: Callable[[str], float],
    parse_positive_int: Callable[[str], int],
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("inspect", help="Inspect one namespace")
    parser.add_argument("--config", help="YAML config file with product metadata and namespace list")
    parser.add_argument(
        "-n", "--namespace", action="append", default=[], help="Namespace (repeat -n or use comma-separated list)"
    )
    parser.add_argument(
        "--namespace-project", action="append", default=[], help="Per-namespace project mapping (namespace=project)"
    )
    parser.add_argument("--project", default=os.environ.get("KMAP_PROJECT", ""))
    parser.add_argument("--product", default=os.environ.get("KMAP_PRODUCT", "product"))
    parser.add_argument(
        "--kubeconfig",
        default="",
        help="Path to kubectl config file (defaults to KUBECONFIG or ~/.kube/config)",
    )
    parser.add_argument("--kubectl", default=os.environ.get("KUBECTL_BIN", "kubectl"))
    parser.add_argument("--helm", default=os.environ.get("HELM_BIN", "helm"))
    parser.add_argument("--out-dir", default=os.environ.get("OUT_DIR", default_reports_dir))
    parser.add_argument("--request-timeout", default=os.environ.get("REQUEST_TIMEOUT", "15s"))
    parser.add_argument("--exec-sleep", type=parse_non_negative_float, default=os.environ.get("EXEC_SLEEP", "0.4"))
    parser.add_argument(
        "--kubectl-qps-sleep",
        type=parse_non_negative_float,
        default=os.environ.get("KUBECTL_QPS_SLEEP", "0.15"),
    )
    parser.add_argument("--match-regex", default=os.environ.get("MATCH_REGEX", default_match_re))
    parser.add_argument("--no-exec", action="store_true", default=os.environ.get("NO_EXEC", "0") == "1")
    parser.add_argument(
        "--max-exec-pods-per-workload",
        type=parse_positive_int,
        default=os.environ.get("MAX_EXEC_PODS_PER_WORKLOAD", "1"),
    )
    parser.add_argument("--format", choices=["text", "json", "both"], default=os.environ.get("REPORT_FORMAT", "both"))
    parser.add_argument(
        "--data-mode",
        choices=["raw", "sanitized", "mocked"],
        default=os.environ.get("KMAP_DATA_MODE", "sanitized"),
    )
    parser.add_argument("--mock-seed", default=os.environ.get("KMAP_MOCK_SEED", ""))
    parser.set_defaults(func=inspect_namespaces)
    return parser


__all__ = ["add_inspect_parser"]
