from kmap.command.inspect.storage import (
    collect_pvc_storage_metadata,
    pvc_items_by_name,
    pvc_storage_metadata,
    storage_provider_from_text,
    volume_storage_type,
    workload_storage_context,
    workload_volumes,
)


def test_workload_storage_context_collects_pvc_and_storage_provider_metadata():
    workload = {
        "spec": {
            "template": {
                "spec": {
                    "volumes": [
                        {"name": "data", "persistentVolumeClaim": {"claimName": "api-data"}},
                        {"name": "cfg", "configMap": {"name": "api-config"}},
                        {"name": "secret", "secret": {"secretName": "api-secret"}},
                        {"name": "cache", "emptyDir": {}},
                        {"name": "logs", "csi": {"driver": "rook-ceph.rbd.csi.ceph.com"}},
                    ]
                }
            }
        }
    }
    pvc_items = [
        {
            "metadata": {"name": "api-data"},
            "spec": {
                "storageClassName": "rook-ceph-block",
                "resources": {"requests": {"storage": "20Gi"}},
                "accessModes": ["ReadWriteOnce"],
                "volumeName": "pvc-123",
            },
        }
    ]

    assert workload_storage_context(workload, pvc_items) == {
        "volume_types": ["persistentVolumeClaim", "configMap", "secret", "emptyDir", "csi"],
        "persistent_volume_claims": [
            {
                "name": "api-data",
                "storage_class": "rook-ceph-block",
                "size": "20Gi",
                "access_modes": ["ReadWriteOnce"],
                "volume_name": "pvc-123",
            }
        ],
        "storage_classes": ["rook-ceph-block"],
        "storage_providers": ["ceph"],
        "configmap_volumes": ["api-config"],
        "secret_volumes": ["api-secret"],
    }


def test_storage_helpers_handle_unknown_or_partial_values():
    assert volume_storage_type({"name": "plain"}) == ""
    assert pvc_storage_metadata("claim", {}) == {"name": "claim"}
    assert storage_provider_from_text("fast-rbd") == "ceph"
    assert storage_provider_from_text("standard") == ""


def test_workload_volumes_and_pvc_index_helpers_clean_names():
    workload = {
        "spec": {
            "template": {
                "spec": {
                    "volumes": [
                        {"name": "data", "persistentVolumeClaim": {"claimName": "api-data"}},
                    ]
                }
            }
        }
    }
    pvc = {"metadata": {"name": " api-data "}}

    assert workload_volumes(workload) == [{"name": "data", "persistentVolumeClaim": {"claimName": "api-data"}}]
    assert pvc_items_by_name([pvc]) == {"api-data": pvc}
    assert workload_volumes({}) == []
    assert pvc_items_by_name([]) == {}


def test_collect_pvc_storage_metadata_appends_claim_and_provider_once():
    context = {
        "persistent_volume_claims": [],
        "storage_classes": [],
        "storage_providers": [],
    }
    pvc = {"spec": {"storageClassName": "rook-ceph-block"}}

    collect_pvc_storage_metadata(
        context,
        {"persistentVolumeClaim": {"claimName": "api-data"}},
        {"api-data": pvc},
    )
    collect_pvc_storage_metadata(
        context,
        {"persistentVolumeClaim": {"claimName": "api-logs"}},
        {"api-logs": pvc},
    )

    assert context == {
        "persistent_volume_claims": [
            {"name": "api-data", "storage_class": "rook-ceph-block"},
            {"name": "api-logs", "storage_class": "rook-ceph-block"},
        ],
        "storage_classes": ["rook-ceph-block"],
        "storage_providers": ["ceph"],
    }
