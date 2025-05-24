"""models.py defines all classes and functions related to representing pol/pli(z) files.
"""

from typing import Callable, List, Optional, Sequence, Tuple

from pydantic.v1 import Field

from hydrolib.core.base.models import BaseModel, ModelSaveSettings, ParsableFileModel


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


class PolyFile(ParsableFileModel):
    """
    Poly-file (.pol/.pli/.pliz) representation.

    Notes:
        - The `has_z_values` attribute is used to determine if the PolyFile contains z-values.
        - The `has_z_values` is false by default and should be set to true if the PolyFile path ends with `.pliz`.
        - The `***.pliz` file should have a 2*3 structure, where the third column contains the z-values, otherwise
        (the parser will give an error).
        - If there is a label in the file, the parser will ignore the label and read the file as a normal polyline file.
        ```
        tfl_01
            2 2
            0.00 1.00 #zee
            0.00 2.00 #zee
        ```
        - if the file is .pliz, and the dimensions are 2*5 the first three columns will be considered as x, y, z values
        and the last two columns will be considered as data values.
        ```
        L1
            2 5
            63.35 12.95 -4.20 -5.35 0
            45.20 6.35 -3.00 -2.90 0
        ```
    """

    has_z_values: bool = False
    objects: Sequence[PolyObject] = Field(default_factory=list)

    def _serialize(self, _: dict, save_settings: ModelSaveSettings) -> None:
        from .serializer import write_polyfile

        # We skip the passed dict for a better one.
        write_polyfile(self._resolved_filepath, self.objects, self.serializer_config)

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
        # Prevent circular dependency in Parser
        from hydrolib.core.dflowfm.polyfile.parser import read_polyfile

        return read_polyfile

    @property
    def x(self) -> List[float]:
        """X-coordinates of all points in the PolyFile."""
        return [point.x for obj in self.objects for point in obj.points]

    @property
    def y(self) -> List[float]:
        """Y-coordinates of all points in the PolyFile."""
        return [point.y for obj in self.objects for point in obj.points]

    def get_z_sources_sinks(self) -> Tuple[List[float], List[float]]:
        """
        Get the z values of the source and sink points from the polyline file.

        Returns:
            z_source, z_sinkA: Tuple[List[float]]:
            If the polyline has data (more than 3 columns), then both the z_source and z_sink will be a list of two values.
            Otherwise, the z_source and the z_sink will be a single value each.

        Note:
             - calling this method on a polyline file that does not have z-values will return a list of None.

        Examples:
        in case the polyline has 3 columns:
            >>> polyline = PolyFile("tests/data/input/source-sink/leftsor.pliz")
            >>> z_source, z_sink = polyline.get_z_sources_sinks()
            >>> print(z_source, z_sink)
            [-3.0] [-4.2]

        in case the polyline has more than 3 columns:
            >>> polyline = PolyFile("tests/data/input/source-sink/leftsor-5-columns.pliz") #Doctest: +SKIP
            >>> z_source, z_sink = polyline.get_z_sources_sinks()
            >>> print(z_source, z_sink)
            [-3.0, -2.9] [-4.2, -5.35]

        in case the polyline does not have z-values:
            >>> root_dir = "tests/data/input/dflowfm_individual_files/polylines"
            >>> polyline = PolyFile(f"{root_dir}/boundary-polyline-no-z-no-label.pli")
            >>> z_source, z_sink = polyline.get_z_sources_sinks()
            >>> print(z_source, z_sink)
            [None] [None]
        """
        has_data = True if self.objects[0].points[0].data else False

        z_source_sink = []
        for elem in [0, -1]:
            point = self.objects[0].points[elem]
            if has_data:
                z_source_sink.append([point.z, point.data[0]])
            else:
                z_source_sink.append([point.z])

        z_sink: list[float | None] = z_source_sink[0]
        z_source: list[float | None] = z_source_sink[1]
        return z_source, z_sink

    @property
    def number_of_points(self) -> int:
        """Total number of points in the PolyFile."""
        return len(self.x)
