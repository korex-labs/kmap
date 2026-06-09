"""Shared inventory page styles."""

BASE_PAGE_STYLES = [
    "    :root { color-scheme: light; --bg: #f7f9fc; --panel: #ffffff; --text: #1f2933; --muted: #52606d; --line: #d9e2ec; --soft: #eef2f7; --accent: #0967d2; }",
    "    * { box-sizing: border-box; }",
    '    body { margin: 0; background: var(--bg); color: var(--text); font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }',
    "    header { display: flex; justify-content: space-between; gap: 24px; align-items: flex-end; margin-bottom: 24px; }",
    "    nav { display: flex; gap: 12px; margin-bottom: 18px; }",
    "    h1 { margin: 0 0 8px; font-size: 2rem; line-height: 1.15; letter-spacing: 0; }",
    "    .summary { margin: 0; color: var(--muted); }",
    "    .generated { text-align: right; white-space: nowrap; }",
    "    .stat { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px 16px; }",
    "    .stat strong { display: block; font-size: 1.35rem; line-height: 1.1; }",
    "    .stat span { color: var(--muted); font-size: 0.82rem; }",
    "    .toolbar { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; margin-bottom: 12px; }",
    "    .toolbar label { display: inline-flex; align-items: center; gap: 7px; color: var(--muted); font-size: 0.9rem; white-space: nowrap; }",
    '    input[type="search"] { width: min(520px, 100%); border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px; font: inherit; background: var(--panel); color: var(--text); }',
    "    .table-wrap { overflow: auto; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; }",
    "    table { border-collapse: collapse; width: 100%; }",
    "    th, td { border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }",
    "    th { position: sticky; top: 0; background: var(--soft); z-index: 1; text-transform: uppercase; color: #334e68; letter-spacing: 0; }",
    "    tbody tr:nth-child(even) td { background: #fbfdff; }",
    "    tr:hover td { background: #f0f7ff; }",
    "    td code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }",
    "    .primary { display: block; font-weight: 500; }",
    "    .secondary { display: block; margin-top: 3px; color: var(--muted); font-size: 0.8rem; }",
    "    a { color: var(--accent); text-decoration: none; font-weight: 600; }",
    "    a:hover { text-decoration: underline; }",
    "    .chip { display: inline-block; margin-left: 6px; border: 1px solid #bcccdc; border-radius: 999px; padding: 1px 7px; color: #334e68; background: #f0f4f8; font-size: 0.76rem; font-weight: 700; white-space: nowrap; }",
    "    .chip.archived { color: #92400e; background: #fef3c7; border-color: #f59e0b; }",
    "    .state { display: inline-block; border-radius: 999px; padding: 2px 8px; font-size: 0.76rem; font-weight: 800; text-transform: uppercase; white-space: nowrap; }",
    "    .state.current { color: #0b6b3a; background: #dff6e8; border: 1px solid #9bd8b3; }",
    "    .state.carried { color: #92400e; background: #fef3c7; border: 1px solid #fbbf24; }",
    "    .missing { color: #9aa5b1; font-style: italic; }",
    "    .empty { display: none; padding: 24px; color: var(--muted); }",
]


__all__ = ["BASE_PAGE_STYLES"]
