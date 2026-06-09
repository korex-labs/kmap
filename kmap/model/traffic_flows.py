"""Architecture traffic-flow assembly."""

from typing import Any, Dict, List

from ..identifiers import architecture_id
from ..naming import short_hash


def traffic_flows_from_workloads(
    workloads_by_service_id: Dict[str, Dict[str, Any]],
    workload_primary_container_ids: Dict[str, str],
    workload_primary_instance_ids: Dict[str, str],
) -> List[Dict[str, Any]]:
    traffic_flows = []
    for service_id, svc in sorted(workloads_by_service_id.items()):
        container_id = workload_primary_container_ids.get(service_id, "")
        if not container_id:
            continue
        for index, route in enumerate(svc.get("traffic_routes") or [], start=1):
            traffic_flows.append(
                traffic_flow_entry(
                    service_id=service_id,
                    svc=svc,
                    route=route,
                    index=index,
                    container_id=container_id,
                    instance_id=workload_primary_instance_ids.get(service_id, ""),
                )
            )
    return traffic_flows


def traffic_flow_entry(
    *,
    service_id: str,
    svc: Dict[str, Any],
    route: Dict[str, Any],
    index: int,
    container_id: str,
    instance_id: str,
) -> Dict[str, Any]:
    route_hops = route.get("hops") or []
    return {
        "id": architecture_id("flow", short_hash(f"{service_id}:{index}:{route_hops}", 12)),
        "direction": route.get("direction") or "inbound",
        "service_id": service_id,
        "container_id": container_id,
        "instance_id": instance_id,
        "cluster": svc.get("cluster") or "",
        "namespace": svc.get("namespace") or "",
        "source": route.get("source") or {},
        "hops": route_hops,
        "target": route.get("target") or {},
        "confidence": 0.8,
    }


__all__ = ["traffic_flow_entry", "traffic_flows_from_workloads"]
