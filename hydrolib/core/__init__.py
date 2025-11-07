from importlib.metadata import version, PackageNotFoundError


try:
    __version__ = version("hydrolib-core")
except PackageNotFoundError:
    __version__ = "unknown"

