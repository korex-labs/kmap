"""LikeC4 deployment route graph rendering."""

from typing import Any, Dict, List

from .common import likec4_alias, likec4_metadata_lines, likec4_quote


def normalized_ingress_path(path: str) -> str:
    text = str(path or "").strip() or "/"
    if text == "/":
        return text
    return text.rstrip("/")


def namespace_flows(
    traffic_flows: List[Dict[str, Any]],
    cluster: Dict[str, Any],
    namespace: Dict[str, Any],
) -> List[Dict[str, Any]]:
    return [
        flow
        for flow in traffic_flows
        if flow.get("cluster") == cluster.get("name") and flow.get("namespace") == namespace.get("name")
    ]


def route_lines(namespace_flows: List[Dict[str, Any]], instance_aliases: Dict[str, str]) -> List[str]:
    route_nodes, route_edges = route_graph(namespace_flows, instance_aliases)
    lines: List[str] = []
    for node in route_nodes.values():
        lines.extend(route_node_lines(node))
    for source_alias, target_alias, label in sorted(route_edges):
        lines.append(f'        {source_alias} -> {target_alias} "{label}"')
    return lines


def route_graph(
    namespace_flows: List[Dict[str, Any]],
    instance_aliases: Dict[str, str],
) -> tuple[Dict[tuple[str, str, str, str], Dict[str, Any]], set[tuple[str, str, str]]]:
    route_nodes: Dict[tuple[str, str, str, str], Dict[str, Any]] = {}
    route_edges: set[tuple[str, str, str]] = set()
    for flow in namespace_flows:
        collect_route_flow(flow, instance_aliases, route_nodes, route_edges)
    return route_nodes, route_edges


def collect_route_flow(
    flow: Dict[str, Any],
    instance_aliases: Dict[str, str],
    route_nodes: Dict[tuple[str, str, str, str], Dict[str, Any]],
    route_edges: set[tuple[str, str, str]],
) -> None:
    previous_alias = ""
    for hop in route_hops(flow):
        node = route_node(hop, route_nodes)
        node_alias = node["alias"]
        record_ingress_raw_path(hop, node)
        if previous_alias:
            route_edges.add((previous_alias, node_alias, "routes"))
        previous_alias = node_alias
    target_alias = instance_aliases.get(flow.get("instance_id") or "")
    if previous_alias and target_alias:
        route_edges.add((previous_alias, target_alias, "selects"))


def route_node(hop: Dict[str, Any], route_nodes: Dict[tuple[str, str, str, str], Dict[str, Any]]) -> Dict[str, Any]:
    hop_type = hop.get("type") or ""
    hop_name = hop.get("name") or hop_type
    raw_path = hop.get("path") or ""
    path = normalized_ingress_path(raw_path) if hop_type == "Ingress" else raw_path
    node_key = (hop_type, hop_name, hop.get("host") or "", path)
    node = route_nodes.get(node_key)
    if node:
        return node

    title = hop_name
    if hop_type == "Ingress" and hop.get("host"):
        title = f"{hop.get('host')}{path}"
    node = {
        "alias": likec4_alias(f"{hop_type}-{hop_name}-{hop.get('host') or ''}-{path}"),
        "kind": "k8s_ingress" if hop_type == "Ingress" else "k8s_service",
        "title": title,
        "type": hop_type,
        "host": hop.get("host") or "",
        "path": path,
        "port": hop.get("port") or "",
        "raw_paths": [],
    }
    route_nodes[node_key] = node
    return node


def route_hops(flow: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [hop for hop in flow.get("hops") or [] if hop.get("type") in {"Ingress", "Service"}]


def record_ingress_raw_path(hop: Dict[str, Any], node: Dict[str, Any]) -> None:
    raw_path = hop.get("path") or ""
    if hop.get("type") == "Ingress" and raw_path and raw_path not in node["raw_paths"]:
        node["raw_paths"].append(raw_path)


def route_node_lines(node: Dict[str, Any]) -> List[str]:
    metadata = [
        ("k8s_kind", node["type"]),
        ("host", node["host"]),
        ("path", node["path"]),
        ("port", node["port"]),
    ]
    raw_paths = node["raw_paths"]
    if len(raw_paths) > 1:
        metadata.append(("raw_paths", ", ".join(raw_paths)))
    lines = [f'        {node["alias"]} = {node["kind"]} "{likec4_quote(node["title"])}" {{']
    lines.extend(likec4_metadata_lines(metadata, indent="          "))
    lines.append("        }")
    return lines


__all__ = [
    "collect_route_flow",
    "namespace_flows",
    "normalized_ingress_path",
    "record_ingress_raw_path",
    "route_graph",
    "route_hops",
    "route_lines",
    "route_node",
    "route_node_lines",
]
