from kmap.metadata_runtime import (
    CONTAINER_PROBE_METADATA_ITEMS,
    CONTAINER_RESOURCE_METADATA_ITEMS,
    CONTAINER_SECURITY_METADATA_ITEMS,
    RUNTIME_METADATA_ITEMS,
)
from kmap.render.likec4.metadata import (
    LIKEC4_METADATA_RESERVED_KEYS,
    grouped_container_metadata_items,
    grouped_runtime_metadata_items,
)


def test_grouped_container_metadata_items_collapses_runtime_details():
    items = grouped_container_metadata_items(
        [
            ("database_engine", "mysql"),
            ("databases", "app, audit"),
            ("container_images", "example/api:1"),
            ("services", "api-svc"),
            ("ingresses", "api.example.com"),
            ("service_ports", "80/TCP"),
            ("container_ports", "8080/TCP"),
            ("prometheus_scrapes", "true"),
            ("prometheus_paths", "/metrics"),
            ("prometheus_ports", "9090"),
            ("otel_service_names", "api"),
            ("container_readiness_probes", "http /ready:8080"),
            ("container_liveness_probes", "tcp 9000"),
            ("container_startup_probes", "exec"),
            ("container_cpu_requests", "100m"),
            ("container_cpu_limits", "500m"),
            ("container_memory_requests", "128Mi"),
            ("container_memory_limits", "512Mi"),
            ("workload_kinds", "Deployment"),
            ("replicas_desired", "2"),
            ("replicas_ready", "1"),
            ("scaling_enabled", "true"),
            ("scaling_type", "hpa"),
            ("min_replicas", "2"),
            ("max_replicas", "5"),
            ("scale_formula", "cpu averageUtilization 80"),
            ("priority_class", "high"),
            ("node_selector", "disk=ssd"),
            ("service_account", "api-sa"),
            ("pod_seccomp_profile", "RuntimeDefault"),
            ("container_allow_privilege_escalation", "false"),
            ("container_read_only_root_filesystem", "true"),
            ("container_capabilities_drop", "ALL"),
            ("storage_types", "persistentVolumeClaim"),
            ("persistent_volume_claims", "api-data"),
            ("storage_classes", "rook-ceph-block"),
            ("storage_providers", "ceph"),
            ("container_source", "api-prod"),
        ]
    )

    assert items == [
        ("ops_database", "mysql: app, audit"),
        ("container_image", "example/api:1"),
        (
            "ops_network",
            "services: api-svc; ingresses: api.example.com; service ports: 80/TCP; container ports: 8080/TCP",
        ),
        ("ops_observability", "prometheus: true; paths: /metrics; ports: 9090; otel services: api"),
        ("ops_probes", "readiness: http /ready:8080; liveness: tcp 9000; startup: exec"),
        ("ops_resources", "cpu 100m/500m; memory 128Mi/512Mi"),
        ("ops_runtime", "workloads: Deployment; replicas desired: 2; ready: 1"),
        ("ops_scaling", "enabled: true; type: hpa; min: 2; max: 5; formula: cpu averageUtilization 80"),
        ("ops_scheduling", "priority: high; node selector: disk=ssd"),
        (
            "ops_security",
            "service account: api-sa; pod seccomp: RuntimeDefault; "
            "allow privilege escalation: false; read-only root fs: true; cap drop: ALL",
        ),
        ("container_source", "api-prod"),
        ("ops_storage", "types: persistentVolumeClaim; pvcs: api-data; classes: rook-ceph-block; providers: ceph"),
    ]


def test_grouped_container_metadata_items_skips_empty_groups_and_deduplicates():
    items = grouped_container_metadata_items(
        [
            ("container_images", "example/api:1"),
            ("container_images", "example/api:1"),
            ("container_ports", ""),
            ("services", "api-svc"),
        ]
    )

    assert items == [
        ("container_image", "example/api:1"),
        ("ops_network", "services: api-svc"),
    ]


def test_grouped_container_metadata_items_displays_every_collected_runtime_key():
    collected_display_keys = {
        "database_engine",
        "databases",
        "container_images",
        "container_ports",
        "container_source",
        *(property_key for _, property_key in RUNTIME_METADATA_ITEMS),
        *(property_key for property_key, _ in CONTAINER_RESOURCE_METADATA_ITEMS),
        *(property_key for property_key, _ in CONTAINER_PROBE_METADATA_ITEMS),
        *(property_key for property_key, _ in CONTAINER_SECURITY_METADATA_ITEMS),
    }
    items = [(key, f"value-for-{key}") for key in sorted(collected_display_keys)]

    rendered_values = " | ".join(value for _, value in grouped_container_metadata_items(items))

    for key in collected_display_keys:
        assert f"value-for-{key}" in rendered_values


def test_grouped_container_metadata_items_avoids_likec4_reserved_keys():
    items = [
        ("database_engine", "mysql"),
        ("container_images", "example/api:1"),
        ("services", "api-svc"),
        ("prometheus_scrapes", "true"),
        ("container_readiness_probes", "tcp 9000"),
        ("container_cpu_requests", "100m"),
        ("workload_kinds", "Deployment"),
        ("scaling_enabled", "true"),
        ("priority_class", "high"),
        ("service_account", "api-sa"),
        ("container_source", "api"),
        ("storage_types", "configMap"),
    ]
    keys = [key for key, _ in grouped_container_metadata_items(items)]

    assert not LIKEC4_METADATA_RESERVED_KEYS.intersection(keys)


def test_grouped_runtime_metadata_items_preserves_deployment_context_and_groups_runtime_details():
    items = grouped_runtime_metadata_items(
        [
            ("workload", "api"),
            ("system", "Payments"),
            ("node_kind", "k8s_pod"),
            ("services", "api-svc"),
            ("storage_types", "configMap"),
        ],
        preserve_keys=("workload", "system", "node_kind"),
    )

    assert items == [
        ("workload", "api"),
        ("system", "Payments"),
        ("node_kind", "k8s_pod"),
        ("ops_network", "services: api-svc"),
        ("ops_storage", "types: configMap"),
    ]
