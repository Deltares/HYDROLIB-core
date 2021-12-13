"""models.py defines all classes and functions related to representing pol/pli(z) files.
"""

from typing import Callable, List, Optional, Sequence

from hydrolib.core.basemodel import BaseModel, FileModel


class Description(BaseModel):
    """Description of a single PolyObject.

    The Description will be prepended to a block. Each line will
    start with a '*'.

    Attributes:
        content (str): The content of this Description.
    """

    content: str


class Metadata(BaseModel):
    """Metadata of a single PolyObject.

    Attributes:
        name (str): The name of the PolyObject
        n_rows (int): The number of rows (i.e. Point instances) of the PolyObject
        n_columns (int): The total number of values in a Point, including x, y, and z.
    """

    name: str
    n_rows: int
    n_columns: int


class Point(BaseModel):
    """Point consisting of a x and y coordinate, an optional z coordinate and data.

    Attributes:
        x (float): The x-coordinate of this Point
        y (float): The y-coordinate of this Point
        z (Optional[float]): An optional z-coordinate of this Point.
        data (Sequence[float]): The additional data variables of this Point.
    """

    x: float
    y: float
    z: Optional[float]
    data: Sequence[float]

    def _get_identifier(self, data: dict) -> Optional[str]:
        x = data.get("x")
        y = data.get("y")
        z = data.get("z")
        return f"x:{x} y:{y} z:{z}"


class PolyObject(BaseModel):
    """PolyObject describing a single block in a poly file.

    The metadata should be consistent with the points:
    - The number of points should be equal to number of rows defined in the metadata
    - The data of each point should be equal to the number of columns defined in the
      metadata.

    Attributes:
        description (Optional[Description]):
            An optional description of this PolyObject
        metadata (Metadata):
            The Metadata of this PolObject, describing the structure
        points (List[Point]):
            The points describing this PolyObject, structured according to the Metadata
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
        # TODO Prevent circular dependency in Parser
        from .serializer import write_polyfile

        return write_polyfile

    @classmethod
    def _get_parser(cls) -> Callable:
        # TODO Prevent circular dependency in Parser
        from .parser import read_polyfile

        return read_polyfile
