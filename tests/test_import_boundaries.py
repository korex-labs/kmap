from pathlib import Path

from kmap import metadata_runtime
from kmap.command.config_recommend import common as config_recommend_common
from kmap.command.config_recommend import namespace_rules, product_rules
from kmap.command.inspect import namespace_context, namespace_runtime, namespace_workloads
from kmap.command.view import commands as view_commands
from kmap.command.view import flow as view_flow
from kmap.command.view import paths as view_paths
from kmap.command.view import validation as view_validation
from kmap.config import project_metadata, validation_external, validation_resources
from kmap.inspection import bucket_dedup as inspection_bucket_dedup
from kmap.inspection import bucket_detection as inspection_bucket_detection
from kmap.inspection import bucket_sanitization as inspection_bucket_sanitization
from kmap.inspection import buckets as inspection_buckets
from kmap.inspection import dependency_sanitization as inspection_dependency_sanitization
from kmap.inspection import runtime as inspection_runtime
from kmap.inspection import sanitization as inspection_sanitization
from kmap.inspection import sanitization_mocking as inspection_sanitization_mocking
from kmap.inspection import workloads as inspection_workloads
from kmap.inspection.dependencies import candidates as inspection_dependency_candidates
from kmap.inspection.dependencies import core as inspection_dependency_core
from kmap.inspection.dependencies import dedup as inspection_dependency_dedup
from kmap.inspection.dependencies import env as inspection_dependency_env
from kmap.inspection.dependencies import model as inspection_dependency_model
from kmap.inspection.dependencies import parsing as inspection_dependency_parsing
from kmap.inspection.dependencies import sources as inspection_dependency_sources
from kmap.inventory import (
    bucket_rows,
    cluster_inventory_rows,
    full_discovery_client,
    full_discovery_inventory,
    full_discovery_namespaces,
    full_discovery_persistence,
    html_filter,
    html_styles,
    live_namespace_resources,
    live_namespace_workloads,
    namespace_html,
    namespace_repository,
    namespace_rows,
    namespace_state,
    namespaces,
    repository_cache,
    repository_enrichment,
    repository_gitlab,
    repository_matching,
    repository_model,
)
from kmap.inventory.bucket_rows import artifacts as bucket_row_artifacts
from kmap.inventory.bucket_rows import model as bucket_row_model
from kmap.inventory.bucket_rows import reports as bucket_row_reports
from kmap.inventory.bucket_rows import signals as bucket_row_signals
from kmap.kubernetes import (
    data as kubernetes_data,
)
from kmap.kubernetes import (
    metadata,
    metadata_probes,
    metadata_resources,
    metadata_scheduling,
    metadata_security,
    metadata_values,
    network_ingress,
    network_services,
)
from kmap.logging import commands as logging_commands
from kmap.logging import output as logging_output
from kmap.logging import progress as logging_progress
from kmap.logging import runner as logging_runner
from kmap.model import (
    build_state,
    dependencies,
    deployments,
    relationship_rendering,
    relationship_stats,
    traffic_flows,
    workloads,
)
from kmap.model.dependencies import dependency_relationships, external, external_endpoints, state, targets
from kmap.model.workloads import context as workload_context
from kmap.model.workloads import deployment as workload_deployment
from kmap.model.workloads import entries as workload_entries
from kmap.model.workloads import processing as workload_processing
from kmap.model.workloads import processing_context, processing_state
from kmap.naming import display_dependencies, display_text
from kmap.progress import lifecycle as progress_lifecycle
from kmap.relations import files as relation_files
from kmap.render.likec4 import (
    deployment_context,
    deployment_routes,
    deployment_views,
    metadata_summaries,
    model_context,
    model_partitions,
    model_resources,
    readme_sections,
    readme_static_sections,
    readme_table_external,
    readme_table_indexes,
    readme_tables,
    system_views,
    views_shared,
)
from kmap.render.likec4 import (
    metadata_values as likec4_metadata_values,
)
from kmap.render.structurizr import element_metadata as structurizr_element_metadata


