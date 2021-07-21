"""models.py defines all classes and functions related to representing pol/pli(z) files.
"""

from hydrolib.core.basemodel import BaseModel, FileModel
from hydrolib.core.io.base import DummmyParser, DummySerializer
from typing import Callable, List, Optional, Sequence


class Description(BaseModel):
    """Description of a single PolyObject.

    The Description will be prepended to a block. Each line will
    start with a '*'.
    """

    content: str


class Metadata(BaseModel):
    """Metadata of a single PolyObject."""

    name: str
    n_rows: int
    n_columns: int


class Point(BaseModel):
    """Point consisting of a x and y coordinate, an optional z coordinate and data."""

    x: float
    y: float
    z: Optional[float]
    data: Sequence[float]


class PolyObject(BaseModel):
    """PolyObject describing a single block in a poly file.

    The metadata should be consistent with the points:
    - The number of points should be equal to number of rows defined in the metadata
    - The data of each point should be equal to the number of columns defined in the
      metadata.
    """

    description: Optional[Description]
    metadata: Metadata
    points: List[Point]


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
        return DummySerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return DummmyParser.parse
