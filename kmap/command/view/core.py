"""Start local viewers for generated kmap output."""

import argparse

from ...logging import eprint
from . import docker as docker_helpers
from .commands import likec4_run_command, structurizr_command_args, structurizr_run_command
from .flow import run_view_product
from .paths import (
    MAX_TCP_PORT,
    SCHEMAS_ROOT,
    container_name,
    likec4_output_path,
    require_file,
    structurizr_common_workspace_path,
    structurizr_workspace_path,
    validate_port,
)
from .validation import validate_view_args as _validate_view_args

time = docker_helpers.time
docker_container_exists = docker_helpers.docker_container_exists
docker_container_running = docker_helpers.docker_container_running
docker_container_using_port = docker_helpers.docker_container_using_port
docker_rm = docker_helpers.docker_rm
docker_run = docker_helpers.docker_run
ensure_started = docker_helpers.ensure_started
eprint_logs_hint = docker_helpers.eprint_logs_hint
prepare_viewer_container = docker_helpers.prepare_viewer_container


def eprint_port_conflict_hint(docker_bin: str, kind: str, port: str) -> None:
    fallback_port = str(min(int(port) + 1, MAX_TCP_PORT))
    owner = docker_helpers.docker_container_using_port(docker_bin, port)
    eprint(
        f"[kmap] {kind} port {port} is already allocated. `--restart` only recreates this product's viewer containers."
    )
    if owner:
        eprint(f"[kmap] {owner} is currently using port {port}")
    eprint(f"[kmap] stop the viewer using that port or choose another port, e.g. --{kind.lower()}-port {fallback_port}")


def start_likec4(args: argparse.Namespace, product: str) -> int:
    name = container_name("likec4", product)
    rc = docker_helpers.prepare_viewer_container(args.docker, name, restart=args.restart, kind="LikeC4")
    if rc is not None:
        return rc

    result = docker_helpers.docker_run(likec4_run_command(args, product, name))
    if result.returncode != 0:
        eprint(result.stderr.strip() or f"[kmap] failed to start LikeC4 container: {name}")
        if "port is already allocated" in result.stderr.lower():
            eprint_port_conflict_hint(args.docker, "LikeC4", args.likec4_port)
        docker_helpers.eprint_logs_hint(name)
        return result.returncode
    return docker_helpers.ensure_started(args.docker, name)


def start_structurizr(args: argparse.Namespace, product: str) -> int:
    name = container_name("structurizr", product)
    rc = docker_helpers.prepare_viewer_container(args.docker, name, restart=args.restart, kind="Structurizr")
    if rc is not None:
        return rc

    result = docker_helpers.docker_run(structurizr_run_command(args, product, name))
    if result.returncode != 0:
        eprint(result.stderr.strip() or f"[kmap] failed to start Structurizr container: {name}")
        if "port is already allocated" in result.stderr.lower():
            eprint_port_conflict_hint(args.docker, "Structurizr", args.structurizr_port)
        docker_helpers.eprint_logs_hint(name)
        return result.returncode
    return docker_helpers.ensure_started(args.docker, name)


def stop_viewers(args: argparse.Namespace, product: str) -> int:
    rc = 0
    if not args.no_likec4:
        rc = docker_helpers.docker_rm(args.docker, container_name("likec4", product)) or rc
    if not args.no_structurizr:
        rc = docker_helpers.docker_rm(args.docker, container_name("structurizr", product)) or rc
    if rc == 0:
        eprint(f"[kmap] stopped viewers for {product}")
    return rc


def start_enabled_viewers(args: argparse.Namespace, product: str) -> tuple[int, bool, bool]:
    likec4_started = False
    structurizr_started = False

    if not args.no_likec4:
        rc = start_likec4(args, product)
        if rc != 0:
            return rc, likec4_started, structurizr_started
        likec4_started = True
    if not args.no_structurizr:
        rc = start_structurizr(args, product)
        if rc != 0:
            return rc, likec4_started, structurizr_started
        structurizr_started = True
    return 0, likec4_started, structurizr_started


def view_product(args: argparse.Namespace) -> int:
    return run_view_product(
        args,
        validate_args=validate_view_args,
        stop_viewers=stop_viewers,
        require_outputs=require_view_outputs,
        start_viewers=start_enabled_viewers,
        print_urls=print_viewer_urls,
    )


def validate_view_args(args: argparse.Namespace) -> str:
    return _validate_view_args(args, validate_port=validate_port)


def require_view_outputs(args: argparse.Namespace, product: str) -> None:
    if not args.no_likec4:
        require_file(
            likec4_output_path(product),
            "Run: python kmap.py run-all --config <config> --render likec4",
        )
    if not args.no_structurizr:
        require_file(
            structurizr_workspace_path(product),
            "Run: python kmap.py run-all --config <config> --render structurizr",
        )
        require_file(
            structurizr_common_workspace_path(),
            "Structurizr common workspace is required because generated workspaces extend ../common/workspace.dsl",
        )


def print_viewer_urls(args: argparse.Namespace, *, likec4_started: bool, structurizr_started: bool) -> None:
    if likec4_started:
        print(f"LikeC4:      http://localhost:{args.likec4_port}")
    if structurizr_started:
        print(f"Structurizr: http://localhost:{args.structurizr_port}")


__all__ = [
    "MAX_TCP_PORT",
    "SCHEMAS_ROOT",
    "container_name",
    "docker_container_exists",
    "docker_container_running",
    "docker_container_using_port",
    "docker_rm",
    "docker_run",
    "ensure_started",
    "eprint_logs_hint",
    "eprint_port_conflict_hint",
    "likec4_output_path",
    "likec4_run_command",
    "prepare_viewer_container",
    "print_viewer_urls",
    "require_file",
    "require_view_outputs",
    "start_enabled_viewers",
    "start_likec4",
    "start_structurizr",
    "stop_viewers",
    "structurizr_command_args",
    "structurizr_common_workspace_path",
    "structurizr_run_command",
    "structurizr_workspace_path",
    "validate_port",
    "validate_view_args",
    "view_product",
]
