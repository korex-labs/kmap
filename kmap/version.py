"""Package version helpers."""

from importlib.metadata import PackageNotFoundError, version

SOURCE_VERSION = "1.1.1"


def package_version() -> str:
    try:
        return version("kmap")
    except PackageNotFoundError:
        return SOURCE_VERSION


__version__ = package_version()

__all__ = ["SOURCE_VERSION", "__version__", "package_version"]
