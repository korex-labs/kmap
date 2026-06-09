"""CLI parser and command dispatch for kmap."""

import argparse
from typing import List, Optional

from .command.combine.cli import add_combine_parser
from .command.config_recommend.cli import add_config_recommend_parser
from .command.inspect.cli import add_inspect_parser
from .command.normalize.cli import add_normalize_parser
from .command.render.cli import add_render_parser
from .command.render_inventory.cli import add_render_inventory_parser
from .command.run_all.cli import add_run_all_parser
from .command.validate_config.cli import add_validate_config_parser
from .command.validate_likec4.cli import add_validate_likec4_parser
from .command.validate_structurizr.cli import add_validate_structurizr_parser
from .command.view.cli import add_view_parser
from .config import apply_config_overrides
from .env import load_dotenv_files
from .logging import eprint
from .paths import KMAP_TMP_DIR
from .tool_config import apply_tool_config_overrides

DEFAULT_REPORTS_DIR = str(KMAP_TMP_DIR / "reports")
DEFAULT_DEPENDENCIES_FILE = str(KMAP_TMP_DIR / "reports" / "dependencies.list")
DEFAULT_ARCHITECTURE_FILE = str(KMAP_TMP_DIR / "reports" / "architecture.json")
DEFAULT_MATCH_RE = r"(^|[-_.])(main|master)([-_.]|$)"


def parse_non_negative_float(value: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(f"expected a non-negative number, got {value!r}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError(f"expected a non-negative number, got {value!r}")
    return parsed


def parse_positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Kubernetes architecture map generator")
    parser.add_argument("--kmap-config", default=None, help="kmap tool config path")
    sub = parser.add_subparsers(dest="command", required=True)

    add_config_recommend_parser(sub)
    add_validate_config_parser(sub)
    add_validate_likec4_parser(sub)
    add_validate_structurizr_parser(sub)
    add_render_inventory_parser(sub)

    add_inspect_parser(
        sub,
        default_reports_dir=DEFAULT_REPORTS_DIR,
        default_match_re=DEFAULT_MATCH_RE,
        parse_non_negative_float=parse_non_negative_float,
        parse_positive_int=parse_positive_int,
    )

    add_combine_parser(
        sub,
        default_reports_dir=DEFAULT_REPORTS_DIR,
        default_dependencies_file=DEFAULT_DEPENDENCIES_FILE,
    )

    add_normalize_parser(
        sub,
        default_reports_dir=DEFAULT_REPORTS_DIR,
        default_dependencies_file=DEFAULT_DEPENDENCIES_FILE,
        default_architecture_file=DEFAULT_ARCHITECTURE_FILE,
    )

    add_render_parser(sub, default_architecture_file=DEFAULT_ARCHITECTURE_FILE)

    add_view_parser(sub)

    add_run_all_parser(
        sub,
        default_reports_dir=DEFAULT_REPORTS_DIR,
        default_dependencies_file=DEFAULT_DEPENDENCIES_FILE,
        default_architecture_file=DEFAULT_ARCHITECTURE_FILE,
        default_match_re=DEFAULT_MATCH_RE,
        parse_non_negative_float=parse_non_negative_float,
        parse_positive_int=parse_positive_int,
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    try:
        load_dotenv_files()
        parser = build_parser()
        args = parser.parse_args(argv)
        args = apply_tool_config_overrides(args)
        args = apply_config_overrides(args)
        return args.func(args)
    except KeyboardInterrupt:
        eprint("\n[kmap] interrupted; stopping without updating partially written output files")
        return 130


__all__ = [
    "apply_config_overrides",
    "apply_tool_config_overrides",
    "build_parser",
    "main",
    "parse_non_negative_float",
    "parse_positive_int",
]
