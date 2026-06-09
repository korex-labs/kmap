from kmap.render.generated_paths import unique_generated_path


def test_unique_generated_path_uses_name_then_id_then_suffix():
    used_paths: set[str] = set()

    assert (
        unique_generated_path(
            {"id": "prj.pay.api", "name": "pay"},
            used_paths,
            directory="model/projects",
            extension="c4",
        )
        == "model/projects/pay.c4"
    )
    assert (
        unique_generated_path(
            {"id": "prj.pay.worker", "name": "pay"},
            used_paths,
            directory="model/projects",
            extension="c4",
        )
        == "model/projects/prj-pay-worker.c4"
    )
    assert (
        unique_generated_path(
            {"id": "prj.pay.worker", "name": "pay"},
            used_paths,
            directory="model/projects",
            extension="c4",
        )
        == "model/projects/prj-pay-worker-2.c4"
    )


def test_unique_generated_path_uses_project_for_blank_project_identity():
    used_paths: set[str] = set()

    assert unique_generated_path({}, used_paths, directory="model/relations", extension="dsl") == (
        "model/relations/project.dsl"
    )
