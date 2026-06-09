from kmap.config import normalize_system_naming_config
from kmap.model.workloads import (
    configured_system_title_from_project,
    process_workload,
    resolved_container_title,
    resolved_project_name,
    resolved_system_name_and_source,
)


def _naming(project="", env="prod"):
    return type("Naming", (), {"project": project, "env": env})()


def test_process_workload_creates_project_system_container_and_instance():
    deployment = {"env": "prod", "clusters": {}}
    projects_by_id = {}
    systems_by_id = {}
    containers_by_id = {}
    workload_project_ids = {}
    workload_primary_container_ids = {}
    workload_primary_instance_ids = {}
    workloads_by_service_id = {}

    process_workload(
        svc={
            "service_id": "svc-api",
            "service_name": "prod-demo-api",
            "app_service": "demo-api",
            "namespace": "demo-prod",
            "project": "demo",
            "cluster": "cluster-a",
            "containers": [{"name": "app", "kind": "container"}],
            "discovery": {"context": "prod-context"},
        },
        naming=_naming(),
        product_name="product",
        product_id="prod.product",
        product_metadata={"owner_team": "Platform"},
        project_metadata={"demo": {"title": "Demo", "domain_team": "Payments"}},
        config_namespace_projects={},
        system_naming_config=normalize_system_naming_config({}),
        env="prod",
        deployment=deployment,
        projects_by_id=projects_by_id,
        systems_by_id=systems_by_id,
        containers_by_id=containers_by_id,
        workload_project_ids=workload_project_ids,
        workload_primary_container_ids=workload_primary_container_ids,
        workload_primary_instance_ids=workload_primary_instance_ids,
        workloads_by_service_id=workloads_by_service_id,
    )

    assert workload_project_ids == {"svc-api": "prj.product.demo"}
    assert workloads_by_service_id["svc-api"]["service_name"] == "prod-demo-api"
    assert projects_by_id["prj.product.demo"]["discovery"]["namespace_metadata"]["demo-prod"]["context"] == (
        "prod-context"
    )
    system = systems_by_id["sys.product.demo.demo_api"]
    assert system["title"] == "Demo API"
    container_id = workload_primary_container_ids["svc-api"]
    assert containers_by_id[container_id]["discovery"] == {
        "clusters": ["cluster-a"],
        "namespaces": ["demo-prod"],
        "workloads": ["prod-demo-api"],
    }
    assert workload_primary_instance_ids["svc-api"].startswith("inst.prod.demo.demo_api.app.")
    cluster = deployment["clusters"]["cluster.prod.cluster_a"]
    assert cluster["namespaces"]["ns.demo_prod"]["instances"][0]["container_id"] == container_id


def test_process_workload_skips_unmodeled_workload():
    projects_by_id = {}

    process_workload(
        svc={"service_id": "svc", "service_name": "cert-operator", "entrypoints": [], "dependency_candidates": []},
        naming=_naming(),
        product_name="product",
        product_id="prod.product",
        product_metadata={},
        project_metadata={},
        config_namespace_projects={},
        system_naming_config=normalize_system_naming_config({}),
        env="prod",
        deployment={"env": "prod", "clusters": {}},
        projects_by_id=projects_by_id,
        systems_by_id={},
        containers_by_id={},
        workload_project_ids={},
        workload_primary_container_ids={},
        workload_primary_instance_ids={},
        workloads_by_service_id={},
    )

    assert projects_by_id == {}


def test_process_workload_without_service_id_does_not_record_primary_indexes():
    deployment = {"env": "prod", "clusters": {}}
    workload_project_ids = {}
    workload_primary_container_ids = {}
    workload_primary_instance_ids = {}
    workloads_by_service_id = {}

    process_workload(
        svc={
            "service_name": "prod-demo-api",
            "app_service": "demo-api",
            "namespace": "demo-prod",
            "project": "demo",
            "cluster": "cluster-a",
            "containers": [{"name": "app", "kind": "container"}],
        },
        naming=_naming(),
        product_name="product",
        product_id="prod.product",
        product_metadata={},
        project_metadata={},
        config_namespace_projects={},
        system_naming_config=normalize_system_naming_config({}),
        env="prod",
        deployment=deployment,
        projects_by_id={},
        systems_by_id={},
        containers_by_id={},
        workload_project_ids=workload_project_ids,
        workload_primary_container_ids=workload_primary_container_ids,
        workload_primary_instance_ids=workload_primary_instance_ids,
        workloads_by_service_id=workloads_by_service_id,
    )

    assert workload_project_ids == {}
    assert workload_primary_container_ids == {}
    assert workload_primary_instance_ids == {}
    assert workloads_by_service_id == {}
    assert deployment["clusters"]["cluster.prod.cluster_a"]["namespaces"]["ns.demo_prod"]["instances"]


def test_resolved_project_name_prefers_config_service_naming_and_namespace():
    assert (
        resolved_project_name(
            svc={"project": "service-project"},
            naming=_naming(project="naming-project"),
            product_name="product",
            namespace="payments-prod",
            config_namespace_projects={"payments-prod": "configured-project"},
        )
        == "configured-project"
    )
    assert (
        resolved_project_name(
            svc={"project": "service-project"},
            naming=_naming(project="naming-project"),
            product_name="product",
            namespace="payments-prod",
            config_namespace_projects={},
        )
        == "service-project"
    )
    assert (
        resolved_project_name(
            svc={},
            naming=_naming(project="naming-project"),
            product_name="product",
            namespace="payments-prod",
            config_namespace_projects={},
        )
        == "naming-project"
    )
    assert (
        resolved_project_name(
            svc={},
            naming=_naming(),
            product_name="product",
            namespace="payments-prod",
            config_namespace_projects={},
        )
        == "payments"
    )


def test_configured_system_title_from_project_uses_single_namespace_project_title():
    project = {"title": "Payments", "discovery": {"namespaces": ["payments-prod"]}}
    project_meta = {"title": "Payments API"}

    assert configured_system_title_from_project(project, project_meta) == "Payments API"
    assert configured_system_title_from_project(project, {"system_title": "Checkout API"}) == "Checkout API"
    assert configured_system_title_from_project({"title": "Payments"}, {"title": "Payments"}) == ""


def test_resolved_system_name_and_source_prefers_app_service_and_marks_fallback():
    assert resolved_system_name_and_source(
        svc={"app_service": "checkout", "app_service_source": {"kind": "annotation"}},
        raw_service_name="checkout-api",
        product_name="product",
        project_name="payments",
        system_naming_config=normalize_system_naming_config({}),
    ) == ("checkout", {"kind": "annotation"})

    system_name, source = resolved_system_name_and_source(
        svc={},
        raw_service_name="product-payments-api",
        product_name="product",
        project_name="payments",
        system_naming_config=normalize_system_naming_config({}),
    )

    assert system_name == "payments-api"
    assert source["kind"] == "fallback"
    assert source["fallback_used"] is True


def test_resolved_container_title_collapses_matching_app_container_title():
    assert (
        resolved_container_title(
            raw_container_name="checkout-api",
            product_name="product",
            project_name="payments",
            product_metadata={},
            system_title="Checkout API",
            system_element_type="System",
            system_category="App",
        )
        == "App"
    )
    assert (
        resolved_container_title(
            raw_container_name="worker",
            product_name="product",
            project_name="payments",
            product_metadata={},
            system_title="Checkout API",
            system_element_type="System",
            system_category="App",
        )
        == "Worker"
    )
