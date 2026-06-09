"""Workload storage context extraction."""

from typing import Any, Dict, List

from ...config import clean_metadata_string

STORAGE_VOLUME_KEYS = (
    "persistentVolumeClaim",
    "configMap",
    "secret",
    "emptyDir",
    "hostPath",
    "nfs",
    "csi",
)
CEPH_MARKERS = ("ceph", "rbd", "rook")


def workload_storage_context(workload: Dict[str, Any], pvc_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    volumes = workload_volumes(workload)
    pvc_by_name = pvc_items_by_name(pvc_items)

    context: Dict[str, Any] = {
        "volume_types": [],
        "persistent_volume_claims": [],
        "storage_classes": [],
        "storage_providers": [],
        "configmap_volumes": [],
        "secret_volumes": [],
    }

    for volume in volumes:
        if not isinstance(volume, dict):
            continue
        volume_type = volume_storage_type(volume)
        if volume_type:
            append_unique(context["volume_types"], volume_type)
        collect_volume_storage_metadata(context, volume, pvc_by_name)

    return {key: value for key, value in context.items() if value}


def workload_volumes(workload: Dict[str, Any]) -> List[Dict[str, Any]]:
    tpl_spec = (((workload.get("spec") or {}).get("template") or {}).get("spec")) or {}
    return tpl_spec.get("volumes") or []


def pvc_items_by_name(pvc_items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {clean_metadata_string((pvc.get("metadata") or {}).get("name")): pvc for pvc in pvc_items or []}


def volume_storage_type(volume: Dict[str, Any]) -> str:
    for key in STORAGE_VOLUME_KEYS:
        if isinstance(volume.get(key), dict):
            return key
    return ""


def collect_volume_storage_metadata(
    context: Dict[str, Any],
    volume: Dict[str, Any],
    pvc_by_name: Dict[str, Dict[str, Any]],
) -> None:
    collect_pvc_storage_metadata(context, volume, pvc_by_name)

    configmap_name = clean_metadata_string((volume.get("configMap") or {}).get("name"))
    append_unique(context["configmap_volumes"], configmap_name)

    secret_name = clean_metadata_string((volume.get("secret") or {}).get("secretName"))
    append_unique(context["secret_volumes"], secret_name)

    csi = volume.get("csi") or {}
    append_unique(context["storage_providers"], storage_provider_from_text(csi.get("driver")))


def collect_pvc_storage_metadata(
    context: Dict[str, Any],
    volume: Dict[str, Any],
    pvc_by_name: Dict[str, Dict[str, Any]],
) -> None:
    pvc_ref = volume.get("persistentVolumeClaim") or {}
    claim_name = clean_metadata_string(pvc_ref.get("claimName"))
    if claim_name:
        pvc_metadata = pvc_storage_metadata(claim_name, pvc_by_name.get(claim_name) or {})
        context["persistent_volume_claims"].append(pvc_metadata)
        append_unique(context["storage_classes"], pvc_metadata.get("storage_class"))
        append_unique(context["storage_providers"], storage_provider_from_text(pvc_metadata.get("storage_class")))


def pvc_storage_metadata(claim_name: str, pvc: Dict[str, Any]) -> Dict[str, Any]:
    spec = pvc.get("spec") or {}
    requests = ((spec.get("resources") or {}).get("requests")) or {}
    return {
        key: value
        for key, value in {
            "name": claim_name,
            "storage_class": clean_metadata_string(spec.get("storageClassName")),
            "size": clean_metadata_string(requests.get("storage")),
            "access_modes": [clean_metadata_string(value) for value in spec.get("accessModes") or [] if value],
            "volume_name": clean_metadata_string(spec.get("volumeName")),
        }.items()
        if value
    }


def storage_provider_from_text(value: Any) -> str:
    text = clean_metadata_string(value).lower()
    if any(marker in text for marker in CEPH_MARKERS):
        return "ceph"
    return ""


def append_unique(items: List[Any], value: Any) -> None:
    if not value:
        return
    if value not in items:
        items.append(value)


__all__ = [
    "collect_pvc_storage_metadata",
    "pvc_items_by_name",
    "pvc_storage_metadata",
    "storage_provider_from_text",
    "volume_storage_type",
    "workload_storage_context",
    "workload_volumes",
]
