"""Helpers for generated renderer file manifests."""

from pathlib import Path
from typing import Iterable, Mapping

from ..io import dump_json, load_json_file

GENERATED_MODEL_MANIFEST = "model/.kmap-generated.json"


def _safe_model_relative_path(relative: str) -> bool:
    if not isinstance(relative, str) or not relative.startswith("model/"):
        return False
    relative_path = Path(relative)
    return not relative_path.is_absolute() and ".." not in relative_path.parts


def remove_generated_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        return
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    if "Generated" in text and "kmap" in text:
        path.unlink()


def clean_manifest_files(output_dir: Path, manifest_path: str = GENERATED_MODEL_MANIFEST) -> None:
    manifest = load_json_file(output_dir / manifest_path, {})
    files = manifest.get("files") if isinstance(manifest, dict) else []
    if not isinstance(files, list):
        return
    for relative in files:
        if not _safe_model_relative_path(relative):
            continue
        path = output_dir / relative
        if path.is_file():
            path.unlink()


def clean_generated_files(
    output_dir: Path,
    *,
    suffix: str,
    legacy_files: Iterable[str] = (),
    force_files: Iterable[str] = (),
    generated_dirs: Iterable[str] = (),
    manifest_path: str = GENERATED_MODEL_MANIFEST,
) -> None:
    clean_manifest_files(output_dir, manifest_path)
    for relative in force_files:
        path = output_dir / relative
        if path.exists() and path.is_file():
            path.unlink()
    for relative in legacy_files:
        remove_generated_file(output_dir / relative)
    for relative_dir in generated_dirs:
        directory = output_dir / relative_dir
        if not directory.exists():
            continue
        for path in directory.glob(f"*{suffix}"):
            remove_generated_file(path)


def write_generated_manifest(
    output_dir: Path,
    *,
    kind: str,
    files: Mapping[str, str],
    manifest_path: str = GENERATED_MODEL_MANIFEST,
) -> None:
    dump_json(
        output_dir / manifest_path,
        {
            "generator": "kmap",
            "kind": kind,
            "files": sorted(files),
        },
    )


__all__ = [
    "GENERATED_MODEL_MANIFEST",
    "clean_generated_files",
    "clean_manifest_files",
    "remove_generated_file",
    "write_generated_manifest",
]
