"""Project discovery for LikeC4 validation."""

from pathlib import Path


def selected_likec4_projects(
    root: Path,
    products: list[str],
    *,
    include_multi_project: bool = False,
) -> list[Path]:
    if products:
        return [root / product for product in products]
    projects = sorted(path.parent for path in root.glob("**/likec4.config.json"))
    if include_multi_project:
        return projects
    return [project for project in projects if not has_nested_likec4_projects(project)]


def has_nested_likec4_projects(project_dir: Path) -> bool:
    return any(path.parent != project_dir for path in project_dir.glob("*/likec4.config.json"))


__all__ = ["has_nested_likec4_projects", "selected_likec4_projects"]
