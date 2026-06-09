"""Bucket usage signal heuristics."""

import re
from typing import Any

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


def key_for_bucket_candidate(candidate: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(candidate.get("bucket") or "").lower(),
        str(candidate.get("endpoint") or "").lower(),
        str(candidate.get("var") or "").lower(),
    )


def is_bucket_usage_signal(candidate: dict[str, Any]) -> bool:
    bucket = str(candidate.get("bucket") or "")
    endpoint = str(candidate.get("endpoint") or "")
    if bucket and not looks_like_false_positive_bucket(bucket):
        return True
    return bool(endpoint and looks_like_object_storage_endpoint(endpoint))


def looks_like_false_positive_bucket(bucket: str) -> bool:
    return (
        bucket.lower() in REJECTED_BUCKET_VALUES or bucket.isdigit() or bool(re.fullmatch(r"\d+(?:[.-]\d+)+", bucket))
    )


def looks_like_object_storage_endpoint(endpoint: str) -> bool:
    endpoint = (endpoint or "").lower()
    return any(
        marker in endpoint
        for marker in ("s3", "ceph", "minio", "object-storage", "objectstorage", "servers.com", "openstack", "swift")
    )


__all__ = [
    "REJECTED_BUCKET_VALUES",
    "is_bucket_usage_signal",
    "key_for_bucket_candidate",
    "looks_like_false_positive_bucket",
    "looks_like_object_storage_endpoint",
]
