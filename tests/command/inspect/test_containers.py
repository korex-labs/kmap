from kmap.inspection.workloads import (
    extract_literal_env_from_container,
    extract_refs_from_container,
    workload_container_context,
)
from kmap.kubernetes.metadata import (
    affinity_summary,
    container_capabilities_inventory,
    container_probe_inventory,
    container_resource_inventory,
    container_security_inventory,
    grpc_probe_summary,
    http_probe_summary,
    metadata_bool,
    metadata_bool_fields,
    metadata_bool_or_scalar_fields,
    metadata_list,
    metadata_scalar,
    metadata_scalar_fields,
    port_probe_summary,
    probe_summary,
    toleration_summaries,
    topology_spread_summary,
    workload_scheduling_context,
    workload_security_context,
)


def test_container_reference_extractors():
    container = {
        "envFrom": [
            {"configMapRef": {"name": "app-config"}},
            {"secretRef": {"name": "app-secret"}},
        ],
        "env": [
            {"name": "API_URL", "value": "https://api.example.com"},
            {"name": "FROM_CM", "valueFrom": {"configMapKeyRef": {"name": "cm-key"}}},
            {"name": "FROM_SECRET", "valueFrom": {"secretKeyRef": {"name": "secret-key"}}},
        ],
    }

    assert extract_refs_from_container(container) == ({"app-config", "cm-key"}, {"app-secret", "secret-key"})
    assert extract_literal_env_from_container(container) == {"API_URL": "https://api.example.com"}


def test_workload_container_context_collects_inventory_and_references():
    context = workload_container_context(
        {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "name": "app",
                                "image": "example/app:1",
                                "resources": {
                                    "requests": {"cpu": "100m", "memory": "128Mi"},
                                    "limits": {"cpu": "500m", "memory": "512Mi"},
                                },
                                "readinessProbe": {"httpGet": {"path": "/ready", "port": 8080}},
                                "livenessProbe": {"tcpSocket": {"port": "http"}},
                                "startupProbe": {"exec": {"command": ["test", "-f", "/tmp/ready"]}},
                                "securityContext": {
                                    "allowPrivilegeEscalation": False,
                                    "privileged": False,
                                    "readOnlyRootFilesystem": True,
                                    "runAsNonRoot": True,
                                    "runAsUser": 10001,
                                    "capabilities": {"drop": ["ALL"]},
                                },
                                "envFrom": [{"configMapRef": {"name": "app-config"}}],
                            }
                        ],
                        "initContainers": [
                            {
                                "name": "migrate",
                                "image": "example/migrate:1",
                                "env": [
                                    {
                                        "name": "PASSWORD",
                                        "valueFrom": {"secretKeyRef": {"name": "db-secret"}},
                                    }
                                ],
                            }
                        ],
                    }
                }
            }
        }
    )

    assert context["containers"][0]["name"] == "app"
    assert context["containers"][1]["name"] == "migrate"
    assert context["inventory"] == [
        {
            "name": "app",
            "image": "example/app:1",
            "kind": "container",
            "ports": [],
            "request_cpu": "100m",
            "request_memory": "128Mi",
            "limit_cpu": "500m",
            "limit_memory": "512Mi",
            "readiness_probe": "http http /ready:8080",
            "liveness_probe": "tcp http",
            "startup_probe": "exec",
            "security_allow_privilege_escalation": "false",
            "security_privileged": "false",
            "security_read_only_root_filesystem": "true",
            "security_run_as_non_root": "true",
            "security_run_as_user": "10001",
            "security_capabilities_drop": "ALL",
        },
        {"name": "migrate", "image": "example/migrate:1", "kind": "initContainer", "ports": []},
    ]
    assert context["referenced_configmaps"] == {"app-config"}
    assert context["referenced_secrets"] == {"db-secret"}


def test_probe_summary_handles_http_grpc_and_empty_probes():
    assert probe_summary({"httpGet": {"path": "/health", "port": 8080, "scheme": "HTTPS"}}) == "http https /health:8080"
    assert probe_summary({"grpc": {"service": "health", "port": 9090}}) == "grpc health:9090"
    assert probe_summary({}) == ""


