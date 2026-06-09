from kmap.render.likec4.deployment import deployment_render_context, render_likec4_deployment, route_graph, route_hops


def test_deployment_render_context_indexes_architecture_inputs():
    architecture = {
        "projects": [{"id": "prj.pay", "name": "pay"}],
        "systems": [{"id": "sys.pay", "title": "Pay"}],
        "containers": [{"id": "ctr.pay.api", "system_id": "sys.pay", "title": "API"}],
        "traffic_flows": [{"id": "flow.1"}],
    }

    context = deployment_render_context(architecture)

    assert context.projects_by_id == {"prj.pay": {"id": "prj.pay", "name": "pay"}}
    assert context.systems_by_id == {"sys.pay": {"id": "sys.pay", "title": "Pay"}}
    assert context.containers_by_id == {"ctr.pay.api": {"id": "ctr.pay.api", "system_id": "sys.pay", "title": "API"}}
    assert context.refs["ctr.pay.api"] == "sys_pay.ctr_pay_api"
    assert context.traffic_flows == [{"id": "flow.1"}]


def test_route_graph_collects_route_nodes_edges_and_raw_ingress_paths():
    flow = {
        "instance_id": "pod-api",
        "hops": [
            {"type": "External", "name": "ignored"},
            {"type": "Ingress", "name": "api-ing", "host": "api.example.com", "path": "/orders"},
            {"type": "Service", "name": "api-svc", "port": 80},
        ],
    }
    duplicate_path_flow = {
        "instance_id": "pod-api",
        "hops": [
            {"type": "Ingress", "name": "api-ing", "host": "api.example.com", "path": "/orders/"},
            {"type": "Service", "name": "api-svc", "port": 80},
        ],
    }

    nodes, edges = route_graph([flow, duplicate_path_flow], {"pod-api": "pod_api"})

    assert route_hops(flow) == flow["hops"][1:]
    assert [node["type"] for node in nodes.values()] == ["Ingress", "Service"]
    ingress = next(node for node in nodes.values() if node["type"] == "Ingress")
    assert ingress["path"] == "/orders"
    assert ingress["raw_paths"] == ["/orders", "/orders/"]
    assert edges == {
        ("Ingress_api_ing_api_example_com_orders", "Service_api_svc", "routes"),
        ("Service_api_svc", "pod_api", "selects"),
    }


def test_render_likec4_deployment_links_instances_to_containers():
    rendered = render_likec4_deployment(
        {
            "product": {"name": "demo"},
            "projects": [{"id": "prj.pay", "name": "pay", "title": "Payments"}],
            "systems": [{"id": "sys.pay", "title": "Pay"}],
            "containers": [{"id": "ctr.pay.api", "system_id": "sys.pay", "title": "API"}],
            "traffic_flows": [
                {
                    "id": "flow.1",
                    "cluster": "cluster-1",
                    "namespace": "payments",
                    "instance_id": "pod-api",
                    "direction": "inbound",
                    "source": {"type": "External", "name": "api.example.com"},
                    "hops": [
                        {"type": "Ingress", "name": "api-ing", "host": "api.example.com", "path": "/"},
                        {"type": "Service", "name": "api-svc", "port": 80},
                        {"type": "Workload", "name": "api"},
                    ],
                }
            ],
        },
        {
            "env": "prod",
            "clusters": [
                {
                    "id": "cluster-1",
                    "name": "cluster-1",
                    "namespaces": [
                        {
                            "id": "ns-pay",
                            "name": "payments",
                            "project_id": "prj.pay",
                            "instances": [
                                {
                                    "id": "pod-api",
                                    "name": "api",
                                    "container_id": "ctr.pay.api",
                                    "node_kind": "workload",
                                }
                            ],
                        }
                    ],
                }
            ],
        },
    )

    assert 'demo_prod = Stage "prod"' in rendered
    assert 'cluster_1 = k8s_cluster "cluster-1"' in rendered
    assert 'ns_pay = k8s_namespace "payments"' in rendered
    assert 'k8s_ingress "api.example.com/"' in rendered
    assert 'k8s_service "api-svc"' in rendered
    assert '-> pod_api "selects"' in rendered
    assert 'pod_api_container = k8s_container "API"' in rendered
    assert "instanceOf sys_pay.ctr_pay_api" in rendered


