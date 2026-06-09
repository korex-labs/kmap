from kmap.command.inspect.autoscaling import (
    autoscaling_by_workload,
    autoscaling_metadata_from_hpa,
    autoscaling_metadata_from_keda_scaled_object,
    autoscaling_text,
    merge_autoscaling_metadata,
)


def test_autoscaling_metadata_from_hpa_preserves_replicas_and_metrics():
    metadata = autoscaling_metadata_from_hpa(
        {
            "spec": {
                "minReplicas": 2,
                "maxReplicas": 20,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {"type": "Utilization", "averageUtilization": 75},
                        },
                    }
                ],
            }
        }
    )

    assert metadata == {
        "scaling_enabled": "true",
        "scaling_type": "hpa",
        "min_replicas": "2",
        "max_replicas": "20",
        "scale_formula": "cpu averageUtilization 75",
    }


def test_autoscaling_metadata_from_keda_scaled_object_prefers_scaling_modifier_formula():
    metadata = autoscaling_metadata_from_keda_scaled_object(
        {
            "spec": {
                "minReplicaCount": 2,
                "maxReplicaCount": 20,
                "advanced": {"scalingModifiers": {"formula": "ceil(RPS / 150)"}},
                "triggers": [{"type": "prometheus", "metadata": {"metricName": "RPS", "threshold": "150"}}],
            }
        }
    )

    assert metadata == {
        "scaling_enabled": "true",
        "scaling_type": "keda",
        "min_replicas": "2",
        "max_replicas": "20",
        "scale_formula": "ceil(RPS / 150)",
    }


def test_autoscaling_by_workload_maps_hpa_and_keda_by_scale_target_ref():
    by_workload = autoscaling_by_workload(
        {
            "items": [
                {
                    "spec": {
                        "scaleTargetRef": {"kind": "Deployment", "name": "api"},
                        "minReplicas": 1,
                        "maxReplicas": 5,
                    }
                }
            ]
        },
        {
            "items": [
                {
                    "spec": {
                        "scaleTargetRef": {"name": "worker"},
                        "minReplicaCount": 2,
                        "maxReplicaCount": 10,
                        "triggers": [{"type": "prometheus", "metadata": {"metricName": "queue", "threshold": "42"}}],
                    }
                }
            ]
        },
    )

    assert by_workload["Deployment", "api"]["scaling_type"] == "hpa"
    assert by_workload["Deployment", "worker"] == {
        "scaling_enabled": "true",
        "scaling_type": "keda",
        "min_replicas": "2",
        "max_replicas": "10",
        "scale_formula": "queue >= 42",
    }


def test_autoscaling_metadata_from_hpa_formats_supported_metric_types():
    metadata = autoscaling_metadata_from_hpa(
        {
            "spec": {
                "metrics": [
                    {
                        "type": "Pods",
                        "pods": {"metric": {"name": "rps"}, "target": {"averageValue": "150"}},
                    },
                    {
                        "type": "Object",
                        "object": {"metric": {"name": "queue_depth"}, "target": {"value": "42"}},
                    },
                    {
                        "type": "External",
                        "external": {"metric": {"name": "lag"}, "target": {"averageValue": "10"}},
                    },
                    {
                        "type": "ContainerResource",
                        "containerResource": {
                            "container": "api",
                            "name": "memory",
                            "target": {"averageUtilization": 80},
                        },
                    },
                    {"type": "CustomMetric"},
                ]
            }
        }
    )

    assert metadata["scale_formula"] == (
        "rps averageValue 150; queue_depth value 42; lag averageValue 10; "
        "api.memory averageUtilization 80; CustomMetric"
    )


def test_autoscaling_metadata_from_keda_scaled_object_formats_trigger_fallbacks():
    metadata = autoscaling_metadata_from_keda_scaled_object(
        {
            "spec": {
                "triggers": [
                    {
                        "type": "prometheus",
                        "metadata": {"metricNameFromEnv": "QUEUE_METRIC", "targetValue": "25"},
                    },
                    {
                        "type": "redis",
                        "metadata": {"activationThreshold": "5"},
                    },
                    {
                        "type": "kafka",
                        "metadata": {"metricName": "consumer_lag"},
                    },
                    {"metadata": {}},
                ]
            }
        }
    )

    assert metadata == {
        "scaling_enabled": "true",
        "scaling_type": "keda",
        "scale_formula": "QUEUE_METRIC >= 25; redis >= 5; kafka:consumer_lag; trigger",
    }


def test_autoscaling_by_workload_merges_hpa_and_keda_and_skips_missing_targets():
    by_workload = autoscaling_by_workload(
        {
            "items": [
                {
                    "spec": {
                        "scaleTargetRef": {"kind": "Deployment", "name": "api"},
                        "minReplicas": 1,
                        "maxReplicas": 5,
                        "metrics": [
                            {
                                "type": "Resource",
                                "resource": {"name": "cpu", "target": {"averageUtilization": 70}},
                            }
                        ],
                    }
                },
                {"spec": {"scaleTargetRef": {"kind": "Deployment"}}},
            ]
        },
        {
            "items": [
                {
                    "spec": {
                        "scaleTargetRef": {"kind": "Deployment", "name": "api"},
                        "minReplicaCount": 2,
                        "maxReplicaCount": 10,
                        "triggers": [{"type": "prometheus", "metadata": {"metricName": "rps", "threshold": "150"}}],
                    }
                },
                {"spec": {"scaleTargetRef": {}}},
            ]
        },
    )

    assert list(by_workload) == [("Deployment", "api")]
    assert by_workload["Deployment", "api"] == {
        "scaling_enabled": "true",
        "scaling_type": "hpa,keda",
        "min_replicas": "2",
        "max_replicas": "10",
        "scale_formula": "cpu averageUtilization 70; rps >= 150",
    }


def test_merge_autoscaling_metadata_combines_types_and_prefers_incoming_limits():
    assert merge_autoscaling_metadata(
        {
            "scaling_enabled": "true",
            "scaling_type": "hpa",
            "min_replicas": "1",
            "max_replicas": "5",
            "scale_formula": "cpu averageUtilization 70",
        },
        {
            "scaling_enabled": "true",
            "scaling_type": "keda",
            "min_replicas": "2",
            "max_replicas": "10",
            "scale_formula": "rps >= 150",
        },
    ) == {
        "scaling_enabled": "true",
        "scaling_type": "hpa,keda",
        "min_replicas": "2",
        "max_replicas": "10",
        "scale_formula": "cpu averageUtilization 70; rps >= 150",
    }


def test_autoscaling_text_renders_known_keys_in_stable_order():
    assert (
        autoscaling_text(
            {
                "scale_formula": "rps >= 150",
                "scaling_type": "keda",
                "ignored": "value",
                "scaling_enabled": "true",
                "max_replicas": 10,
            }
        )
        == "scaling_enabled=true, scaling_type=keda, max_replicas=10, scale_formula=rps >= 150"
    )
    assert autoscaling_text({}) == ""
