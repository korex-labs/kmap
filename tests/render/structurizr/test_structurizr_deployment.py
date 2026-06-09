from kmap.render.structurizr.deployment import render_structurizr_deployment


def test_structurizr_deployment_groups_workload_containers_under_one_pod():
    rendered = render_structurizr_deployment(
        {
            "product": {"name": "demo"},
            "projects": [{"id": "prj.pay", "name": "pay", "title": "Payments"}],
            "systems": [{"id": "sys.pay", "project_id": "prj.pay", "title": "Pay"}],
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
                                        "scaling_enabled": ["true"],
                                        "scaling_type": ["hpa"],
                                        "min_replicas": ["2"],
                                        "max_replicas": ["20"],
                                        "scale_formula": ["cpu averageUtilization 75"],
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

    assert 'deploymentEnvironment "prod"' in rendered
    assert 'deploymentNode "cluster-1" "Kubernetes cluster: cluster-1" "Kubernetes Cluster"' in rendered
    assert (
        'deploymentNode "Namespace: payments" "Kubernetes namespace: payments; project: Payments" '
        '"Kubernetes Namespace"'
    ) in rendered
    assert 'deploymentNode "Deployment: Pay" "Kubernetes workload: api; system: Pay" "Kubernetes Pod"' in rendered
    assert rendered.count('deploymentNode "Deployment: Pay"') == 1
    assert "containerInstance ctr_pay_api_app" in rendered
    assert "containerInstance ctr_pay_api_hydra" in rendered
    assert '"workload" "api"' in rendered
    assert '"system" "Pay"' in rendered
    assert "instances 2" in rendered
    assert '"service_ports" "8080/TCP"' in rendered
    assert '"services" "api-svc"' in rendered
    assert '"scaling_enabled" "true"' in rendered
    assert '"scaling_type" "hpa"' in rendered
    assert '"min_replicas" "2"' in rendered
    assert '"max_replicas" "20"' in rendered
    assert '"scale_formula" "cpu averageUtilization 75"' in rendered
    assert '"container_images" "example/app:1"' in rendered
    assert '"container_ports" "8080/TCP"' in rendered
    assert '"container_source" "app"' in rendered


def test_structurizr_deployment_uses_fallback_titles_and_skips_unknown_containers():
    rendered = render_structurizr_deployment(
        {
            "projects": [{"id": "prj.worker", "name": "worker"}],
            "systems": [{"id": "sys.worker", "title": "Worker", "project_id": "prj.worker"}],
            "containers": [{"id": "ctr.worker.app", "system_id": "sys.worker", "name": "worker-app"}],
        },
        {
            "clusters": [
                {
                    "id": "cluster-a",
                    "namespaces": [
                        {
                            "id": "ns-worker",
                            "instances": [
                                {
                                    "id": "pod-worker",
                                    "name": "worker",
                                    "container_id": "ctr.worker.app",
                                    "replicas": "3",
                                },
                                {
                                    "id": "pod-missing",
                                    "name": "missing",
                                    "container_id": "ctr.missing",
                                },
                            ],
                        }
                    ],
                }
            ],
        },
    )

    assert 'deploymentEnvironment "env"' in rendered
    assert 'deploymentNode "cluster-a" "Kubernetes cluster: cluster-a" "Kubernetes Cluster"' in rendered
    assert 'deploymentNode "Namespace: ns-worker" "Kubernetes namespace: ns-worker" "Kubernetes Namespace"' in rendered
    assert (
        'deploymentNode "Deployment: Worker" "Kubernetes workload: worker; system: Worker" "Kubernetes Pod"' in rendered
    )
    assert "instances 3" in rendered
    assert "containerInstance ctr_worker_app" in rendered
    assert '"container" "worker-app"' in rendered
    assert "ctr_missing" not in rendered
