"""T3D file"""

from strenum import StrEnum


class LayerType(StrEnum):
    """
    Layer types in the t3d file.
    """

    sigma = "SIGMA"
    z = "Z"
