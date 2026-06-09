"""GitLab repository catalog fetching."""

from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from ..config import clean_metadata_string
from ..logging import eprint
from .repository_model import RepositoryConfig, RepositoryRecord


def fetch_gitlab_repositories(
    config: RepositoryConfig,
    token: str,
    repository_ids: list[str],
) -> list[RepositoryRecord]:
    records: dict[str, RepositoryRecord] = {}
    for repository_id in repository_ids:
        project = fetch_gitlab_project(config.base_url, repository_id, token)
        if not project:
            continue
        record = repository_record_from_gitlab_project(project)
        if record.id:
            records[record.id] = record
    return sorted(records.values(), key=lambda item: item.path_with_namespace.lower())


def fetch_gitlab_project(base_url: str, repository_id: str, token: str) -> dict[str, Any]:
    try:
        project, _next_page = fetch_gitlab_json_page(gitlab_project_url(base_url, repository_id), token)
    except HTTPError as exc:
        if exc.code in {403, 404}:
            eprint(f"[kmap] repository lookup skipped: GitLab project {repository_id} is not accessible")
            return {}
        raise
    return project if isinstance(project, dict) else {}


def gitlab_project_url(base_url: str, repository_id: str) -> str:
    root = base_url.rstrip("/")
    return f"{root}/api/v4/projects/{quote(repository_id, safe='')}"


def fetch_gitlab_json_page(url: str, token: str) -> tuple[Any, int]:
    request = Request(url, headers={"PRIVATE-TOKEN": token, "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        payload = load_json_bytes(response.read(), source=url)
        next_page = clean_metadata_string(response.headers.get("X-Next-Page"))
    return payload, int(next_page or "0")


def load_json_bytes(raw: bytes, *, source: str) -> Any:
    import json

    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON response from {source}: {exc}") from exc


def repository_record_from_gitlab_project(project: dict[str, Any]) -> RepositoryRecord:
    namespace = project.get("namespace") if isinstance(project.get("namespace"), dict) else {}
    path_with_namespace = clean_metadata_string(project.get("path_with_namespace"))
    namespace_full_path = clean_metadata_string(namespace.get("full_path"))
    group_path = namespace_full_path or group_path_from_repo_path(path_with_namespace)
    url = clean_metadata_string(project.get("http_url_to_repo") or project.get("web_url"))
    web_url = clean_metadata_string(project.get("web_url") or url)
    return RepositoryRecord(
        id=clean_metadata_string(project.get("id")),
        name=clean_metadata_string(project.get("name")),
        path=clean_metadata_string(project.get("path")),
        path_with_namespace=path_with_namespace,
        namespace_full_path=namespace_full_path,
        group_path=group_path,
        url=url,
        web_url=web_url,
        default_branch=clean_metadata_string(project.get("default_branch")),
        archived=str(bool(project.get("archived"))).lower() if project.get("archived") is not None else "",
    )


def group_path_from_repo_path(path_with_namespace: str) -> str:
    parts = [part for part in path_with_namespace.split("/") if part]
    return "/".join(parts[:-1])


__all__ = [
    "fetch_gitlab_json_page",
    "fetch_gitlab_project",
    "fetch_gitlab_repositories",
    "gitlab_project_url",
    "group_path_from_repo_path",
    "load_json_bytes",
    "repository_record_from_gitlab_project",
]
