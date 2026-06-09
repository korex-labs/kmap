"""Structurizr model rendering compatibility facade."""

from .model_content import render_structurizr_model
from .model_files import render_structurizr_model_files
from .references import (
    structurizr_alias,
    structurizr_external_alias,
    structurizr_external_container_alias,
    structurizr_reference_map,
    structurizr_system_alias,
)

__all__ = [
    "render_structurizr_model",
    "render_structurizr_model_files",
    "structurizr_alias",
    "structurizr_external_alias",
    "structurizr_external_container_alias",
    "structurizr_reference_map",
    "structurizr_system_alias",
]
