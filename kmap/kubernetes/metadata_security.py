"""Kubernetes container and pod security metadata."""

from typing import Any, Dict

from ..config import clean_metadata_string
from .metadata_values import (
    metadata_bool_fields,
    metadata_bool_or_scalar_fields,
    metadata_list,
    metadata_scalar,
    pod_spec,
)

CONTAINER_SECURITY_BOOL_FIELDS = (
    ("privileged", "security_privileged"),
    ("allowPrivilegeEscalation", "security_allow_privilege_escalation"),
    ("readOnlyRootFilesystem", "security_read_only_root_filesystem"),
    ("runAsNonRoot", "security_run_as_non_root"),
)

CONTAINER_CAPABILITY_FIELDS = (
    ("add", "security_capabilities_add"),
    ("drop", "security_capabilities_drop"),
)

POD_SECURITY_BOOL_FIELDS = (
    ("automountServiceAccountToken", "automount_service_account_token"),
    ("hostNetwork", "host_network"),
    ("hostPID", "host_pid"),
    ("hostIPC", "host_ipc"),
)

POD_SECURITY_CONTEXT_FIELDS = (
    ("runAsNonRoot", "pod_run_as_non_root"),
    ("runAsUser", "pod_run_as_user"),
    ("fsGroup", "pod_fs_group"),
)


def container_security_inventory(container: Dict[str, Any]) -> Dict[str, str]:
    security_context = (container or {}).get("securityContext") or {}
    out: Dict[str, str] = {}
    out.update(metadata_bool_fields(security_context, CONTAINER_SECURITY_BOOL_FIELDS))
    run_as_user = metadata_scalar(security_context.get("runAsUser"))
    if run_as_user:
        out["security_run_as_user"] = run_as_user
    out.update(container_capabilities_inventory(security_context.get("capabilities") or {}))
    return out


def workload_security_context(workload: Dict[str, Any]) -> Dict[str, str]:
    spec = pod_spec(workload)
    security_context = spec.get("securityContext") or {}
    out: Dict[str, str] = {}
    service_account = clean_metadata_string(spec.get("serviceAccountName") or spec.get("serviceAccount")) or "default"
    out["service_account"] = service_account
    out.update(metadata_bool_fields(spec, POD_SECURITY_BOOL_FIELDS))
    out.update(metadata_bool_or_scalar_fields(security_context, POD_SECURITY_CONTEXT_FIELDS))
    seccomp_type = metadata_scalar((security_context.get("seccompProfile") or {}).get("type"))
    if seccomp_type:
        out["pod_seccomp_profile"] = seccomp_type
    return out


def container_capabilities_inventory(capabilities: Dict[str, Any]) -> Dict[str, str]:
    out = {}
    for source_key, target_key in CONTAINER_CAPABILITY_FIELDS:
        values = metadata_list(capabilities.get(source_key))
        if values:
            out[target_key] = ", ".join(values)
    return out


__all__ = [
    "CONTAINER_CAPABILITY_FIELDS",
    "CONTAINER_SECURITY_BOOL_FIELDS",
    "POD_SECURITY_BOOL_FIELDS",
    "POD_SECURITY_CONTEXT_FIELDS",
    "container_capabilities_inventory",
    "container_security_inventory",
    "workload_security_context",
]
