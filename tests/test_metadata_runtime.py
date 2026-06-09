from kmap.metadata_runtime import (
    container_runtime_metadata_pairs,
    deployment_runtime_metadata_by_container_id,
    runtime_metadata_items,
    runtime_metadata_pairs,
    short_join_metadata,
    update_container_runtime_metadata,
    workload_instance_runtime_metadata,
    workload_runtime_metadata_items,
)
from kmap.render.structurizr import structurizr_properties_lines


def test_runtime_metadata_items_are_stable_and_deduplicated():
    container_entry = {
        "discovery": {
            "clusters": ["cluster-a"],
            "namespaces": ["ns-a"],
            "workloads": ["api"],
        }
    }
    svc = {
        "kind": "Deployment",
        "entrypoints": [{"port": 8080, "protocol": "TCP"}],
        "services": ["api-svc", "api-svc"],
        "ingresses": ["api-ing"],
        "runtime": {"replicas_ready": 2},
        "autoscaling": {
            "scaling_enabled": "true",
            "scaling_type": "keda",
            "min_replicas": "2",
            "max_replicas": "20",
            "scale_formula": "ceil(RPS / 150)",
        },
        "storage": {
            "volume_types": ["persistentVolumeClaim"],
            "persistent_volume_claims": [{"name": "api-data"}],
            "storage_classes": ["rook-ceph-block"],
            "storage_providers": ["ceph"],
        },
        "observability": {
            "prometheus_scrapes": ["true"],
            "prometheus_paths": ["/metrics"],
            "prometheus_ports": ["9090"],
            "prometheus_schemes": ["http"],
            "prometheus_sources": ["pod_template"],
            "otel_service_names": ["api"],
            "otel_exporter_otlp_endpoints": ["http://otel-collector:4317"],
            "otel_env_vars": ["OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_SERVICE_NAME"],
        },
        "security": {
            "service_account": "api-sa",
            "automount_service_account_token": "false",
            "host_network": "true",
            "pod_run_as_non_root": "true",
            "pod_seccomp_profile": "RuntimeDefault",
        },
    }
    update_container_runtime_metadata(
        container_entry,
        svc,
        {
            "name": "api",
            "kind": "app",
            "image": "example/api:1",
            "ports": [8080],
            "request_cpu": "100m",
            "request_memory": "128Mi",
            "limit_cpu": "500m",
            "limit_memory": "512Mi",
            "readiness_probe": "http http /ready:8080",
            "liveness_probe": "tcp http",
            "startup_probe": "exec",
            "security_allow_privilege_escalation": "false",
            "security_read_only_root_filesystem": "true",
            "security_run_as_non_root": "true",
            "security_run_as_user": "10001",
            "security_capabilities_drop": "ALL",
        },
    )

    assert ("container_images", "example/api:1") not in runtime_metadata_items(container_entry)
    assert ("container_ports", "8080") not in runtime_metadata_items(container_entry)
    assert ("clusters", "cluster-a") not in runtime_metadata_items(container_entry)
    assert ("service_ports", "8080/TCP") not in runtime_metadata_items(container_entry)
    assert ("container_images", "example/api:1") in container_runtime_metadata_pairs(container_entry)
    assert ("container_ports", "8080") in container_runtime_metadata_pairs(container_entry)
    assert ("container_cpu_requests", "100m") in container_runtime_metadata_pairs(container_entry)
    assert ("container_memory_requests", "128Mi") in container_runtime_metadata_pairs(container_entry)
    assert ("container_cpu_limits", "500m") in container_runtime_metadata_pairs(container_entry)
    assert ("container_memory_limits", "512Mi") in container_runtime_metadata_pairs(container_entry)
    assert ("container_readiness_probes", "http http /ready:8080") in container_runtime_metadata_pairs(container_entry)
    assert ("container_liveness_probes", "tcp http") in container_runtime_metadata_pairs(container_entry)
    assert ("container_startup_probes", "exec") in container_runtime_metadata_pairs(container_entry)
    assert ("container_allow_privilege_escalation", "false") in container_runtime_metadata_pairs(container_entry)
    assert ("container_read_only_root_filesystem", "true") in container_runtime_metadata_pairs(container_entry)
    assert ("container_run_as_non_root", "true") in container_runtime_metadata_pairs(container_entry)
    assert ("container_run_as_user", "10001") in container_runtime_metadata_pairs(container_entry)
    assert ("container_capabilities_drop", "ALL") in container_runtime_metadata_pairs(container_entry)

    instance_runtime = workload_instance_runtime_metadata(svc)
    assert ("service_ports", "8080/TCP") in runtime_metadata_pairs(instance_runtime)
    assert ("services", "api-svc") in runtime_metadata_pairs(instance_runtime)
    assert ("scaling_enabled", "true") in runtime_metadata_pairs(instance_runtime)
    assert ("scaling_type", "keda") in runtime_metadata_pairs(instance_runtime)
    assert ("min_replicas", "2") in runtime_metadata_pairs(instance_runtime)
    assert ("max_replicas", "20") in runtime_metadata_pairs(instance_runtime)
    assert ("scale_formula", "ceil(RPS / 150)") in runtime_metadata_pairs(instance_runtime)
    assert ("storage_types", "persistentVolumeClaim") in runtime_metadata_pairs(instance_runtime)
    assert ("persistent_volume_claims", "api-data") in runtime_metadata_pairs(instance_runtime)
    assert ("storage_classes", "rook-ceph-block") in runtime_metadata_pairs(instance_runtime)
    assert ("storage_providers", "ceph") in runtime_metadata_pairs(instance_runtime)
    assert ("prometheus_scrapes", "true") in runtime_metadata_pairs(instance_runtime)
    assert ("prometheus_paths", "/metrics") in runtime_metadata_pairs(instance_runtime)
    assert ("prometheus_ports", "9090") in runtime_metadata_pairs(instance_runtime)
    assert ("prometheus_schemes", "http") in runtime_metadata_pairs(instance_runtime)
    assert ("prometheus_sources", "pod_template") in runtime_metadata_pairs(instance_runtime)
    assert ("otel_service_names", "api") in runtime_metadata_pairs(instance_runtime)
    assert ("otel_exporter_otlp_endpoints", "http://otel-collector:4317") in runtime_metadata_pairs(instance_runtime)
    assert ("otel_env_vars", "OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_SERVICE_NAME") in runtime_metadata_pairs(
        instance_runtime
    )
    assert ("service_account", "api-sa") in runtime_metadata_pairs(instance_runtime)
    assert ("automount_service_account_token", "false") in runtime_metadata_pairs(instance_runtime)
    assert ("host_network", "true") in runtime_metadata_pairs(instance_runtime)
    assert ("pod_run_as_non_root", "true") in runtime_metadata_pairs(instance_runtime)
    assert ("pod_seccomp_profile", "RuntimeDefault") in runtime_metadata_pairs(instance_runtime)


