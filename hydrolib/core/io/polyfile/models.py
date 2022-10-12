"""models.py defines all classes and functions related to representing pol/pli(z) files.
"""

from typing import Callable, List, Optional, Sequence, Tuple

from hydrolib.core.basemodel import BaseModel, ParsableFileModel


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

class XYZValues:
    """Class that holds lists of x, y and z values."""

    x: List[float] = []
    """The x values."""

    y: List[float] = []
    """The y values."""

    z: List[Optional[float]] = []
    """The z values. The values can be `None`."""

    def append(self, x: float, y: float, z: Optional[float]):
        """Append an x, y and z value to their corresponding lists.

        Args:
            x (float): The x value
            y (float): The y value
            z (Optional[float]): The z value. Can be `None`.
        """
        self.x.append(x)
        self.y.append(y)
        self.z.append(z)

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

    @property
    def xy_values(self) -> Tuple[List[float], List[float]]:
        """Get a tuple containing the x-coordinates and y-coordinates of the polygon points.

        Returns:
            Tuple[List[float], List[float]]: Tuple containing a list of x-coordinates and a list of y-coordinates
        """

        x, y, z = self.xyz_values
        return x, y

    @property
    def xyz_values(self) -> Tuple[List[float], List[float], List[Optional[float]]]:
        """Get a tuple containing the x-coordinates, y-coordinates and z values of the polygon points.

        Returns:
            Tuple[List[float], List[float], List[Optional[float]]]: Tuple containing a list of x-coordinates, a list of y-coordinates and a list of z values.
        """
        x: List[float] = []
        y: List[float] = []
        z: List[Optional[float]] = []

        for point in self.points:
            x.append(point.x)
            y.append(point.y)
            z.append(point.z)

        return x, y, z


class PolyFile(ParsableFileModel):
    """Poly-file (.pol/.pli/.pliz) representation."""

    has_z_values: bool = False
    objects: Sequence[PolyObject] = []

    def _serialize(self, _: dict) -> None:
        from .serializer import write_polyfile

        # We skip the passed dict for a better one.
        write_polyfile(self._resolved_filepath, self.objects)

    @classmethod
    def _ext(cls) -> str:
        return ".pli"

    @classmethod
    def _filename(cls) -> str:
        return "objects"

    @classmethod
    def _get_serializer(cls) -> Callable:
        # Unused, but requires abstract implementation
        pass

    @classmethod
    def _get_parser(cls) -> Callable:
        # TODO Prevent circular dependency in Parser
        from .parser import read_polyfile

        return read_polyfile
