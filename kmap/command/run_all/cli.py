"""CLI wiring for the run-all command."""

import argparse
import os
from typing import Callable

from ...inventory.buckets import DEFAULT_BUCKET_REPORTS_DIR
from ...inventory.namespaces import DEFAULT_INVENTORY_DIR
from . import run_all


def add_run_all_parser(
    subparsers: argparse._SubParsersAction,
    *,
    default_reports_dir: str,
    default_dependencies_file: str,
    default_architecture_file: str,
    default_match_re: str,
    parse_non_negative_float: Callable[[str], float],
    parse_positive_int: Callable[[str], int],
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("run-all", help="Run inspect, combine, normalize, and render")
    parser.add_argument("--config", help="YAML config file with product metadata and namespace list")
    parser.add_argument(
        "-n", "--namespace", action="append", default=[], help="Namespace (repeat -n or use comma-separated list)"
    )
    parser.add_argument(
        "--namespace-project", action="append", default=[], help="Per-namespace project mapping (namespace=project)"
    )
    parser.add_argument(
        "--kubeconfig",
        default="",
        help="Path to kubectl config file (defaults to KUBECONFIG or ~/.kube/config)",
    )
    parser.add_argument("--kubectl", default=os.environ.get("KUBECTL_BIN", "kubectl"))
    parser.add_argument("--helm", default=os.environ.get("HELM_BIN", "helm"))
    parser.add_argument("--out-dir", default=os.environ.get("OUT_DIR", default_reports_dir))
    parser.add_argument("--request-timeout", default=os.environ.get("REQUEST_TIMEOUT", "15s"))
    parser.add_argument(
        "--skip-cluster-preflight",
        action="store_false",
        dest="cluster_preflight",
        default=os.environ.get("KMAP_SKIP_CLUSTER_PREFLIGHT", "0") != "1",
        help="Skip the lightweight Kubernetes API reachability check before run-all inspection",
    )
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
    parser.add_argument("--inspect-format", choices=["json", "both"], default=os.environ.get("REPORT_FORMAT", "both"))
    parser.add_argument(
        "--data-mode",
        choices=["raw", "sanitized", "mocked"],
        default=os.environ.get("KMAP_DATA_MODE", "sanitized"),
    )
    parser.add_argument("--mock-seed", default=os.environ.get("KMAP_MOCK_SEED", ""))
    parser.add_argument(
        "--output",
        choices=["progress", "lines"],
        default=os.environ.get("KMAP_OUTPUT", "progress"),
        help="Output mode: progress bar by default, or line-by-line logs",
    )
    parser.add_argument("--dependencies-file", default=os.environ.get("OUTPUT_FILE", default_dependencies_file))
    parser.add_argument("--dependencies-json-output-file", default=os.environ.get("JSON_OUTPUT_FILE"))
    parser.add_argument("--architecture-output-file", default=default_architecture_file)
    parser.add_argument(
        "--bucket-reports-dir",
        default=os.environ.get("KMAP_BUCKET_REPORTS_DIR", str(DEFAULT_BUCKET_REPORTS_DIR)),
        help="Directory for sanitized per-product bucket artifacts",
    )
    parser.add_argument(
        "--inventory-output-dir",
        default=os.environ.get("KMAP_INVENTORY_OUTPUT_DIR", str(DEFAULT_INVENTORY_DIR)),
        help="Directory for generated inventory HTML files",
    )
    parser.add_argument(
        "--render",
        choices=["structurizr", "likec4", "both"],
        default=os.environ.get("KMAP_RENDER", "both"),
        help="Renderer to run after normalize",
    )
    parser.add_argument("--struct-output-dir", default=os.environ.get("STRUCTURIZR_OUTPUT_DIR", ""))
    parser.add_argument("--likec4-output-dir", default=os.environ.get("LIKEC4_OUTPUT_DIR", ""))
    parser.add_argument(
        "--likec4-common-path",
        default=os.environ.get("LIKEC4_COMMON_PATH", "../common"),
        help="Relative path to LikeC4 common layer from generated likec4.config.json",
    )
    parser.add_argument("--org", default=os.environ.get("KMAP_ORG", "org"))
    parser.add_argument("--product", default=os.environ.get("KMAP_PRODUCT", "product"))
    parser.add_argument("--project", default=os.environ.get("KMAP_PROJECT", ""))
    parser.add_argument("--env", default=os.environ.get("KMAP_ENV", "prod"))
    parser.set_defaults(func=run_all)
    return parser


__all__ = ["add_run_all_parser"]
