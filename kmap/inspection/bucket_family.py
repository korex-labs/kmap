"""Shared bucket source variable family parsing."""

import re
from collections.abc import Collection

BUCKET_SOURCE_FAMILY_STOP_TOKENS = {"BASE", "BUCKET", "ENDPOINT", "HOST", "NAME", "URL", "URI"}


def bucket_source_family_name(source_var: str, *, extra_stop_tokens: Collection[str] = ()) -> str:
    stop_tokens = BUCKET_SOURCE_FAMILY_STOP_TOKENS | {str(token).upper() for token in extra_stop_tokens}
    family_tokens = []
    for token in [part for part in re.split(r"_+", source_var.upper()) if part]:
        if token in stop_tokens:
            break
        family_tokens.append(token)
    return "_".join(family_tokens)


__all__ = ["BUCKET_SOURCE_FAMILY_STOP_TOKENS", "bucket_source_family_name"]
