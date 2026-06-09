from argparse import Namespace

from kmap.command.config_recommend import (
    ConfigRecommendation,
    config_recommend,
    has_config_value,
    namespace_recommendations,
    print_recommendations,
    project_config,
    recommend_config,
)


def test_config_recommend_validates_before_recommending(tmp_path, capsys):
    config = tmp_path / "bad.yaml"
    config.write_text("product: demo\n", encoding="utf-8")

    assert config_recommend(Namespace(config_file=str(config))) == 1

    captured = capsys.readouterr()
    assert "config validation failed" in captured.err
    assert "title: required" in captured.err
    assert "config recommendations" not in captured.out


def test_config_recommend_reports_missing_file(tmp_path, capsys):
    assert config_recommend(Namespace(config_file=str(tmp_path / "missing.yaml"))) == 1

    captured = capsys.readouterr()
    assert "config validation failed" in captured.err
    assert "file not found" in captured.err
    assert captured.out == ""


def test_config_recommend_reports_directory_path(tmp_path, capsys):
    assert config_recommend(Namespace(config_file=str(tmp_path))) == 1

    captured = capsys.readouterr()
    assert "path is not a file" in captured.err


def test_config_recommend_prints_validation_warnings_with_errors(tmp_path, capsys):
    config = tmp_path / "bad.yaml"
    config.write_text(
        """
product: demo
title: Demo
env: prod
namespaces: []
""",
        encoding="utf-8",
    )

    assert config_recommend(Namespace(config_file=str(config))) == 1

    captured = capsys.readouterr()
    assert "namespaces: required and must not be empty" in captured.err
    assert "owner_team: recommended" in captured.err


def test_config_recommend_prints_advisory_recommendations(tmp_path, capsys):
    config = tmp_path / "minimal.yaml"
    config.write_text(
        """
org: web
product: demo
title: Demo
env: prod
owner_team: Team
namespaces:
  demo-api-prod: {}
""",
        encoding="utf-8",
    )

    assert config_recommend(Namespace(config_file=str(config))) == 0

    captured = capsys.readouterr()
    assert "[kmap] config recommendations:" in captured.out
    assert "[medium] domain" in captured.out
    assert "[medium] namespaces.*.project.title" in captured.out
    assert "[low] tags" not in captured.out
    assert "[low] namespaces.*.project.tags" not in captured.out
    assert "[high] namespaces.*.resources.repo" in captured.out
    assert "namespaces.demo-api-prod.resources.repo" in captured.out
    assert "Example:" in captured.out


def test_recommend_config_groups_namespace_gaps_and_required_resources():
    recommendations = recommend_config(
        {
            "product": "demo",
            "title": "Demo",
            "env": "prod",
            "owner_team": "Team",
            "namespaces": {
                "api-prod": {},
                "worker-prod": {"project": {"title": "Worker"}, "resources": {"repo": "https://git/repo"}},
            },
        }
    )

    by_path = {recommendation.path: recommendation for recommendation in recommendations}

    assert by_path["namespaces.*.project.title"].details == ("namespaces.api-prod.project.title",)
    assert by_path["namespaces.*.resources.repo"].priority == "high"
    assert by_path["namespaces.*.resources.repo"].details == ("namespaces.api-prod.resources.repo",)
    assert "namespaces.*.resources.tasks" not in by_path
    assert "namespaces.worker-prod.project.element_type" in by_path["namespaces.*.project.element_type"].details
    assert "namespaces.*.project.tags" not in by_path
    assert [recommendation.priority for recommendation in recommendations][:1] == ["high"]


def test_recommend_config_can_include_low_priority_suggestions():
    recommendations = recommend_config(
        {
            "product": "demo",
            "title": "Demo",
            "env": "prod",
            "owner_team": "Team",
            "namespaces": {"api-prod": {}},
        },
        include_low=True,
    )
    by_path = {recommendation.path: recommendation for recommendation in recommendations}

    assert by_path["system_naming"].priority == "low"
    assert by_path["namespaces.*.project.tags"].priority == "low"
    assert by_path["namespaces.*.project.tags"].details == ("namespaces.api-prod.project.tags",)


def test_namespace_recommendations_accepts_namespace_list_and_non_mapping_items():
    recommendations = namespace_recommendations({"namespaces": ["api-prod"], "namespace": "ignored"})
    by_path = {recommendation.path: recommendation for recommendation in recommendations}

    assert by_path["namespaces.*.project.title"].details == ("namespaces.api-prod.project.title",)
    assert "namespaces.*.resources.monitoring" not in by_path


def test_namespace_recommendations_include_optional_when_requested():
    recommendations = namespace_recommendations({"namespaces": ["api-prod"]}, include_optional=True)
    by_path = {recommendation.path: recommendation for recommendation in recommendations}

    assert by_path["namespaces.*.resources.monitoring"].priority == "low"
    assert by_path["namespaces.*.resources.monitoring"].details == ("namespaces.api-prod.resources.monitoring",)


def test_namespace_recommendations_use_product_resource_inheritance():
    recommendations = namespace_recommendations(
        {"resources": {"repo": "https://git/product"}, "namespaces": {"api-prod": {}}}
    )
    paths = [recommendation.path for recommendation in recommendations]

    assert "namespaces.*.resources.repo" not in paths


def test_namespace_recommendations_ignores_invalid_namespace_shape():
    assert namespace_recommendations({"namespaces": "api-prod"}) == []


def test_project_config_uses_string_project_as_title():
    assert project_config({"project": "Payments API"}) == {"title": "Payments API"}
    assert project_config({"project": ""}) == {}


def test_has_config_value_classifies_empty_and_non_empty_values():
    assert not has_config_value({"tags": []}, "tags")
    assert not has_config_value({"title": " "}, "title")
    assert has_config_value({"count": 0}, "count")
    assert has_config_value({"tags": ["api"]}, "tags")


def test_print_recommendations_handles_empty_snippetless_and_details(capsys):
    print_recommendations("demo.yaml", [])
    assert "No recommendations" in capsys.readouterr().out

    print_recommendations("demo.yaml", [ConfigRecommendation("low", "path", "reason")])
    captured = capsys.readouterr()
    assert "[low] path" in captured.out
    assert "Example:" not in captured.out

    print_recommendations(
        "demo.yaml",
        [ConfigRecommendation("high", "path", "reason", details=("one", "two", "three", "four"))],
    )
    captured = capsys.readouterr()
    assert "... +1 more; use --details to list all" in captured.out

    print_recommendations(
        "demo.yaml",
        [ConfigRecommendation("high", "path", "reason", details=("one", "two", "three", "four"))],
        details=True,
    )
    captured = capsys.readouterr()
    assert "     - four" in captured.out
