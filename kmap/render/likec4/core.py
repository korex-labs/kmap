"""LikeC4 render command orchestration."""

from pathlib import Path

from ...config import slug_name
from ...io import ensure_dir, load_required_json_file, write_text_atomic
from ...logging import eprint
from ...paths import SCHEMAS_ROOT
from ..generated_files import clean_generated_files, write_generated_manifest
from .config import likec4_write_config
from .deployment import render_likec4_deployment
from .model import render_likec4_model_files
from .readme import render_likec4_readme
from .relations import render_likec4_relation_files
from .specification import render_likec4_specification
from .views import render_likec4_views


def default_likec4_output_dir(product: str) -> Path:
    return SCHEMAS_ROOT / "Likec4" / slug_name(product or "product")


def _clean_generated_model_files(output_dir: Path, suffix: str) -> None:
    clean_generated_files(
        output_dir,
        suffix=suffix,
        legacy_files=("model/product.c4", "model/relations.c4", "model/generated.dsl", "model/00-external.c4"),
        generated_dirs=("model/projects", "model/external", "model/relations"),
    )


def render_likec4(args) -> int:
    architecture_path = Path(args.architecture_file)
    architecture = load_required_json_file(architecture_path)
    if not isinstance(architecture, dict) or not architecture:
        raise SystemExit(f"Invalid architecture model: {architecture_path}")

    product_name = (
        ((architecture.get("product") or {}).get("name"))
        or ((architecture.get("workspace") or {}).get("product"))
        or "product"
    )
    output_dir = Path(args.output_dir) if args.output_dir else default_likec4_output_dir(product_name)
    common_path = args.common_path or "../common"
    if Path(common_path).is_absolute():
        raise SystemExit("LikeC4 include paths must be relative; use a relative --common-path")
    ensure_dir(output_dir)
    ensure_dir(output_dir / "model")
    ensure_dir(output_dir / "model" / "projects")
    ensure_dir(output_dir / "model" / "relations")
    ensure_dir(output_dir / "deployments")
    ensure_dir(output_dir / "specification")
    ensure_dir(output_dir / "views")

    likec4_write_config(output_dir, architecture, common_path)
    _clean_generated_model_files(output_dir, ".c4")
    model_files = {
        **render_likec4_model_files(architecture),
        **render_likec4_relation_files(architecture),
    }
    for relative_path, content in model_files.items():
        target = output_dir / relative_path
        ensure_dir(target.parent)
        write_text_atomic(target, content)
    write_generated_manifest(output_dir, kind="likec4-model", files=model_files)
    for deployment in architecture.get("deployments") or []:
        env = deployment.get("env") or "env"
        write_text_atomic(
            output_dir / "deployments" / f"{slug_name(env)}.c4",
            render_likec4_deployment(architecture, deployment),
        )
    write_text_atomic(
        output_dir / "specification" / "generated.c4",
        render_likec4_specification(architecture),
    )
    write_text_atomic(output_dir / "views" / "generated.c4", render_likec4_views(architecture))
    write_text_atomic(output_dir / "README.md", render_likec4_readme(architecture))

    eprint(f"[kmap] wrote LikeC4 project: {output_dir}")
    return 0


__all__ = [
    "default_likec4_output_dir",
    "render_likec4",
]
