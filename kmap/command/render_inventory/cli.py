"""CLI wiring for the render-inventory command."""

import argparse
import os

from ...inventory.buckets import DEFAULT_BUCKET_REPORTS_DIR
from ...inventory.full_discovery import DEFAULT_FULL_DISCOVERY_REPORTS_DIR
from ...inventory.namespaces import DEFAULT_CONFIG_DIR, DEFAULT_INVENTORY_DIR, render_inventory


def add_render_inventory_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "render-inventory",
        help="Render Inventory/namespaces.html and Inventory/buckets.html",
    )
    parser.add_argument("--config-dir", default=str(DEFAULT_CONFIG_DIR), help="Directory with product YAML configs")
    parser.add_argument(
        "--bucket-artifacts-dir",
        default=str(DEFAULT_BUCKET_REPORTS_DIR),
        help="Directory with committed per-product bucket artifact JSON files",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_INVENTORY_DIR), help="Inventory HTML output directory")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run live discovery for --cluster and write per-cluster inventory fragments/pages",
    )
    parser.add_argument("--cluster", default="", help="Kubernetes context/cluster to discover when --full is used")
    parser.add_argument("--fragment-id", default="", help="Fragment id for live discovery output")
    parser.add_argument(
        "--full-reports-dir",
        default=os.environ.get("KMAP_FULL_INVENTORY_REPORTS_DIR", str(DEFAULT_FULL_DISCOVERY_REPORTS_DIR)),
        help="Temporary directory for live discovery namespace reports",
    )
    parser.add_argument(
        "--kubeconfig",
        default="",
        help="Path to kubectl config file (defaults to KUBECONFIG or ~/.kube/config)",
    )
    parser.add_argument("--kubectl", default=os.environ.get("KUBECTL_BIN", "kubectl"))
    parser.add_argument("--helm", default=os.environ.get("HELM_BIN", "helm"))
    parser.add_argument("--request-timeout", default=os.environ.get("REQUEST_TIMEOUT", "15s"))
    parser.add_argument("--exec-sleep", type=float, default=os.environ.get("EXEC_SLEEP", "0.4"))
    parser.add_argument("--kubectl-qps-sleep", type=float, default=os.environ.get("KUBECTL_QPS_SLEEP", "0.15"))
    parser.add_argument("--match-regex", default=os.environ.get("MATCH_REGEX", r"(^|[-_.])(main|master)([-_.]|$)"))
    parser.add_argument("--no-exec", action="store_true", default=os.environ.get("NO_EXEC", "0") == "1")
    parser.add_argument(
        "--max-exec-pods-per-workload",
        type=int,
        default=os.environ.get("MAX_EXEC_PODS_PER_WORKLOAD", "1"),
    )
    parser.add_argument(
        "--inventory-exec-timeout",
        type=float,
        default=os.environ.get("KMAP_INVENTORY_EXEC_TIMEOUT", "5"),
        help="Timeout in seconds for each full-inventory runtime exec call",
    )
    parser.add_argument(
        "--inventory-exec-attempts",
        type=int,
        default=os.environ.get("KMAP_INVENTORY_EXEC_ATTEMPTS", "1"),
        help="Retry attempts for each full-inventory runtime exec call",
    )
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
        help="Output mode for live discovery progress",
    )
    parser.set_defaults(func=render_inventory)
    return parser


__all__ = ["add_render_inventory_parser"]
