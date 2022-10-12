from typing import List, Optional
from enum import Enum


class LocationType(str, Enum):
    """
    Enum class containing the valid values for the locationType
    attribute in several classes such as Lateral and ObservationPoint.
    """

    oned = "1d"
    """str: Denotes 1D locations (typically 1D pressure points) in a model."""

    twod = "2d"
    """str: Denotes 2D locations (typically 2D grid cells) in a model."""

    all = "all"
    """str: Denotes that both 1D and 2D locations may be selected."""

class XYZValues:
    """Class that holds lists of x, y and z values."""

    x: List[float] = []
    """The x values."""

    y: List[float] = []
    """The y values."""

    z: List[Optional[float]] = []
    """The z values. The values can be `None`."""