import re

from kmap.inspection.workloads import (
    all_workload_items,
    matching_helm_release_names,
    matching_workload_items,
    related_replicasets_by_deployment,
    select_workloads,
    workload_source_items,
)


def test_related_replicasets_by_deployment_groups_owned_replicasets():
    grouped = related_replicasets_by_deployment(
        {
            "items": [
                {
                    "metadata": {
                        "name": "api-rs-b",
                        "ownerReferences": [{"kind": "Deployment", "name": "api"}],
                    }
                },
                {
                    "metadata": {
                        "name": "api-rs-a",
                        "ownerReferences": [{"kind": "Deployment", "name": "api"}],
                    }
                },
                {
                    "metadata": {
                        "name": "ignored-sts-rs",
                        "ownerReferences": [{"kind": "StatefulSet", "name": "db"}],
                    }
                },
                {"metadata": {"name": "orphan"}},
            ]
        }
    )

    assert grouped == {"api": ["api-rs-a", "api-rs-b"]}


def test_matching_helm_release_names_filters_by_match_regex():
    releases = [
        {"name": "api-main"},
        {"name": "worker"},
        {"name": ""},
        {},
    ]

    assert matching_helm_release_names(releases, re.compile(r"main|worker")) == ["api-main", "worker"]


def test_workload_source_items_keeps_kind_order_and_payloads():
    deployments = {"items": [{"metadata": {"name": "api"}}]}
    statefulsets = {"items": [{"metadata": {"name": "db"}}]}
    daemonsets = {"items": [{"metadata": {"name": "agent"}}]}

    assert workload_source_items(deployments, statefulsets, daemonsets) == [
        ("Deployment", deployments),
        ("StatefulSet", statefulsets),
        ("DaemonSet", daemonsets),
    ]


def test_workload_collection_helpers_keep_kind_order():
    sources = workload_source_items(
        {"items": [{"metadata": {"name": "api-main"}}, {"metadata": {"name": "worker"}}]},
        {"items": [{"metadata": {"name": "db-main"}}]},
        {"items": [{"metadata": {"name": "node-agent"}}]},
    )

    assert [
        (kind, item["metadata"]["name"]) for kind, item in matching_workload_items(sources, re.compile(r"main"))
    ] == [
        ("Deployment", "api-main"),
        ("StatefulSet", "db-main"),
    ]
    assert [(kind, item["metadata"]["name"]) for kind, item in all_workload_items(sources)] == [
        ("Deployment", "api-main"),
        ("Deployment", "worker"),
        ("StatefulSet", "db-main"),
        ("DaemonSet", "node-agent"),
    ]


def test_select_workloads_returns_matches_without_message():
    selected, message = select_workloads(
        deployments={"items": [{"metadata": {"name": "api-main"}}, {"metadata": {"name": "worker"}}]},
        statefulsets={"items": [{"metadata": {"name": "db-main"}}]},
        daemonsets={"items": []},
        match_re=re.compile(r"main"),
        match_regex="main",
        namespace="payments",
    )

    assert [(kind, item["metadata"]["name"]) for kind, item in selected] == [
        ("Deployment", "api-main"),
        ("StatefulSet", "db-main"),
    ]
    assert message == ""


def test_select_workloads_falls_back_to_all_workloads_with_message():
    selected, message = select_workloads(
        deployments={"items": [{"metadata": {"name": "api"}}]},
        statefulsets={"items": []},
        daemonsets={"items": [{"metadata": {"name": "node-agent"}}]},
        match_re=re.compile(r"does-not-match"),
        match_regex="does-not-match",
        namespace="payments",
    )

    assert [(kind, item["metadata"]["name"]) for kind, item in selected] == [
        ("Deployment", "api"),
        ("DaemonSet", "node-agent"),
    ]
    assert "inspecting all 2 workloads instead" in message


def test_select_workloads_reports_empty_namespace():
    selected, message = select_workloads(
        deployments={"items": []},
        statefulsets={"items": []},
        daemonsets={"items": []},
        match_re=re.compile(r"api"),
        match_regex="api",
        namespace="payments",
    )

    assert selected == []
    assert "namespace has no Deployment/StatefulSet/DaemonSet workloads" in message
