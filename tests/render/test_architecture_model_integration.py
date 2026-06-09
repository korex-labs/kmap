import json
from argparse import Namespace

from kmap.model import architecture_model_from_reports
from kmap.render.likec4.model import render_likec4_model
from kmap.render.structurizr.model_content import render_structurizr_model


def test_architecture_model_from_minimal_report(tmp_path):
    report = {
        "workloads": [
            {
                "service_id": "svc.demo.api",
                "cluster": "demo-cluster",
                "namespace": "demo-api-prod-1234",
                "project": "api",
                "kind": "Deployment",
                "service_name": "prod-demo-api",
                "app_service": "demo-api",
                "containers": [{"name": "app", "kind": "container", "image": "example/api:1"}],
                "runtime": {
                    "replicas_desired": 1,
                    "replicas_ready": 1,
                    "replicas_available": 1,
                    "running_pods": 1,
                },
                "autoscaling": {
                    "scaling_enabled": "true",
                    "scaling_type": "keda",
                    "min_replicas": "2",
                    "max_replicas": "20",
                    "scale_formula": "ceil(RPS / 150)",
                },
                "selector": {"app": "demo-api"},
                "entrypoints": [],
                "traffic_routes": [
                    {
                        "direction": "inbound",
                        "source": {"type": "External", "name": "api.example.com"},
                        "hops": [
                            {"type": "Ingress", "name": "api-ing", "host": "api.example.com", "path": "/"},
                            {"type": "Service", "name": "api-svc", "port": 80},
                            {"type": "Workload", "name": "prod-demo-api"},
                        ],
                        "target": {"type": "Container", "names": ["app"]},
                    }
                ],
                "dependency_candidates": [],
            }
        ]
    }
    (tmp_path / "demo.report.json").write_text(json.dumps(report), encoding="utf-8")

    architecture = architecture_model_from_reports(
        Namespace(
            reports_dir=str(tmp_path),
            dependencies_file="",
            config="",
            org="web",
            product="demo",
            project="",
            env="prod",
            product_metadata={"owner_team": "Team"},
            project_metadata={},
            config_namespace_projects={},
            system_naming_config={},
            dependency_hotspots_config={},
        )
    )

    assert architecture["product"]["name"] == "demo"
    assert architecture["projects"][0]["name"] == "api"
    assert architecture["systems"][0]["title"] == "API"
    assert architecture["traffic_flows"][0]["namespace"] == "demo-api-prod-1234"
    assert architecture["containers"][0]["runtime"] == {
        "container_kinds": ["container"],
        "container_ports": [],
        "images": ["example/api:1"],
    }
    assert architecture["deployments"][0]["clusters"][0]["namespaces"][0]["instances"][0]["runtime"] == {
        "ingresses": [],
        "replicas_available": [1],
        "replicas_desired": [1],
        "replicas_ready": [1],
        "running_pods": [1],
        "scale_formula": ["ceil(RPS / 150)"],
        "scaling_enabled": ["true"],
        "scaling_type": ["keda"],
        "service_ports": [],
        "services": [],
        "max_replicas": ["20"],
        "min_replicas": ["2"],
        "workload_kinds": ["Deployment"],
    }


def test_architecture_model_preserves_mapped_external_endpoints(tmp_path):
    report = {
        "workloads": [
            {
                "service_id": "svc.demo.api",
                "cluster": "demo-cluster",
                "namespace": "demo-api-prod-1234",
                "project": "api",
                "kind": "Deployment",
                "service_name": "prod-demo-api",
                "app_service": "demo-api",
                "containers": [{"name": "app", "kind": "container", "image": "example/api:1"}],
                "runtime": {},
                "selector": {},
                "entrypoints": [],
                "dependency_candidates": [],
            }
        ]
    }
    (tmp_path / "demo.report.json").write_text(json.dumps(report), encoding="utf-8")
    dependencies_file = tmp_path / "dependencies.list"
    dependencies_file.write_text(
        "svc.demo.api | KAFKA_URL | kafka-1.example.com:9092 | EXTERNAL |  | Env | external | KAFKA_URL=kafka\n",
        encoding="utf-8",
    )
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
external_mappings:
  - name: Kafka
    match:
      - kafka-1.example.com