def test_render_likec4_deployment_groups_workload_containers_under_one_pod():
    rendered = render_likec4_deployment(
        {
            "product": {"name": "demo"},
            "projects": [{"id": "prj.pay", "name": "pay", "title": "Payments"}],
            "systems": [{"id": "sys.pay", "title": "Pay"}],
            "containers": [
                {
                    "id": "ctr.pay.api.app",
                    "system_id": "sys.pay",
                    "title": "App",
                    "kind": "container",
                    "runtime": {"images": ["example/app:1"], "container_ports": ["8080/TCP"]},
                    "name_source": {"raw_container_name": "app"},
                },
                {"id": "ctr.pay.api.hydra", "system_id": "sys.pay", "title": "Hydra", "kind": "container"},
            ],
            "traffic_flows": [],
        },
        {
            "env": "prod",
            "clusters": [
                {
                    "id": "cluster-1",
                    "name": "cluster-1",
                    "namespaces": [
                        {
                            "id": "ns-pay",
                            "name": "payments",
                            "project_id": "prj.pay",
                            "instances": [
                                {
                                    "id": "pod-api-app-abc",
                                    "name": "api",
                                    "container_id": "ctr.pay.api.app",
                                    "node_kind": "k8s_pod",
                                    "runtime": {
                                        "replicas_desired": [2],
                                        "service_ports": ["8080/TCP"],
                                        "services": ["api-svc"],
                                        "storage_types": ["configMap"],
                                        "service_account": ["api-sa"],
                                        "scaling_enabled": ["true"],
                                        "scaling_type": ["keda"],
                                        "min_replicas": ["2"],
                                        "max_replicas": ["20"],
                                        "scale_formula": ["ceil(RPS / 150)"],
                                    },
                                },
                                {
                                    "id": "pod-api-hydra-abc",
                                    "name": "api",
                                    "container_id": "ctr.pay.api.hydra",
                                    "node_kind": "k8s_pod",
                                },
                            ],
                        }
                    ],
                }
            ],
        },
    )

    assert rendered.count('= k8s_pod "Pay"') == 1
    assert 'pod_api_app_abc = k8s_pod "Pay"' in rendered
    assert 'workload "api"' in rendered
    assert 'pod_api_app_abc_container = k8s_container "App"' in rendered
    assert 'pod_api_hydra_abc_container = k8s_container "Hydra"' in rendered
    assert "instanceOf sys_pay.ctr_pay_api_app" in rendered
    assert "instanceOf sys_pay.ctr_pay_api_hydra" in rendered
    assert 'ops_runtime "replicas desired: 2"' in rendered
    assert 'ops_network "services: api-svc; service ports: 8080/TCP"' in rendered
    assert 'ops_storage "types: configMap"' in rendered
    assert 'ops_security "service account: api-sa"' in rendered
    assert 'ops_scaling "enabled: true; type: keda; min: 2; max: 20; formula: ceil(RPS / 150)"' in rendered
    assert rendered.count("ceil(RPS / 150)") == 1
    assert rendered.count("multiple true") == 2
    assert 'container_image "example/app:1"' in rendered
    assert 'ops_network "container ports: 8080/TCP"' in rendered
    assert 'container_source "app"' in rendered
    assert rendered.count('container_image "example/app:1"') == 1
    assert rendered.count("container ports: 8080/TCP") == 1


def test_render_likec4_deployment_keeps_raw_workload_title_when_system_title_is_duplicated():
    rendered = render_likec4_deployment(
        {
            "product": {"name": "demo"},
            "projects": [{"id": "prj.pay", "name": "pay", "title": "Payments"}],
            "systems": [{"id": "sys.pay", "title": "Pay"}],
            "containers": [
                {"id": "ctr.pay.api", "system_id": "sys.pay", "title": "App"},
                {"id": "ctr.pay.worker", "system_id": "sys.pay", "title": "Worker"},
            ],
            "traffic_flows": [],
        },
        {
            "env": "prod",
            "clusters": [
                {
                    "id": "cluster-1",
                    "name": "cluster-1",
                    "namespaces": [
                        {
                            "id": "ns-pay",
                            "name": "payments",
                            "project_id": "prj.pay",
                            "instances": [
                                {"id": "pod-api", "name": "api", "container_id": "ctr.pay.api"},
                                {"id": "pod-worker", "name": "worker", "container_id": "ctr.pay.worker"},
                            ],
                        }
                    ],
                }
            ],
        },
    )

    assert 'pod_api = k8s_pod "api"' in rendered
    assert 'pod_worker = k8s_pod "worker"' in rendered


def test_render_likec4_deployment_merges_trailing_slash_ingress_paths():
    architecture = {
        "product": {"name": "demo"},
        "projects": [],
        "systems": [{"id": "sys.pay", "title": "Pay"}],
        "containers": [{"id": "ctr.pay.api", "system_id": "sys.pay", "title": "API"}],
        "traffic_flows": [
            {
                "id": "flow.1",
                "cluster": "cluster-1",
                "namespace": "payments",
                "instance_id": "pod-api",
                "hops": [
                    {"type": "Ingress", "name": "api-ing", "host": "api.example.com", "path": "/orders"},
                    {"type": "Service", "name": "api-svc", "port": 80},
                ],
            },
            {
                "id": "flow.2",
                "cluster": "cluster-1",
                "namespace": "payments",
                "instance_id": "pod-api",
                "hops": [
                    {"type": "Ingress", "name": "api-ing", "host": "api.example.com", "path": "/orders/"},
                    {"type": "Service", "name": "api-svc", "port": 80},
                ],
            },
        ],
    }
    deployment = {
        "env": "prod",
        "clusters": [
            {
                "id": "cluster-1",
                "name": "cluster-1",
                "namespaces": [
                    {
                        "id": "ns-pay",
                        "name": "payments",
                        "instances": [{"id": "pod-api", "name": "api", "container_id": "ctr.pay.api"}],
                    }
                ],
            }
        ],
    }

    rendered = render_likec4_deployment(architecture, deployment)

    assert rendered.count('= k8s_ingress "api.example.com/orders"') == 1
    assert 'path "/orders"' in rendered
    assert 'raw_paths "/orders, /orders/"' in rendered
    assert "api_example_com_orders = k8s_ingress" in rendered
