"""State cell rendering for namespace inventory pages."""

from datetime import datetime
from html import escape


def render_state_cell(last_seen_at: str, generated_at: datetime | None = None) -> str:
    if not last_seen_at:
        return '<td><span class="missing">unknown</span></td>'
    generated = generated_at.isoformat(timespec="seconds") if generated_at else ""
    status = "current" if generated and last_seen_at >= generated else "carried"
    return (
        f'<td><span class="state {escape(status)}" title="Last seen: {escape(last_seen_at)}">'
        f"{escape(status)}</span></td>"
    )


__all__ = ["render_state_cell"]
