"""
Implementations of the [`FileModel`][hydrolib.core.basemodel.FileModel] for
all known extensions.
"""

from typing import Callable, List, Optional, Sequence, Union

import meshkernel as mk
from pydantic import Field, validator

from hydrolib.core import __version__
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
from hydrolib.core.io.net.models import Link1d2d, Mesh1d, Mesh2d
from hydrolib.core.io.dimr.parser import DIMRParser
from hydrolib.core.io.dimr.serializer import DIMRSerializer
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

    # TODO: This should be fixed as part of #37
    # meshkernel: mk.MeshKernel = Field(default_factory=mk.MeshKernel)

    # _mesh1d: Optional[Mesh1d] = None
    # _mesh2d: Optional[Mesh2d] = None
    # _link1d2d: Optional[Link1d2d] = None

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    #     if self._mesh1d is None:
    #         self._mesh1d = Mesh1d(meshkernel=self.meshkernel)
    #     if self._mesh2d is None:
    #         self._mesh2d = Mesh2d(meshkernel=self.meshkernel)
    #     if self._link1d2d is None:
    #         self._link1d2d = Link1d2d(meshkernel=self.meshkernel)

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

    documentation: Documentation = Documentation()
    control: Control = Control()
    component: List[Union[RRComponent, FMComponent, Component]] = []
    coupler: Optional[List[Coupler]] = []
    waitFile: Optional[str]
    global_settings: Optional[GlobalSettings]

    @validator("component", "coupler", pre=True)
    def validate_component(cls, v):
        return to_list(v)

    def dict(self, *args, **kwargs):
        """Converts this object recursively to a dictionary.

        Returns:
            dict: The created dictionary for this object.
        """
        return self._to_serializable_dict(self)

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
        return DIMRSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return DIMRParser.parse

    def _to_serializable_dict(self, obj) -> dict:
        if not hasattr(obj, "__dict__"):
            return obj

        result = {}

        for key, val in obj.__dict__.items():
            if (
                key.startswith("_")
                or key == "filepath"
                or isinstance(val, FileModel)
                or val is None
            ):
                continue

            element = []
            if isinstance(val, list):
                for item in val:
                    element.append(self._to_serializable_dict(item))
            else:
                element = self._to_serializable_dict(val)
            result[key] = element

        return result


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
