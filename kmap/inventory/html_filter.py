"""Client-side inventory table filtering script rendering."""

from html import escape


def render_filter_script(*, input_id: str, table_id: str, empty_id: str) -> list[str]:
    return [
        "  <script>",
        f"    const filter = document.getElementById('{escape(input_id)}');",
        f"    const archived = document.getElementById('{escape(input_id)}-archived');",
        f"    const rows = Array.from(document.querySelectorAll('#{escape(table_id)} tbody tr'));",
        f"    const empty = document.getElementById('{escape(empty_id)}');",
        "    const applyFilter = () => {",
        "      const query = filter.value.trim().toLowerCase();",
        "      const archivedOnly = archived ? archived.checked : false;",
        "      let visible = 0;",
        "      for (const row of rows) {",
        "        const textMatched = row.textContent.toLowerCase().includes(query);",
        "        const archiveMatched = !archivedOnly || row.dataset.repositoryArchived === 'true';",
        "        const matched = textMatched && archiveMatched;",
        "        row.hidden = !matched;",
        "        if (matched) visible += 1;",
        "      }",
        "      empty.style.display = visible === 0 ? 'block' : 'none';",
        "    };",
        "    filter.addEventListener('input', applyFilter);",
        "    if (archived) archived.addEventListener('change', applyFilter);",
        "  </script>",
    ]


__all__ = ["render_filter_script"]
