"""
Implementations of the [`FileModel`][hydrolib.core.basemodel.FileModel] for
all known extensions.
"""

from hydrolib.core.dimr_parser import DimrParser
from typing import Callable, List, Optional

from hydrolib.core.io.base import DummmyParser, DummySerializer

from .basemodel import BaseModel, FileModel


class Edge(BaseModel):
    """Test

    Attributes:
        a: This is some weird `int`.
    """

    a: int = 0
    b: int = 1


class Network(FileModel):
    """Network model representation."""

    n_vertices: int = 100
    edges: List[Edge] = [Edge()]

    @classmethod
    def _ext(cls) -> str:
        return ".nc"

    @classmethod
    def _filename(cls) -> str:
        return "network"

    @classmethod
    def _get_serializer(cls) -> Callable:
        return DummySerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return DummmyParser.parse


class FMModel(FileModel):
    """FM Model representation."""

    name: str = "Dummy"
    network: Optional[Network] = Network()

    @classmethod
    def _ext(cls) -> str:
        return ".mdu"

    @classmethod
    def _filename(cls) -> str:
        return "fm"

    @classmethod
    def _get_serializer(cls) -> Callable:
        return DummySerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return DummmyParser.parse


class DIMR(FileModel):
    """DIMR model representation."""

    model: Optional[FMModel]

    @classmethod
    def _ext(cls) -> str:
        return ".xml"

    @classmethod
    def _filename(cls) -> str:
        return "dimrconfig"

    @classmethod
    def _get_serializer(cls) -> Callable:
        return DummySerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return DimrParser.parse
