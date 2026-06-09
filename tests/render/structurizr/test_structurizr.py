from kmap.render.structurizr import structurizr_resource_lines
from kmap.rendering_resources import project_discovery_items, project_resource_items, short_join_unique


def test_project_resource_items_normalizes_and_adds_repo_fallback():
    items = project_resource_items(
        {
            "repo": "https://git.example/api",
            "resources": {
                "Run Book": "https://docs.example/runbook",
                "empty": "",
            },
        }
    )

    assert items == [
        ("Run_Book", "https://docs.example/runbook"),
        ("repo", "https://git.example/api"),
    ]


def test_project_resource_items_skips_blank_values_and_prefers_explicit_repo():
    assert project_resource_items(
        {
            "repo": "https://git.example/fallback",
            "resources": {
                "repo": "https://git.example/explicit",
                "blank": " ",
            },
        }
    ) == [("repo", "https://git.example/explicit")]


def test_project_resource_items_do_not_auto_promote_discovery():
    items = project_resource_items(
        {"discovery": {"namespaces": ["api"], "clusters": ["cluster-a"]}},
        [
            {
                "discovery": {
                    "clusters": ["cluster-b", "cluster-a"],
                    "namespaces": ["api", "worker"],
                    "workloads": ["api-deploy"],
                }
            }
        ],
    )

    assert ("clusters", "cluster-a, cluster-b") not in items
    assert ("namespaces", "api, worker") not in items
    assert ("workloads", "api-deploy") not in items


def test_project_discovery_items_are_available_without_declared_resources():
    assert project_discovery_items({"discovery": {"namespaces": ["api"]}}) == [
        ("clusters", ""),
        ("namespaces", "api"),
        ("workloads", ""),
    ]
    assert short_join_unique(["a", "A", "b"], limit=1) == "a, +1 more"


def test_project_discovery_items_merge_container_discovery_values():
    assert project_discovery_items(
        {"discovery": {"clusters": ["cluster-a"], "namespaces": ["api"], "workloads": ["api"]}},
        [
            {"discovery": {"clusters": ["cluster-b", "cluster-a"], "namespaces": ["worker"]}},
            {"discovery": {"workloads": ["api", "worker"]}},
        ],
    ) == [
        ("clusters", "cluster-a, cluster-b"),
        ("namespaces", "api, worker"),
        ("workloads", "api, worker"),
    ]


def test_structurizr_resource_lines_emit_url_and_resource_properties():
    lines = structurizr_resource_lines(
        {"resources": {"repo": "https://git.example/api", "dash": 'quoted "value"'}},
        indent="    ",
        extra_items=[("logs", "https://logs.example/api")],
    )

    assert lines[0] == "    url https://git.example/api"
    assert '      "resource.dash" "quoted \\"value\\""' in lines
    assert '      "resource.logs" "https://logs.example/api"' in lines


def test_structurizr_resource_lines_skip_unsafe_urls_but_escape_properties():
    lines = structurizr_resource_lines(
        {"resources": {"repo": 'https://git.example/"bad"\ninclude hacked', "path": "C:\\tmp\\repo"}},
        indent="    ",
    )

    assert not any(line.strip().startswith("url ") for line in lines)
    assert '      "resource.repo" "https://git.example/\\"bad\\"\\ninclude hacked"' in lines
    assert '      "resource.path" "C:\\\\tmp\\\\repo"' in lines