def test_split_modules_publish_stable_exports():
    modules = [
        bucket_row_artifacts,
        bucket_row_model,
        bucket_row_reports,
        bucket_rows,
        bucket_row_signals,
        cluster_inventory_rows,
        config_recommend_common,
        dependencies,
        dependency_relationships,
        deployment_context,
        deployments,
        deployment_routes,
        deployment_views,
        external,
        external_endpoints,
        full_discovery_client,
        full_discovery_inventory,
        full_discovery_namespaces,
        full_discovery_persistence,
        html_filter,
        html_styles,
        inspection_bucket_dedup,
        inspection_bucket_detection,
        inspection_bucket_sanitization,
        inspection_dependency_candidates,
        inspection_dependency_core,
        inspection_dependency_dedup,
        inspection_dependency_env,
        inspection_dependency_model,
        inspection_dependency_parsing,
        inspection_dependency_sanitization,
        inspection_dependency_sources,
        inspection_buckets,
        inspection_runtime,
        inspection_sanitization,
        inspection_sanitization_mocking,
        inspection_workloads,
        kubernetes_data,
        network_ingress,
        network_services,
        likec4_metadata_values,
        live_namespace_resources,
        live_namespace_workloads,
        logging_commands,
        logging_output,
        logging_progress,
        logging_runner,
        metadata,
        metadata_runtime,
        metadata_probes,
        metadata_resources,
        metadata_scheduling,
        metadata_security,
        metadata_values,
        metadata_summaries,
        build_state,
        model_partitions,
        model_context,
        model_resources,
        namespace_context,
        namespace_rules,
        namespace_runtime,
        namespace_workloads,
        namespace_html,
        namespace_repository,
        namespace_rows,
        namespace_state,
        project_metadata,
        progress_lifecycle,
        product_rules,
        readme_sections,
        readme_static_sections,
        readme_table_external,
        readme_table_indexes,
        readme_tables,
        relation_files,
        relationship_rendering,
        relationship_stats,
        repository_cache,
        repository_enrichment,
        repository_gitlab,
        repository_matching,
        repository_model,
        state,
        structurizr_element_metadata,
        system_views,
        targets,
        traffic_flows,
        validation_external,
        validation_resources,
        views_shared,
        view_commands,
        view_flow,
        view_paths,
        view_validation,
        workload_context,
        workload_deployment,
        workload_entries,
        processing_context,
        processing_state,
        workload_processing,
        workloads,
        display_dependencies,
        display_text,
    ]

    for module in modules:
        assert module.__all__
        for name in module.__all__:
            assert getattr(module, name)


def test_inventory_namespaces_facade_keeps_row_and_html_api():
    assert namespaces.InventoryRow is namespace_rows.InventoryRow
    assert namespaces.collect_inventory_rows is namespace_rows.collect_inventory_rows
    assert namespaces.render_inventory_html is namespace_html.render_inventory_html


def test_root_namespace_keeps_domain_packages_instead_of_loose_helper_files():
    root = metadata_runtime.__file__
    assert root
    assert root.endswith("metadata_runtime/__init__.py")


def test_root_package_underscore_files_stay_allowlisted():
    root = metadata_runtime.__file__
    assert root
    package_root = Path(root).resolve().parents[1]
    allowed = {
        "__init__.py",
        "rendering_resources.py",
        "tool_config.py",
        "tool_config_validation.py",
    }

    actual = {path.name for path in package_root.glob("*_*.py")}

    assert actual <= allowed


def test_top_level_command_compatibility_modules_are_not_reintroduced():
    root = metadata_runtime.__file__
    assert root
    package_root = Path(root).resolve().parents[1]
    removed_facades = {"combine.py", "inspect.py", "pipeline.py"}

    assert removed_facades.isdisjoint({path.name for path in package_root.glob("*.py")})


def test_no_wildcard_compatibility_facades():
    root = metadata_runtime.__file__
    assert root
    package_root = Path(root).resolve().parents[1]
    offenders = []

    for source_file in package_root.rglob("*.py"):
        text = source_file.read_text(encoding="utf-8")
        if "import *" in text:
            offenders.append(str(source_file.relative_to(package_root)))

    assert offenders == []


