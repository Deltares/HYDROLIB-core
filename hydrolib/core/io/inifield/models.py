import logging
from abc import ABC, abstractclassmethod
from enum import Enum
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import Field
from pydantic.class_validators import validator

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.util import (
    get_split_string_on_delimiter_validator,
    make_list_validator,
)

logger = logging.getLogger(__name__)


class DataFileType(str, Enum):
    """
    Enum class containing the valid values for the dataFileType
    attribute in several subclasses of AbstractIniField.
    """

    arcinfo = "arcinfo"
    geotiff = "GeoTIFF"
    sample = "sample"
    onedfield = "1dField"
    polygon = "polygon"

    allowedvaluestext = "Possible values: arcinfo, GeoTIFF, sample, 1dField, polygon."


class InterpolationMethod(str, Enum):
    """
    Enum class containing the valid values for the dataFileType
    attribute in several subclasses of AbstractIniField.
    """

    constant = "constant"  # only with dataFileType=polygon .
    triangulation = "triangulation"  # Delaunay triangulation+linear interpolation.
    averaging = "averaging"  # grid cell averaging.

    allowedvaluestext = "Possible values: constant, triangulation, averaging."


class Operand(str, Enum):
    """
    Enum class containing the valid values for the operand
    attribute in several subclasses of AbstractIniField.
    """

    override = "O"  # override any previous data.
    append = "A"  # append, sets only where data is still missing.
    add = "+"  # adds the provided values to the existing values.
    mult = "*"  # multiplies the existing values by the provided values.
    max = "X"  # takes the maximum of the existing values and the provided values.
    min = "N"  # takes the minimum of the existing values and the provided values.

    allowedvaluestext = "Possible values: O, A, +, *, X, N."


class AveragingType(str, Enum):
    """
    Enum class containing the valid values for the averagingType
    attribute in several subclasses of AbstractIniField.
    """

    mean = "mean"  # simple average
    nearestnb = "nearestNb"  # nearest neighbour value
    max = "max"  # highest
    min = "min"  # lowest
    invdist = "invDist"  # inverse-weighted distance average
    minabs = "minAbs"  # smallest absolute value

    allowedvaluestext = "Possible values: mean, nearestNb, max, min, invDist, minAbs."


class LocationType(str, Enum):
    """
    Enum class containing the valid values for the locationType
    attribute in several subclasses of AbstractIniField.
    """

    oned = "1d"  # interpolate only to 1d nodes/links
    twod = "2d"  # interpolate only to 2d nodes/lin
    all = "all"  # interpolate to all nodes/links

    allowedvaluestext = "Possible values: 1d, 2d, all."


class IniFieldGeneral(INIGeneral):
    """The initial field file's `[General]` section with file meta data."""

    class Comments(INIBasedModel.Comments):
        fileversion: Optional[str] = Field(
            "File version. Do not edit this.", alias="fileVersion"
        )
        filetype: Optional[str] = Field(
            "File type. Should be 'iniField'. Do not edit this.",
            alias="fileType",
        )

    comments: Comments = Comments()
    _header: Literal["General"] = "General"
    fileversion: str = Field("2.00", alias="fileVersion")
    filetype: Literal["iniField"] = Field("iniField", alias="fileType")


# class AbstractSpatialField(INIBasedModel, ABC):
#     quantity: str = Field(alias="quantity")


# class InitialField(AbstractSpatialField):
#     _header: Literal["Initial"] = "Initial"


# class ParameterField(AbstractSpatialField):
#     _header: Literal["Parameter"] = "Parameter"


class IniFieldModel(INIModel):
    """
    The overall inifield model that contains the contents of one initial field and parameter file.

    This model is typically referenced under a [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry.inifieldfile[..]`.

    Attributes:
        general (IniFieldGeneral): `[General]` block with file metadata.
    """

    general: IniFieldGeneral = IniFieldGeneral()
    # initial: List[InitialField] = []
    # parameter: List[ParameterField] = []

    # _split_to_list = make_list_validator("boundary", "lateral")

    @classmethod
    def _ext(cls) -> str:
        return ".ini"

    @classmethod
    def _filename(cls) -> str:
        return "fieldFile"
