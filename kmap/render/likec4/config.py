"""LikeC4 project config renderer."""

from pathlib import Path
from typing import Any, Dict

from ...config import clean_metadata_string
from ...io import dump_json, load_json_file
from ...model.metadata import KMAP_GENERATOR_NAME, KMAP_GENERATOR_VERSION, KMAP_RULES_FILE, generator_metadata


def likec4_write_config(output_dir: Path, architecture: Dict[str, Any], common_path: str = "../common") -> None:
    product = architecture.get("product") or {}
    existing = _existing_likec4_config(output_dir)
    existing_metadata = _existing_metadata(existing)
    product_name = product.get("name") or "Generated"

    owner = product.get("owner_team") or clean_metadata_string(existing_metadata.get("owner"))
    domain = product.get("domain") or clean_metadata_string(existing_metadata.get("domain"))
    generator = _generator_metadata(architecture)

    config = {
        "$schema": "https://likec4.dev/schemas/config.json",
        "name": product_name,
        "title": _product_title(product, existing, product_name),
        "metadata": {
            "owner": owner or "",
            "domain": domain or "",
            "generatedBy": generator.get("tool") or KMAP_GENERATOR_NAME,
            "generatorVersion": generator.get("version") or KMAP_GENERATOR_VERSION,
            "rulesFile": generator.get("rules_file") or KMAP_RULES_FILE,
        },
        "include": {
            "paths": [
                common_path,
            ],
        },
    }
    dump_json(output_dir / "likec4.config.json", config)


def _existing_likec4_config(output_dir: Path) -> Dict[str, Any]:
    existing = load_json_file(output_dir / "likec4.config.json", {})
    return existing if isinstance(existing, dict) else {}


def _existing_metadata(existing: Dict[str, Any]) -> Dict[str, Any]:
    metadata = existing.get("metadata") or {}
    return metadata if isinstance(metadata, dict) else {}


def _generator_metadata(architecture: Dict[str, Any]) -> Dict[str, Any]:
    workspace = architecture.get("workspace") or {}
    return workspace.get("generator") or generator_metadata(
        (workspace.get("source") or {}).get("config_file", ""), "likec4"
    )


def _product_title(product: Dict[str, Any], existing: Dict[str, Any], product_name: str) -> str:
    product_title = product.get("title") or ""
    existing_title = clean_metadata_string(existing.get("title"))
    if (not product_title or product_title == product_name) and existing_title and existing_title != product_name:
        product_title = existing_title
    return product_title or product_name or "Generated architecture"


__all__ = ["likec4_write_config"]
