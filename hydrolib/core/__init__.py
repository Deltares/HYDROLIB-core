"""HYDROLIB-core package for D-HYDRO model file wrappers."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("hydrolib-core")
except PackageNotFoundError:
    # Package is not installed
    __version__ = "unknown"
