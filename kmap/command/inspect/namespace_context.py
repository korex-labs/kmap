"""Namespace inspection resource loading and report context."""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from ...inspection.workloads import matching_helm_release_names, related_replicasets_by_deployment, select_workloads
from ...kubernetes import item_map
from ...kubernetes.client import KubectlClient
from ...logging import eprint
from .autoscaling import autoscaling_by_workload
from .runtime_cache import previous_runtime_candidates_by_workload
from .service_catalog import build_internal_alias_to_service, build_service_catalog


@dataclass
class InspectionContext:
    args: argparse.Namespace
    client: Any
    cluster: str
    resources: Dict[str, Any]
    cm_map: Dict[str, Dict[str, Any]]
    sec_map: Dict[str, Dict[str, Any]]
    svc_items: List[Dict[str, Any]]
    ing_items: List[Dict[str, Any]]
    internal_alias_to_service: Dict[str, List[str]]
    previous_runtime_candidates: Dict[tuple[str, str, str, str], List[Dict[str, Any]]]
    autoscaling_by_target: Dict[tuple[str, str], Dict[str, Any]]
    release_names: List[str]
    replicasets_by_deployment: Dict[str, List[str]]


def kubectl_client(args: argparse.Namespace) -> Any:
    return KubectlClient(
        kubectl=args.kubectl,
        helm=args.helm,
        context=getattr(args, "context", ""),
        kubeconfig=getattr(args, "kubeconfig", ""),
        namespace=args.namespace,
        request_timeout=args.request_timeout,
        qps_sleep=args.kubectl_qps_sleep,
        exec_sleep=args.exec_sleep,
    )


def namespace_resources(client: Any, namespace: str) -> Dict[str, Any]:
    try:
        ingress = client.get_json("ingress")
    except Exception:
        ingress = {"items": []}
    return {
        "deploy": client.get_json("deploy"),
        "rs": client.get_json("rs"),
        "sts": client.get_json("sts"),
        "ds": client.get_json("ds"),
        "svc": client.get_json("svc"),
        "ingress": ingress,
        "cm": client.get_json("cm"),
        "secret": client.get_json("secret"),
        "pvc": client.get_json("pvc"),
        "pod": client.get_json("pod"),
        "hpa": client.get_json("hpa"),
        "keda_scaled_object": client.get_json("scaledobject.keda.sh"),
        "helm_releases": client.helm_list(namespace),
    }


def inspection_context(args: argparse.Namespace, out_dir: Path) -> InspectionContext:
    client = kubectl_client(args)
    resources = namespace_resources(client, args.namespace)
    svc_items = resources["svc"].get("items") or []
    match_re = re.compile(args.match_regex)
    service_catalog = build_service_catalog(svc_items, args.namespace)
    return InspectionContext(
        args=args,
        client=client,
        cluster=client.current_context(),
        resources=resources,
        cm_map=item_map(resources["cm"]),
        sec_map=item_map(resources["secret"]),
        svc_items=svc_items,
        ing_items=resources["ingress"].get("items") or [],
        internal_alias_to_service=build_internal_alias_to_service(service_catalog),
        previous_runtime_candidates=previous_runtime_candidates_by_workload(args, out_dir),
        autoscaling_by_target=autoscaling_by_workload(resources["hpa"], resources["keda_scaled_object"]),
        release_names=matching_helm_release_names(resources["helm_releases"], match_re),
        replicasets_by_deployment=related_replicasets_by_deployment(resources["rs"]),
    )


def selected_workloads(context: InspectionContext) -> List[tuple[str, Dict[str, Any]]]:
    args = context.args
    workloads_raw, selection_message = select_workloads(
        deployments=context.resources["deploy"],
        statefulsets=context.resources["sts"],
        daemonsets=context.resources["ds"],
        match_re=re.compile(args.match_regex),
        match_regex=args.match_regex,
        namespace=args.namespace,
    )
    if selection_message:
        eprint(selection_message)
    return workloads_raw


def namespace_report(context: InspectionContext, workloads: List[Dict[str, Any]]) -> Dict[str, Any]:
    args = context.args
    return {
        "cluster": context.cluster,
        "namespace": args.namespace,
        "discovery": {
            "context": getattr(args, "context", "") or context.cluster,
            "kubeconfig": getattr(args, "kubeconfig", ""),
        },
        "helm_releases": context.release_names,
        "workloads": workloads,
    }


__all__ = [
    "InspectionContext",
    "inspection_context",
    "kubectl_client",
    "namespace_report",
    "namespace_resources",
    "selected_workloads",
]
