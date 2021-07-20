"""polyfil.py defines all classes and functions related to handling pol/pli(z) files.
"""

from enum import Enum
from hydrolib.io.common import ParseMsg, BaseModel
from typing import Callable, Dict, List, Optional, Sequence, Tuple


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
