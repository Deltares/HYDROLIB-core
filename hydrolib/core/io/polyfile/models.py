"""models.py defines all classes and functions related to representing pol/pli(z) files.
"""

from hydrolib.core.basemodel import BaseModel
from typing import List, Optional, Sequence


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
