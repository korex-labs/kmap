"""Discovery target planning for run-all."""

import argparse
from dataclasses import dataclass

from ...config import infer_project_from_namespace, resolve_discovery_target
from .discovery import discovery_target_identity


@dataclass(frozen=True)
class RunAllTarget:
    namespace: str
    project: str
    discovery: dict


def project_for_namespace(args: argparse.Namespace, namespace: str, namespace_projects: dict[str, str]) -> str:
    return (
        namespace_projects.get(namespace)
        or getattr(args, "project", "")
        or infer_project_from_namespace(namespace, args.product)
    )


def discovery_for_namespace(args: argparse.Namespace, namespace: str, project_name: str) -> dict:
    return resolve_discovery_target(
        getattr(args, "discovery_config", {}),
        namespace,
        project_name,
        getattr(args, "kubeconfig", ""),
    )


def run_all_target_for_namespace(
    args: argparse.Namespace,
    namespace: str,
    namespace_projects: dict[str, str],
) -> RunAllTarget:
    project_name = project_for_namespace(args, namespace, namespace_projects)
    discovery_target = discovery_for_namespace(args, namespace, project_name)
    return RunAllTarget(namespace=namespace, project=project_name, discovery=discovery_target)


def resolve_run_all_targets(
    args: argparse.Namespace,
    namespaces: list[str],
    namespace_projects: dict[str, str],
) -> list[RunAllTarget]:
    return [run_all_target_for_namespace(args, namespace, namespace_projects) for namespace in namespaces]


def should_use_target_report_stems(targets: list[RunAllTarget]) -> bool:
    distinct_targets = {discovery_target_identity(target.discovery) for target in targets}
    distinct_targets.discard("")
    return len(distinct_targets) > 1