def test_probe_summary_helpers_apply_default_http_path_and_empty_port_fallbacks():
    assert http_probe_summary({"scheme": "HTTPS"}) == "http https /"
    assert port_probe_summary("tcp", {}) == "tcp"
    assert grpc_probe_summary({"port": 9090}) == "grpc 9090"
    assert grpc_probe_summary({}) == "grpc"
    assert probe_summary({"exec": {}}) == ""


def test_metadata_list_and_capabilities_inventory_clean_empty_values():
    assert metadata_bool(True) == "true"
    assert metadata_bool("true") == ""
    assert metadata_scalar(None) == ""
    assert metadata_list(["NET_ADMIN", "", None, " SYS_TIME "]) == ["NET_ADMIN", "SYS_TIME"]
    assert metadata_bool_fields({"enabled": False}, (("enabled", "enabled"),)) == {"enabled": "false"}
    assert metadata_scalar_fields({"port": 9090}, (("port", "port"),)) == {"port": "9090"}
    assert metadata_bool_or_scalar_fields({"flag": "disabled"}, (("flag", "flag"),)) == {"flag": "disabled"}
    assert container_capabilities_inventory({"add": ["NET_ADMIN", ""], "drop": [None, "ALL"]}) == {
        "security_capabilities_add": "NET_ADMIN",
        "security_capabilities_drop": "ALL",
    }


def test_container_inventory_helpers_ignore_empty_values():
    assert container_resource_inventory({"resources": {"requests": {"cpu": ""}, "limits": {"memory": None}}}) == {}
    assert container_probe_inventory({"readinessProbe": {"tcpSocket": {}}}) == {}
    assert container_security_inventory({"securityContext": {"capabilities": {"add": []}}}) == {}


def test_workload_security_context_collects_pod_level_posture():
    context = workload_security_context(
        {
            "spec": {
                "template": {
                    "spec": {
                        "serviceAccountName": "api-sa",
                        "automountServiceAccountToken": False,
                        "hostNetwork": True,
                        "hostPID": True,
                        "securityContext": {
                            "runAsNonRoot": True,
                            "runAsUser": 10001,
                            "fsGroup": 2000,
                            "seccompProfile": {"type": "RuntimeDefault"},
                        },
                    }
                }
            }
        }
    )

    assert context == {
        "service_account": "api-sa",
        "automount_service_account_token": "false",
        "host_network": "true",
        "host_pid": "true",
        "pod_run_as_non_root": "true",
        "pod_run_as_user": "10001",
        "pod_fs_group": "2000",
        "pod_seccomp_profile": "RuntimeDefault",
    }


def test_workload_scheduling_context_collects_pod_scheduling_posture():
    context = workload_scheduling_context(
        {
            "spec": {
                "template": {
                    "spec": {
                        "priorityClassName": "high-priority",
                        "schedulerName": "custom-scheduler",
                        "runtimeClassName": "gvisor",
                        "nodeSelector": {"disktype": "ssd", "zone": "eu"},
                        "tolerations": [
                            {"key": "dedicated", "operator": "Equal", "value": "payments", "effect": "NoSchedule"}
                        ],
                        "affinity": {"nodeAffinity": {"requiredDuringSchedulingIgnoredDuringExecution": {}}},
                        "topologySpreadConstraints": [
                            {
                                "topologyKey": "topology.kubernetes.io/zone",
                                "whenUnsatisfiable": "ScheduleAnyway",
                            }
                        ],
                    }
                }
            }
        }
    )

    assert context == {
        "priority_class": "high-priority",
        "scheduler_name": "custom-scheduler",
        "runtime_class": "gvisor",
        "node_selector": "disktype=ssd, zone=eu",
        "tolerations": "dedicated Equal payments (NoSchedule)",
        "affinity": "node",
        "topology_spread": "topology.kubernetes.io/zone (ScheduleAnyway)",
    }


def test_scheduling_helpers_keep_summaries_compact_and_stable():
    assert toleration_summaries([{"operator": "Exists"}, {"key": "role", "effect": "NoExecute"}]) == [
        "* Exists",
        "role Equal (NoExecute)",
    ]
    assert affinity_summary({"podAffinity": {}, "podAntiAffinity": {"preferred": []}}) == "podAnti"
    assert (
        topology_spread_summary(
            [
                {"topologyKey": "zone"},
                {"topologyKey": "zone"},
                {"topologyKey": "rack", "whenUnsatisfiable": "DoNotSchedule"},
            ]
        )
        == "rack (DoNotSchedule), zone"
    )