def test_workload_scheduling_metadata_pairs_are_included():
    instance_runtime = workload_instance_runtime_metadata(
        {
            "kind": "Deployment",
            "scheduling": {
                "priority_class": "high-priority",
                "scheduler_name": "custom-scheduler",
                "runtime_class": "gvisor",
                "node_selector": "disktype=ssd",
                "tolerations": "dedicated Equal payments (NoSchedule)",
                "affinity": "node",
                "topology_spread": "topology.kubernetes.io/zone (ScheduleAnyway)",
            },
        }
    )

    assert ("priority_class", "high-priority") in runtime_metadata_pairs(instance_runtime)
    assert ("scheduler_name", "custom-scheduler") in runtime_metadata_pairs(instance_runtime)
    assert ("runtime_class", "gvisor") in runtime_metadata_pairs(instance_runtime)
    assert ("node_selector", "disktype=ssd") in runtime_metadata_pairs(instance_runtime)
    assert ("tolerations", "dedicated Equal payments (NoSchedule)") in runtime_metadata_pairs(instance_runtime)
    assert ("affinity", "node") in runtime_metadata_pairs(instance_runtime)
    assert ("topology_spread", "topology.kubernetes.io/zone (ScheduleAnyway)") in runtime_metadata_pairs(
        instance_runtime
    )


