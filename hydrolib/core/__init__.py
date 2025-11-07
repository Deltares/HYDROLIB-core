from importlib.metadata import version, PackageNotFoundError


try:
    __version__ = version("Wadden-Sea-backend")
except PackageNotFoundError:
    __version__ = "unknown"

