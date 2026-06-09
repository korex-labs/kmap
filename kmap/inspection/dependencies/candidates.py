"""Dependency candidate parsing and deduplication."""

import re
from typing import Any, Dict, List, Tuple

from ...database import database_metadata_for_candidate
from .dedup import (
    DEPENDENCY_SOURCE_RANK,
    dedupe_dependency_candidates,
    dependency_candidate_dedupe_key,
    dependency_candidate_sort_key,
    dependency_candidate_source_rank,
)
from .env import parse_env_block
from .model import (
    BaseDependencyCandidateInput,
    DependencyCandidateInput,
)
from .parsing import dependency_candidate_key, dependency_value_parts, parse_dependency_hostish

SUSPECT_KEY_RE = re.compile(r"(HOST|ADDR|ADDRESS|ENDPOINT|URL|URI|DSN|BROKER|BOOTSTRAP|SERVER|AMQP|GRPC)", re.I)
IGNORE_KEY_RE = re.compile(
    r"(^HOSTNAME$|^SERVER_NAME$|SERVER_MODE|API_KEY|PASSWORD|PASSWD|PASS\b|TOKEN\b|SECRET\b|PRIVATE_KEY\b|ACCESS_KEY\b|"
    r"[A-Z0-9]+_[0-9]{2,5}|.*_(TEST|RELEASE|QA|DEV)_.*)",
    re.I,
)


def dependency_candidates_from_map(data: Dict[str, str], source: str, source_name: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for key, value in (data or {}).items():
        key = str(key)
        value = "" if value is None else str(value).strip()
        if not should_consider_dependency_pair(key, value):
            continue
        out.extend(dependency_candidates_from_pair(data, key, value, source, source_name))
    return out


def should_consider_dependency_pair(key: str, value: str) -> bool:
    if not key or not value:
        return False
    if IGNORE_KEY_RE.search(key):
        return False
    return bool(SUSPECT_KEY_RE.search(key))


def dependency_candidates_from_pair(
    data: Dict[str, str],
    key: str,
    value: str,
    source: str,
    source_name: str,
) -> List[Dict[str, Any]]:
    candidates = []
    candidate_input = DependencyCandidateInput(
        data=data,
        key=key,
        value=value,
        source=source,
        source_name=source_name,
    )
    for raw_part in dependency_value_parts(value):
        candidate = dependency_candidate_from_input(candidate_input, raw_part)
        if candidate:
            candidates.append(candidate)
    return candidates


def dependency_candidate_from_raw_part(
    data: Dict[str, str],
    key: str,
    value: str,
    raw_part: str,
    *source_parts: str,
) -> Dict[str, Any]:
    source, source_name = source_parts
    return dependency_candidate_from_input(
        DependencyCandidateInput(
            data=data,
            key=key,
            value=value,
            source=source,
            source_name=source_name,
        ),
        raw_part,
    )


def dependency_candidate_from_input(candidate_input: DependencyCandidateInput, raw_part: str) -> Dict[str, Any]:
    parsed = parse_dependency_hostish(raw_part)
    if not parsed:
        return {}
    return dependency_candidate(candidate_input, raw_part, parsed)


def dependency_candidate(
    candidate_input: DependencyCandidateInput,
    raw_part: str,
    parsed: Tuple[str, int | None, str],
) -> Dict[str, Any]:
    host, port, path = parsed
    item = base_dependency_candidate(
        BaseDependencyCandidateInput(
            key=candidate_input.key,
            value=candidate_input.value,
            host=host,
            port=port,
            path=path,
            source=candidate_input.source,
            source_name=candidate_input.source_name,
        )
    )
    attach_dependency_database_metadata(item, candidate_input.data, candidate_input.key, raw_part, host)
    return item


def base_dependency_candidate(candidate_input: BaseDependencyCandidateInput) -> Dict[str, Any]:
    return {
        "source": candidate_input.source,
        "source_name": candidate_input.source_name,
        "var": candidate_input.key,
        "key": dependency_candidate_key(candidate_input.host, candidate_input.port),
        "value": candidate_input.value,
        "host": candidate_input.host,
        "port": candidate_input.port,
        "path": candidate_input.path,
        "class": "external_candidate",
    }


def attach_dependency_database_metadata(
    item: Dict[str, Any],
    data: Dict[str, str],
    key: str,
    raw_part: str,
    host: str,
) -> None:
    database = database_metadata_for_candidate(data, key, raw_part, host)
    if database:
        item["metadata"] = {"database": database}


__all__ = [
    "DEPENDENCY_SOURCE_RANK",
    "IGNORE_KEY_RE",
    "SUSPECT_KEY_RE",
    "BaseDependencyCandidateInput",
    "DependencyCandidateInput",
    "attach_dependency_database_metadata",
    "base_dependency_candidate",
    "dedupe_dependency_candidates",
    "dependency_candidate",
    "dependency_candidate_dedupe_key",
    "dependency_candidate_from_input",
    "dependency_candidate_from_raw_part",
    "dependency_candidate_key",
    "dependency_candidate_sort_key",
    "dependency_candidate_source_rank",
    "dependency_candidates_from_map",
    "dependency_candidates_from_pair",
    "dependency_value_parts",
    "parse_dependency_hostish",
    "parse_env_block",
    "should_consider_dependency_pair",
]