""",
        encoding="utf-8",
    )

    architecture = architecture_model_from_reports(
        Namespace(
            reports_dir=str(tmp_path),
            dependencies_file=str(dependencies_file),
            config=str(config_file),
            org="web",
            product="demo",
            project="",
            env="prod",
            product_metadata={},
            project_metadata={},
            config_namespace_projects={},
            system_naming_config={},
            dependency_hotspots_config={},
        )
    )

    kafka_system = next(system for system in architecture["systems"] if system["title"] == "Kafka")
    endpoint_container = next(
        container for container in architecture["containers"] if container.get("system_id") == kafka_system["id"]
    )
    relationship = next(rel for rel in architecture["relationships"] if rel["target_id"] == endpoint_container["id"])

    assert endpoint_container["title"] == "kafka-1.example.com"
    assert endpoint_container["technology"] == "External dependency"
    assert endpoint_container["description"] == "External dependency\\nEndpoint: kafka-1.example.com"
    assert relationship["title"] == "kafka-1.example.com"


def test_architecture_model_uses_external_source_var_as_stable_identity(tmp_path):
    def build_architecture(base_dir, endpoint):
        base_dir.mkdir()
        report = {
            "workloads": [
                {
                    "service_id": "svc.demo.partner",
                    "cluster": "demo-cluster",
                    "namespace": "demo-partner-prod-1234",
                    "project": "partner",
                    "kind": "Deployment",
                    "service_name": "prod-demo-partner",
                    "app_service": "demo-partner",
                    "containers": [{"name": "app", "kind": "container", "image": "example/partner:1"}],
                    "runtime": {},
                    "selector": {},
                    "entrypoints": [],
                    "dependency_candidates": [],
                }
            ]
        }
        (base_dir / "demo.report.json").write_text(json.dumps(report), encoding="utf-8")
        config_file = base_dir / "config.yaml"
        config_file.write_text(
            """
external_mappings:
  - name: Website
    element_type: Website
    match:
      - partner-auth.example.com
""",
            encoding="utf-8",
        )
        dependencies_file = base_dir / "dependencies.json"
        dependencies_file.write_text(
            json.dumps(
                [
                    {
                        "source_service": "svc.demo.partner",
                        "source_var": "PARTNER_AUTH_ADDR",
                        "dependency_key": endpoint,
                        "dependency_type": "EXTERNAL",
                        "target_service": "",
                        "source_origin": "Env",
                        "match_type": "external",
                        "evidence": f"PARTNER_AUTH_ADDR=https://{endpoint}",
                    }
                ]
            ),
            encoding="utf-8",
        )
        return architecture_model_from_reports(
            Namespace(
                reports_dir=str(base_dir),
                dependencies_file=str(dependencies_file),
                config=str(config_file),
                org="web",
                product="demo",
                project="",
                env="prod",
                product_metadata={},
                project_metadata={},
                config_namespace_projects={},
                system_naming_config={},
                dependency_hotspots_config={},
            )
        )

    prod_architecture = build_architecture(tmp_path / "prod", "partner-auth.example.com")
    stage_architecture = build_architecture(tmp_path / "stage", "stage.kube.example.internal")

    prod_external = next(system for system in prod_architecture["systems"] if system["kind"] == "external")
    stage_external = next(system for system in stage_architecture["systems"] if system["kind"] == "external")
    relationship = prod_architecture["relationships"][0]

    assert prod_external["id"] == "ext.partner_auth_addr"
    assert stage_external["id"] == "ext.partner_auth_addr"
    assert prod_external["title"] == "Partner Auth Address"
    assert prod_external["element_type"] == "External_API"
    assert prod_external["metadata"] == {
        "endpoint": ["partner-auth.example.com"],
        "source_origin": ["env"],
        "source_var": ["PARTNER_AUTH_ADDR"],
    }
    assert relationship["title"] == "partner-auth.example.com"
    likec4_model = render_likec4_model(prod_architecture)
    structurizr_model = render_structurizr_model(prod_architecture)
    assert 'ext_partner_auth_addr = External_API "Partner Auth Address" {' in likec4_model
    assert 'source_var "PARTNER_AUTH_ADDR"' in likec4_model
    assert 'endpoint "partner-auth.example.com"' in likec4_model
    assert 'ext_web_demo_external_PARTNER_AUTH_ADDR = softwareSystem "Partner Auth Address"' in structurizr_model
    assert '"source_var" "PARTNER_AUTH_ADDR"' in structurizr_model
    assert '"endpoint" "partner-auth.example.com"' in structurizr_model


def test_architecture_model_keeps_explicit_external_mapping_identity(tmp_path):
    report = {
        "workloads": [
            {
                "service_id": "svc.demo.partner",
                "cluster": "demo-cluster",
                "namespace": "demo-partner-prod-1234",
                "project": "partner",
                "kind": "Deployment",
                "service_name": "prod-demo-partner",
                "app_service": "demo-partner",
                "containers": [{"name": "app", "kind": "container", "image": "example/partner:1"}],
                "runtime": {},
                "selector": {},
                "entrypoints": [],
                "dependency_candidates": [],
            }
        ]
    }
    (tmp_path / "demo.report.json").write_text(json.dumps(report), encoding="utf-8")
    dependencies_file = tmp_path / "dependencies.json"
    dependencies_file.write_text(
        json.dumps(
            [
                {
                    "source_service": "svc.demo.partner",
                    "source_var": "PARTNER_AUTH_ADDR",
                    "dependency_key": "partner-auth.example.com",
                    "dependency_type": "EXTERNAL",
                    "target_service": "",
                    "source_origin": "Env",
                    "match_type": "external",
                    "evidence": "PARTNER_AUTH_ADDR=https://partner-auth.example.com",
                }
            ]
        ),
        encoding="utf-8",
    )
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
external_mappings:
  - name: Partner Auth
    element_type: External_API
    match:
      - partner-auth.example.com
""",
        encoding="utf-8",
    )

    architecture = architecture_model_from_reports(
        Namespace(
            reports_dir=str(tmp_path),
            dependencies_file=str(dependencies_file),
            config=str(config_file),
            org="web",
            product="demo",
            project="",
            env="prod",
            product_metadata={},
            project_metadata={},
            config_namespace_projects={},
            system_naming_config={},
            dependency_hotspots_config={},
        )
    )

    external = next(system for system in architecture["systems"] if system["kind"] == "external")

    assert external["id"] == "ext.partner_auth"
    assert external["title"] == "Partner Auth"


