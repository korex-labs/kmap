"""Dependency relation file loading and writing."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..io import load_required_json_file, write_text_atomic

DEPENDENCY_LIST_FIELD_COUNT = 8
DEPENDENCY_LIST_SEPARATOR = " | "


def load_dependency_relations(dependencies_file: Optional[str]) -> List[Dict[str, Any]]:
    if not dependencies_file:
        return []
    path = Path(dependencies_file)
    if not path.exists():
        return []

    if path.suffix.lower() == ".json":
        rows = load_required_json_file(path)
        return rows if isinstance(rows, list) else []

    rows = []
    with path.open("r", encoding="utf-8", errors="replace") as file:
        for line in file:
            row = dependency_relation_from_line(line)
            if row:
                rows.append(row)
    return rows


def dependency_relation_from_line(line: str) -> Dict[str, Any] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = [part.strip() for part in line.split(DEPENDENCY_LIST_SEPARATOR, DEPENDENCY_LIST_FIELD_COUNT - 1)]
    if len(parts) != DEPENDENCY_LIST_FIELD_COUNT:
        return None
    return {
        "source_service": parts[0],
        "source_var": parts[1],
        "dependency_key": parts[2],
        "dependency_type": parts[3],
        "target_service": parts[4],
        "source_origin": parts[5],
        "match_type": parts[6],
        "evidence": parts[7],
    }


def write_dependency_relations(out_path: Path, rows: List[Dict[str, Any]]) -> None:
    lines = [dependency_relation_line(row) for row in rows]
    write_text_atomic(out_path, "\n".join(lines) + ("\n" if lines else ""))


def dependency_relation_line(row: Dict[str, Any]) -> str:
    parts = [
        row["source_service"],
        row["source_var"],
        row["dependency_key"],
        row["dependency_type"],
        row["target_service"],
        row["source_origin"],
        row["match_type"],
        row["evidence"],
    ]
    return DEPENDENCY_LIST_SEPARATOR.join(parts)


__all__ = [
    "DEPENDENCY_LIST_FIELD_COUNT",
    "DEPENDENCY_LIST_SEPARATOR",
    "dependency_relation_from_line",
    "dependency_relation_line",
    "load_dependency_relations",
    "write_dependency_relations",
]
