from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("hydrolib-core")
except PackageNotFoundError:
    __version__ = "unknown"
