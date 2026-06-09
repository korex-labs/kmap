"""Compatibility exports for dependency relation file helpers."""

from ...relations import (
    DEPENDENCY_LIST_FIELD_COUNT,
    DEPENDENCY_LIST_SEPARATOR,
    dependency_relation_from_line,
    dependency_relation_line,
    load_dependency_relations,
    write_dependency_relations,
)

__all__ = [
    "DEPENDENCY_LIST_FIELD_COUNT",
    "DEPENDENCY_LIST_SEPARATOR",
    "dependency_relation_from_line",
    "dependency_relation_line",
    "load_dependency_relations",
    "write_dependency_relations",
]
