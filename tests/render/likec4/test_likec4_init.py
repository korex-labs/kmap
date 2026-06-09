import kmap.render.likec4 as likec4_entrypoint
from kmap.render.likec4.common import likec4_alias, likec4_metadata_lines, likec4_reference_map
from kmap.render.likec4.config import likec4_write_config
from kmap.render.likec4.deployment import render_likec4_deployment
from kmap.render.likec4.model import render_likec4_model, render_likec4_model_files
from kmap.render.likec4.readme import render_likec4_readme
from kmap.render.likec4.relations import render_likec4_relation_files, render_likec4_relations
from kmap.render.likec4.specification import render_likec4_specification
from kmap.render.likec4.views import render_likec4_views


def test_likec4_entrypoint_reexports_helper_imports():
    assert sorted(likec4_entrypoint.__all__) == [
        "default_likec4_output_dir",
        "likec4_alias",
        "likec4_external_resource_lines",
        "likec4_link_label",
        "likec4_metadata_lines",
        "likec4_reference_map",
        "likec4_relationship_kind",
        "likec4_system_description",
        "likec4_system_resource_lines",
        "likec4_write_config",
        "render_likec4",
        "render_likec4_deployment",
        "render_likec4_model",
        "render_likec4_model_files",
        "render_likec4_readme",
        "render_likec4_relation_files",
        "render_likec4_relations",
        "render_likec4_specification",
        "render_likec4_views",
    ]
    assert likec4_entrypoint.likec4_alias is likec4_alias
    assert likec4_entrypoint.likec4_metadata_lines is likec4_metadata_lines
    assert likec4_entrypoint.likec4_reference_map is likec4_reference_map
    assert likec4_entrypoint.likec4_write_config is likec4_write_config
    assert likec4_entrypoint.render_likec4_deployment is render_likec4_deployment
    assert likec4_entrypoint.render_likec4_model is render_likec4_model
    assert likec4_entrypoint.render_likec4_model_files is render_likec4_model_files
    assert likec4_entrypoint.render_likec4_relation_files is render_likec4_relation_files
    assert likec4_entrypoint.render_likec4_readme is render_likec4_readme
    assert likec4_entrypoint.render_likec4_relations is render_likec4_relations
    assert likec4_entrypoint.render_likec4_specification is render_likec4_specification
    assert likec4_entrypoint.render_likec4_views is render_likec4_views