def test_legacy_adapter_names_are_not_reintroduced():
    root = metadata_runtime.__file__
    assert root
    package_root = Path(root).resolve().parents[1]
    offenders = []

    for source_file in package_root.rglob("*.py"):
        text = source_file.read_text(encoding="utf-8")
        if "legacy_dependency_candidate" in text or "legacy_base_dependency_candidate" in text:
            offenders.append(str(source_file.relative_to(package_root)))

    assert offenders == []


def test_package_initializers_stay_facade_sized():
    root = metadata_runtime.__file__
    assert root
    package_root = Path(root).resolve().parents[1]
    allowed_large = {
        package_root / "logging" / "__init__.py",
    }
    offenders = []

    for init_file in package_root.rglob("__init__.py"):
        relative = init_file.relative_to(package_root)
        if init_file in allowed_large:
            continue
        lines = [
            line
            for line in init_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        definitions = [line for line in lines if line.startswith(("def ", "class ", "@dataclass"))]
        if len(definitions) > 2 or (definitions and len(lines) > 80) or len(lines) > 140:
            offenders.append(str(relative))

    assert offenders == []


def test_source_modules_stay_below_review_size_threshold():
    root = metadata_runtime.__file__
    assert root
    package_root = Path(root).resolve().parents[1]
    max_lines = 320
    allowlisted = {
        "model/workloads/processing.py",
    }
    offenders = []

    for source_file in package_root.rglob("*.py"):
        relative = source_file.relative_to(package_root)
        if source_file.name == "__init__.py" or str(relative) in allowlisted:
            continue
        line_count = len(source_file.read_text(encoding="utf-8").splitlines())
        if line_count > max_lines:
            offenders.append(f"{relative}: {line_count}")

    assert offenders == []


def test_domain_layers_do_not_import_command_layer():
    root = metadata_runtime.__file__
    assert root
    package_root = Path(root).resolve().parents[1]
    offenders = []

    for layer in ("inspection", "inventory", "model", "render"):
        for source_file in (package_root / layer).rglob("*.py"):
            text = source_file.read_text(encoding="utf-8")
            if "kmap.command" in text or "from ..command" in text or "from ...command" in text:
                offenders.append(str(source_file.relative_to(package_root)))

    assert offenders == []


def test_shared_inspection_package_stays_inventory_usable():
    assert inspection_buckets.workload_bucket_candidates
    assert inspection_runtime.collect_runtime_env_maps
    assert inspection_workloads.workload_container_context


def test_public_export_names_resolve_to_real_objects():
    root = metadata_runtime.__file__
    assert root
    package_root = Path(root).resolve().parents[1]
    offenders = []

    for source_file in package_root.rglob("*.py"):
        relative = source_file.relative_to(package_root)
        module_parts = relative.parent.parts if relative.name == "__init__.py" else relative.with_suffix("").parts
        module_name = "kmap" if not module_parts else "kmap." + ".".join(module_parts)
        module = __import__(module_name, fromlist=["__all__"])
        public_names = getattr(module, "__all__", None)
        if public_names is None:
            continue
        missing = [name for name in public_names if not hasattr(module, name)]
        duplicates = sorted({name for name in public_names if public_names.count(name) > 1})
        if missing or duplicates:
            offenders.append(f"{relative}: missing={missing}, duplicates={duplicates}")

    assert offenders == []


def test_domain_packages_have_corresponding_test_areas():
    root = metadata_runtime.__file__
    assert root
    package_root = Path(root).resolve().parents[1]
    tests_root = package_root.parent / "tests"
    expected = {
        "command/inspect": tests_root / "command" / "inspect",
        "command/view": tests_root / "command" / "view",
        "config": tests_root / "config",
        "inventory": tests_root / "inventory",
        "kubernetes": tests_root,
        "model": tests_root / "model",
        "render/likec4": tests_root / "render" / "likec4",
        "render/structurizr": tests_root / "render" / "structurizr",
    }
    offenders = []

    for package, tests_path in expected.items():
        source_files = [path for path in (package_root / package).rglob("*.py") if path.name != "__init__.py"]
        test_files = list(tests_path.rglob("test_*.py")) if tests_path.exists() else []
        if source_files and not test_files:
            offenders.append(package)

    assert offenders == []
