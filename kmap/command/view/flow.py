"""Viewer command orchestration helpers."""

import argparse
from typing import Callable

StartViewers = Callable[[argparse.Namespace, str], tuple[int, bool, bool]]
StopViewers = Callable[[argparse.Namespace, str], int]
RequireOutputs = Callable[[argparse.Namespace, str], None]
PrintUrls = Callable[..., None]
ValidateArgs = Callable[[argparse.Namespace], str]


def run_view_product(
    args: argparse.Namespace,
    *,
    validate_args: ValidateArgs,
    stop_viewers: StopViewers,
    require_outputs: RequireOutputs,
    start_viewers: StartViewers,
    print_urls: PrintUrls,
) -> int:
    product = validate_args(args)

    if args.stop:
        return stop_viewers(args, product)

    require_outputs(args, product)

    rc, likec4_started, structurizr_started = start_viewers(args, product)
    if rc != 0:
        if likec4_started:
            print_urls(args, likec4_started=True, structurizr_started=False)
        return rc

    print_urls(args, likec4_started=likec4_started, structurizr_started=structurizr_started)
    return 0


__all__ = ["PrintUrls", "RequireOutputs", "StartViewers", "StopViewers", "ValidateArgs", "run_view_product"]
