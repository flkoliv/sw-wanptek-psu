from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("wanptek-controller")
except PackageNotFoundError:
    __version__ = "dev"
