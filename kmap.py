#!/usr/bin/env python3
"""Compatibility entrypoint for kmap.

Keep this file thin so existing commands such as
`python kmap.py run-all ...` remain stable while the implementation
lives in the `kmap` package.
"""

from kmap.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
