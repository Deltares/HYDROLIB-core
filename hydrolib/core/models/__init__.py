"""
Implementations of the [`FileModel`][hydrolib.core.basemodel.FileModel] for
all known extensions.

TODO: For now I (Guus) places all models that where previously in models.py in this __init__.py
"""

from typing import Callable, List, Optional

from hydrolib.core.basemodel import BaseModel, FileModel
from hydrolib.core.io.base import DummmyParser, DummySerializer


class Edge(BaseModel):
    a: int = 0
    b: int = 1


class Network(FileModel):
    """Network model representation."""

    # TODO: Why make all these classmethods? And not staticmethods or just attributes?
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
        return DummmyParser.parse
