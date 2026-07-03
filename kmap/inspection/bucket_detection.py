"""Object-storage bucket candidate detection from key/value pairs."""

import re
from typing import Any, Dict, List

from ..hostish import parse_hostish

BUCKET_KEY_RE = re.compile(r"(^|_)(BUCKET|BUCKET_NAME|S3_BUCKET|CEPH_BUCKET|MINIO_BUCKET)($|_)", re.IGNORECASE)
OBJECT_STORAGE_KEY_RE = re.compile(r"(S3|CEPH|MINIO|OBJECT_STORAGE|BUCKET|OS_AUTH_URL|OPENSTACK|SWIFT)", re.IGNORECASE)
ENDPOINT_KEY_RE = re.compile(r"(ENDPOINT|HOST|URL|URI|BASE)", re.IGNORECASE)
SENSITIVE_BUCKET_KEY_RE = re.compile(
    r"(ACCESS_KEY|SECRET_KEY|SECRET|PASSWORD|PASSWD|TOKEN|PRIVATE_KEY|CREDENTIAL|SESSION|COOKIE)",
    re.IGNORECASE,
)
VIRTUAL_HOSTED_S3_RE = re.compile(r"^(?P<bucket>[a-z0-9][a-z0-9.-]*)[.]s3[.-]", re.IGNORECASE)
KUBERNETES_SERVICE_PORT_KEY_RE = re.compile(r"_PORT_\d+_(TCP|UDP)($|_)", re.IGNORECASE)
REJECTED_BUCKET_VALUES = {
    "dev",
    "false",
    "http",
    "https",
    "local",
    "none",
    "prod",
    "stage",
    "tcp",
    "test",
    "true",
    "udp",
}
MIN_BUCKET_NAME_LENGTH = 3
MAX_BUCKET_NAME_LENGTH = 128


def bucket_candidates_from_map(data: Dict[str, str], source: str, source_name: str) -> List[Dict[str, Any]]:
    out = [
        candidate
        for key, value in (data or {}).items()
        if (candidate := bucket_candidate_from_pair(str(key), "" if value is None else str(value), source, source_name))
    ]
    return sorted(out, key=lambda item: (item.get("bucket") or "", item.get("endpoint") or "", item.get("var") or ""))


def bucket_candidate_from_pair(key: str, value: str, source: str, source_name: str) -> Dict[str, Any]:
    key = (key or "").strip()
    value = (value or "").strip()
    if not should_consider_bucket_pair(key, value):
        return {}
    endpoint_data = bucket_endpoint_data(key, value)
    bucket = bucket_from_endpoint_or_value(endpoint_data, value, key)
    endpoint = endpoint_data["endpoint"]
    if not is_bucket_candidate_signal(bucket, endpoint):
        return {}
    return {
        "source": source,
        "source_name": source_name,
        "var": key,
        "bucket": bucket,
        "endpoint": endpoint,
        "confidence": bucket_confidence(key, bucket, endpoint),
    }


def should_consider_bucket_pair(key: str, value: str) -> bool:
    if not key or not value:
        return False
    if SENSITIVE_BUCKET_KEY_RE.search(key) or KUBERNETES_SERVICE_PORT_KEY_RE.search(key):
        return False
    return bool(OBJECT_STORAGE_KEY_RE.search(key))


def bucket_endpoint_data(key: str, value: str) -> Dict[str, Any]:
    parsed = parse_hostish(value) if should_parse_bucket_endpoint(key, value) else None
    host = parsed[0] if parsed else ""
    port = parsed[1] if parsed else None
    return {
        "host": host,
        "port": port,
        "path": parsed[2] if parsed else "",
        "endpoint": f"{host}:{port}" if host and port else host,
    }


def bucket_from_endpoint_or_value(endpoint_data: Dict[str, Any], value: str, key: str) -> str:
    return (
        bucket_from_host(endpoint_data["host"], key)
        or bucket_from_path(endpoint_data["path"], key)
        or bucket_from_plain_value(value, key)
    )


def is_bucket_candidate_signal(bucket: str, endpoint: str) -> bool:
    return bool(bucket or (endpoint and looks_like_object_storage_endpoint(endpoint)))


def bucket_from_host(host: str, key: str = "") -> str:
    match = VIRTUAL_HOSTED_S3_RE.search(host or "")
    if match:
        return match.group("bucket")
    first_label = (host or "").split(".", 1)[0]
    if "S3" in key.upper() and "bucket" in first_label.lower() and looks_like_bucket_name(first_label):
        return first_label
    return ""


def should_parse_bucket_endpoint(key: str, value: str) -> bool:
    return bool(ENDPOINT_KEY_RE.search(key) or "://" in value or ":" in value or "." in value)


def bucket_from_path(path: str, key: str) -> str:
    if not BUCKET_KEY_RE.search(key):
        return ""
    first_segment = (path or "").strip("/").split("/", 1)[0]
    return first_segment if looks_like_bucket_name(first_segment) else ""


def bucket_from_plain_value(value: str, key: str) -> str:
    if not BUCKET_KEY_RE.search(key) or "://" in value or "/" in value:
        return ""
    return value if looks_like_bucket_name(value) else ""


def looks_like_bucket_name(value: str) -> bool:
    if not (MIN_BUCKET_NAME_LENGTH <= len(value or "") <= MAX_BUCKET_NAME_LENGTH):
        return False
    if value.lower() in REJECTED_BUCKET_VALUES:
        return False
    if value.isdigit() or re.fullmatch(r"\d+(?:[.-]\d+)+", value):
        return False
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9.-]*[a-z0-9]", value))


def looks_like_object_storage_endpoint(endpoint: str) -> bool:
    endpoint = (endpoint or "").lower()
    return any(
        marker in endpoint
        for marker in ("s3", "ceph", "minio", "object-storage", "objectstorage", "servers.com", "openstack", "swift")
    )


def bucket_confidence(key: str, bucket: str, endpoint: str) -> str:
    if bucket and BUCKET_KEY_RE.search(key):
        return "high"
    if bucket:
        return "medium"
    if endpoint and ENDPOINT_KEY_RE.search(key):
        return "low"
    return "low"


__all__ = [
    "bucket_candidate_from_pair",
    "bucket_candidates_from_map",
    "bucket_confidence",
    "bucket_endpoint_data",
    "bucket_from_endpoint_or_value",
    "bucket_from_host",
    "bucket_from_path",
    "bucket_from_plain_value",
    "is_bucket_candidate_signal",
    "looks_like_bucket_name",
    "looks_like_object_storage_endpoint",
    "should_consider_bucket_pair",
    "should_parse_bucket_endpoint",
]