def test_runtime_metadata_items_include_database_summary():
    items = runtime_metadata_items(
        {
            "metadata": {
                "database": {
                    "engine": "mysql",
                    "names": ["app", "APP", "audit"],
                }
            }
        }
    )

    assert ("database_engine", "mysql") in items
    assert ("databases", "app, audit") in items


def test_runtime_metadata_items_keeps_database_summary_detailed():
    items = runtime_metadata_items(
        {
            "metadata": {
                "database": {
                    "engine": "mysql",
                    "names": ["external_deposit_prod", "payment_gateway_prod", "payment_api_prod", "ticket_prod"],
                }
            }
        }
    )

    assert ("databases", "external_deposit_prod, payment_gateway_prod, payment_api_prod, ticket_prod") in items


def test_workload_runtime_metadata_and_structurizr_properties_escape_values():
    svc = {
        "cluster": "cluster-a",
        "namespace": "ns-a",
        "service_name": "api",
        "kind": "Deployment",
        "containers": [
            {
                "image": 'example/"api":1',
                "ports": [8080],
                "request_cpu": "100m",
                "request_memory": "128Mi",
                "limit_cpu": "500m",
                "limit_memory": "512Mi",
                "readiness_probe": "http http /ready:8080",
                "liveness_probe": "tcp http",
                "security_allow_privilege_escalation": "false",
                "security_read_only_root_filesystem": "true",
            }
        ],
        "entrypoints": [{"port": 80, "protocol": "TCP"}],
        "storage": {
            "volume_types": ["persistentVolumeClaim"],
            "persistent_volume_claims": [{"name": "api-data"}],
            "storage_classes": ["rook-ceph-block"],
            "storage_providers": ["ceph"],
        },
        "observability": {
            "prometheus_scrapes": ["true"],
            "otel_env_vars": ["OTEL_SERVICE_NAME"],
        },
        "security": {
            "service_account": "api-sa",
            "pod_seccomp_profile": "RuntimeDefault",
        },
        "scheduling": {
            "priority_class": "high-priority",
            "node_selector": "disktype=ssd",
        },
    }

    items = workload_runtime_metadata_items(svc)
    lines = structurizr_properties_lines(items, indent="    ")

    assert ("workload", "api") in items
    assert ("container_cpu_requests", "100m") in items
    assert ("container_memory_limits", "512Mi") in items
    assert ("container_readiness_probes", "http http /ready:8080") in items
    assert ("container_liveness_probes", "tcp http") in items
    assert ("container_allow_privilege_escalation", "false") in items
    assert ("container_read_only_root_filesystem", "true") in items
    assert ("service_account", "api-sa") in items
    assert ("pod_seccomp_profile", "RuntimeDefault") in items
    assert ("priority_class", "high-priority") in items
    assert ("node_selector", "disktype=ssd") in items
    assert ("storage_providers", "ceph") in items
    assert ("prometheus_scrapes", "true") in items
    assert ("otel_env_vars", "OTEL_SERVICE_NAME") in items
    assert '      "container_images" "example/\\"api\\":1"' in lines


def test_short_join_metadata_deduplicates_and_applies_limit():
    assert short_join_metadata(["a", "A", "", None, "b", "c"], limit=2) == "a, b, +1 more"


def test_deployment_runtime_metadata_by_container_id_deduplicates_and_flattens_instances():
    metadata_by_container = deployment_runtime_metadata_by_container_id(
        {
            "deployments": [
                {
                    "clusters": [
                        {
                            "namespaces": [
                                {
                                    "instances": [
                                        {
                                            "container_id": "ctr.pay.api",
                                            "runtime": {
                                                "services": [["api-svc", ""], "api-svc"],
                                                "storage_types": ["configMap"],
                                            },
                                        },
                                        {
                                            "container_id": "ctr.pay.api",
                                            "runtime": {
                                                "services": ["api-svc", "api-metrics"],
                                                "storage_types": ["configMap", "secret"],
                                            },
                                        },
                                        {"container_id": "", "runtime": {"services": ["ignored"]}},
                                        {"container_id": "ctr.pay.worker", "runtime": {}},
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
        }
    )

    assert metadata_by_container == {
        "ctr.pay.api": [
            ("services", "api-svc, api-metrics"),
            ("storage_types", "configMap, secret"),
        ]
    }
