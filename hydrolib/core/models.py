"""
Implementations of the [`FileModel`][hydrolib.core.basemodel.FileModel] for
all known extensions.
"""

from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Union

from pydantic import validator

from hydrolib.core import __version__
from hydrolib.core.dimr_parser import DIMRParser
from hydrolib.core.io.base import DummmyParser, DummySerializer
from hydrolib.core.io.dimr.models import (
    Component,
    Control,
    Coupler,
    Documentation,
    FMComponent,
    GlobalSettings,
    RRComponent,
)
from hydrolib.core.io.polyfile.models import PolyObject
from hydrolib.core.io.polyfile.parser import read_polyfile
from hydrolib.core.io.polyfile.serializer import write_polyfile
from hydrolib.core.io.xyz.models import XYZPoint
from hydrolib.core.io.xyz.parser import XYZParser
from hydrolib.core.io.xyz.serializer import XYZSerializer
from hydrolib.core.utils import to_list

from .basemodel import BaseModel, FileModel


class Edge(BaseModel):
    """Test

    Attributes:
        a: This is some weird `int`.
    """

    a: int = 0
    b: int = 1


class XYZ(FileModel):
    """Sample or forcing file.

    Attributes:
        points: List of [`XYZPoint`][hydrolib.core.io.xyz.models.XYZPoint]
    """

    points: List[XYZPoint]

    def dict(self, *args, **kwargs):
        # speed up serializing by not converting these lowest models to dict
        return dict(points=self.points)

    @classmethod
    def _ext(cls) -> str:
        return ".xyz"

    @classmethod
    def _filename(cls) -> str:
        return "sample"

    @classmethod
    def _get_serializer(cls) -> Callable:
        return XYZSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return XYZParser.parse


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

    component: List[Union[RRComponent, FMComponent, Component]] = []
    documentation: Documentation = Documentation()
    coupler: Optional[List[Coupler]]
    control: Control = Control()
    waitFile: Optional[str]
    global_settings = Optional[GlobalSettings]

    @validator("component", "coupler", pre=True)
    def validate_component(cls, v):
        return to_list(v)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # After initilization, try to load all component models
        if self.filepath:
            for comp in self.component:
                fn = self.filepath.parent / comp.filepath
                try:
                    comp.model = comp.get_model()(filepath=fn)
                except NotImplementedError:
                    continue

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
        return DIMRParser.parse


class PolyFile(FileModel):
    """Poly-file (.pol/.pli/.pliz) representation."""

    has_z_values: bool = False
    objects: Sequence[PolyObject] = []

    @classmethod
    def _ext(cls) -> str:
        return ".pli"

    @classmethod
    def _filename(cls) -> str:
        return "objects"

    @classmethod
    def _get_serializer(cls) -> Callable:
        return write_polyfile

    @classmethod
    def _get_parser(cls) -> Callable:
        return read_polyfile
