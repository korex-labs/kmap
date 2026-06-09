"""Report assembly helpers for namespace inspection."""

import json
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class WorkloadReportEntryContext:
    cluster: str
    namespace: str
    project: str
    kind: str
    service_name: str
    service_id: str
    selector: Dict[str, str]
    app_service: str
    app_service_source: Dict[str, Any]
    container_context: Dict[str, Any]
    network_context: Dict[str, Any]
    storage_context: Dict[str, Any]
    observability_context: Dict[str, Any]
    security_context: Dict[str, Any]
    scheduling_context: Dict[str, Any]
    runtime_status: Dict[str, Any]
    release_names: List[str]
    replicasets_by_deployment: Dict[str, List[str]]
    dependency_candidates: List[Dict[str, Any]]
    bucket_candidates: List[Dict[str, Any]] | None = None
    autoscaling: Dict[str, Any] | None = None


def summarize_text_report(report: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"ClusterContext: {report['cluster']}")
    lines.append(f"Namespace: {report['namespace']}")
    lines.append("")
    for wk in report.get("workloads", []):
        lines.append("=== SERVICE BEGIN ===")
        lines.append(f"ServiceId: {wk['service_id']}")
        lines.append(f"Cluster: {wk['cluster']}")
        lines.append(f"Namespace: {wk['namespace']}")
        lines.append(f"Kind: {wk['kind']}")
        lines.append(f"Name: {wk['service_name']}")
        lines.append(f"AppService: {wk.get('app_service', '')}")
        lines.append(f"AppServiceSource: {json.dumps(wk.get('app_service_source') or {}, ensure_ascii=False)}")
        lines.append(f"Containers: {','.join(c.get('name', '') for c in wk.get('containers', []) if c.get('name'))}")
        lines.append(f"Release: {wk.get('release', '')}")
        if wk.get("autoscaling"):
            lines.append(f"Autoscaling: {json.dumps(wk.get('autoscaling') or {}, ensure_ascii=False)}")
        lines.append(f"ReplicaSets: {','.join(wk.get('replicasets', []))}")
        lines.append(f"StatefulSets: {','.join(wk.get('statefulsets', []))}")
        lines.append(f"DaemonSets: {','.join(wk.get('daemonsets', []))}")
        lines.append("ServedEntrypoints:")
        lines.extend(f"  - {json.dumps(ep, ensure_ascii=False)}" for ep in wk.get("entrypoints", []))
        lines.append("Dependencies:")
        lines.extend(
            (
                f"  - source={dep.get('source')} source_name={dep.get('source_name')} "
                f"var={dep.get('var')} key={dep.get('key')} class={dep.get('class')} value={dep.get('value')}"
            )
            for dep in wk.get("dependency_candidates", [])
        )
        lines.append("Buckets:")
        lines.extend(
            (
                f"  - source={bucket.get('source')} source_name={bucket.get('source_name')} "
                f"var={bucket.get('var')} bucket={bucket.get('bucket')} endpoint={bucket.get('endpoint')} "
                f"confidence={bucket.get('confidence')}"
            )
            for bucket in wk.get("bucket_candidates", [])
        )
        lines.append("=== SERVICE END ===")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_workload_report_entry(**entry_options: Any) -> Dict[str, Any]:
    return workload_report_entry(
        WorkloadReportEntryContext(
            cluster=entry_options["cluster"],
            namespace=entry_options["namespace"],
            project=entry_options["project"],
            kind=entry_options["kind"],
            service_name=entry_options["service_name"],
            service_id=entry_options["service_id"],
            selector=entry_options["selector"],
            app_service=entry_options["app_service"],
            app_service_source=entry_options["app_service_source"],
            container_context=entry_options["container_context"],
            network_context=entry_options["network_context"],
            storage_context=entry_options["storage_context"],
            observability_context=entry_options["observability_context"],
            security_context=entry_options["security_context"],
            scheduling_context=entry_options["scheduling_context"],
            runtime_status=entry_options["runtime_status"],
            release_names=entry_options["release_names"],
            replicasets_by_deployment=entry_options["replicasets_by_deployment"],
            dependency_candidates=entry_options["dependency_candidates"],
            bucket_candidates=entry_options.get("bucket_candidates"),
            autoscaling=entry_options.get("autoscaling"),
        )
    )


def workload_report_entry(context: WorkloadReportEntryContext) -> Dict[str, Any]:
    referenced_configmaps = context.container_context["referenced_configmaps"]
    referenced_secrets = context.container_context["referenced_secrets"]
    return {
        "service_id": context.service_id,
        "cluster": context.cluster,
        "namespace": context.namespace,
        "project": context.project,
        "kind": context.kind,
        "service_name": context.service_name,
        "app_service": context.app_service,
        "app_service_source": context.app_service_source,
        "containers": context.container_context["inventory"],
        "runtime": context.runtime_status,
        "autoscaling": dict(context.autoscaling or {}),
        "release": matching_release_name(context.release_names, context.service_name),
        "selector": context.selector,
        **workload_lineage(context.kind, context.service_name, context.replicasets_by_deployment),
        "services": sorted(context.network_context["services"]),
        "ingresses": sorted(context.network_context["ingresses"]),
        "entrypoints": context.network_context["entrypoints"],
        "traffic_routes": context.network_context["traffic_routes"],
        "storage": context.storage_context,
        "observability": context.observability_context,
        "security": context.security_context,
        "scheduling": context.scheduling_context,
        "referenced_configmaps": sorted(referenced_configmaps),
        "referenced_secrets": sorted(referenced_secrets),
        "dependency_candidates": context.dependency_candidates,
        "bucket_candidates": list(context.bucket_candidates or []),
    }


def matching_release_name(release_names: List[str], service_name: str) -> str:
    return next((release for release in release_names if release and release in service_name), "")


def workload_lineage(
    kind: str,
    service_name: str,
    replicasets_by_deployment: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    return {
        "replicasets": replicasets_by_deployment.get(service_name, []) if kind == "Deployment" else [],
        "statefulsets": [service_name] if kind == "StatefulSet" else [],
        "daemonsets": [service_name] if kind == "DaemonSet" else [],
    }


__all__ = [
    "WorkloadReportEntryContext",
    "build_workload_report_entry",
    "matching_release_name",
    "summarize_text_report",
    "workload_lineage",
    "workload_report_entry",
]