def test_architecture_model_preserves_database_metadata_on_relationship_and_endpoint(tmp_path):
    report = {
        "workloads": [
            {
                "service_id": "svc.demo.api",
                "cluster": "demo-cluster",
                "namespace": "demo-api-prod-1234",
                "project": "api",
                "kind": "Deployment",
                "service_name": "prod-demo-api",
                "app_service": "demo-api",
                "containers": [{"name": "app", "kind": "container", "image": "example/api:1"}],
                "runtime": {},
                "selector": {},
                "entrypoints": [],
                "dependency_candidates": [],
            }
        ]
    }
    (tmp_path / "demo.report.json").write_text(json.dumps(report), encoding="utf-8")
    dependencies_file = tmp_path / "dependencies.json"
    dependencies_file.write_text(
        json.dumps(
            [
                {
                    "source_service": "svc.demo.api",
                    "source_var": "MYSQL_DSN",
                    "dependency_key": "mysql.example.com:3306",
                    "dependency_type": "EXTERNAL",
                    "target_service": "",
                    "source_origin": "Env",
                    "match_type": "external",
                    "evidence": "<redacted>",
                    "metadata": {
                        "database": {
                            "engine": "mysql",
                            "names": ["wallet"],
                            "source_vars": ["MYSQL_DSN"],
                            "sources": ["dsn_path"],
                        }
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
external_mappings:
  - name: Database (MySQL)
    element_type: MySQL_DB
    match:
      - mysql.example.com
""",
        encoding="utf-8",
    )

    architecture = architecture_model_from_reports(
        Namespace(
            reports_dir=str(tmp_path),
            dependencies_file=str(dependencies_file),
            config=str(config_file),
            org="web",
            product="demo",
            project="",
            env="prod",
            product_metadata={},
            project_metadata={},
            config_namespace_projects={},
            system_naming_config={},
            dependency_hotspots_config={},
        )
    )

    relationship = architecture["relationships"][0]
    endpoint_container = next(container for container in architecture["containers"] if container["kind"] == "external")

    assert relationship["metadata"]["database"]["names"] == ["wallet"]
    assert endpoint_container["metadata"]["database"]["names"] == ["wallet"]
