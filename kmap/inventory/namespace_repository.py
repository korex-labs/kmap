"""Repository cell rendering for namespace inventory pages."""

from html import escape
from urllib.parse import urlparse


def render_repository(repository: str, usage_count: int = 0, *, archived: bool = False) -> str:
    if not repository:
        return '<span class="missing">missing</span>'
    escaped_repository = escape(repository)
    if repository.startswith(("http://", "https://")):
        label = escape(repository_label(repository))
        repository_html = (
            f'<a href="{escaped_repository}" title="{escaped_repository}" target="_blank" rel="noopener">{label}</a>'
        )
    else:
        repository_html = escaped_repository
    if usage_count > 1:
        repository_html += (
            f' <span class="chip" title="Repository is used by {usage_count} namespaces">x{usage_count}</span>'
        )
    if archived:
        repository_html += ' <span class="chip archived" title="Repository is archived">archived</span>'
    return repository_html


def repository_archived(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def repository_label(repository: str) -> str:
    parsed = urlparse(repository)
    path = parsed.path.strip("/")
    if path:
        return path.removesuffix(".git")
    return parsed.netloc or repository


__all__ = ["render_repository", "repository_archived", "repository_label"]
