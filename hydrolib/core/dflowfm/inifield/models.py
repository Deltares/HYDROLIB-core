import logging
from abc import ABC
from typing import Dict, List, Literal, Optional

from pydantic.v1 import Field
from pydantic.v1.class_validators import root_validator, validator
from pydantic.v1.types import NonNegativeFloat, PositiveInt
from strenum import StrEnum

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.common import LocationType
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.util import (
    get_enum_validator,
    make_list_validator,
    validate_required_fields,
)

logger = logging.getLogger(__name__)


class DataFileType(StrEnum):
    """
    Enum class containing the valid values for the dataFileType
    attribute in several subclasses of AbstractIniField.
    """

    arcinfo = "arcinfo"
    geotiff = "GeoTIFF"
    sample = "sample"
    onedfield = "1dField"
    polygon = "polygon"
    uniform = "uniform"
    netcdf = "netcdf"

    allowedvaluestext = "Possible values: arcinfo, GeoTIFF, sample, 1dField, polygon."


class InterpolationMethod(StrEnum):
    """
    Enum class containing the valid values for the interpolationMethod
    attribute in several subclasses of AbstractIniField.
    """

    constant = "constant"  # only with dataFileType=polygon .
    triangulation = "triangulation"  # Delaunay triangulation+linear interpolation.
    averaging = "averaging"  # grid cell averaging.
    linear_space_time = "linearSpaceTime"  # linear interpolation in space and time.

    allowedvaluestext = "Possible values: constant, triangulation, averaging."


class AveragingType(StrEnum):
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


class AbstractSpatialField(INIBasedModel, ABC):
    """
    Abstract base class for `[Initial]` and `[Parameter]` block data in
    inifield files.

    Defines all common fields. Used via subclasses InitialField and ParameterField.
    """

    class Comments(INIBasedModel.Comments):
        quantity: Optional[str] = Field(
            "Name of the quantity. See UM Table D.2.", alias="quantity"
        )
        datafile: Optional[str] = Field(
            "Name of file containing field data values.", alias="dataFile"
        )
        datafiletype: Optional[str] = Field("Type of dataFile.", alias="dataFileType")
        interpolationmethod: Optional[str] = Field(
            "Type of (spatial) interpolation.", alias="interpolationmethod"
        )
        operand: Optional[str] = Field(
            "How this data is combined with previous data for the same quantity (if any).",
            alias="operand",
        )
        averagingtype: Optional[str] = Field(
            "Type of averaging, if interpolationMethod=averaging .",
            alias="averagingtype",
        )
        averagingrelsize: Optional[str] = Field(
            "Relative search cell size for averaging.", alias="averagingrelsize"
        )
        averagingnummin: Optional[str] = Field(
            "Minimum number of points in averaging. Must be ≥ 1.",
            alias="averagingnummin",
        )
        averagingpercentile: Optional[str] = Field(
            "Percentile value for which data values to include in averaging. 0.0 means off.",
            alias="averagingpercentile",
        )
        extrapolationmethod: Optional[str] = Field(
            "Option for (spatial) extrapolation.", alias="extrapolationmethod"
        )
        locationtype: Optional[str] = Field(
            "Target location of interpolation.", alias="locationtype"
        )
        value: Optional[str] = Field(
            "Only for dataFileType=polygon. The constant value to be set inside for all model points inside the polygon."
        )

    comments: Comments = Comments()

    quantity: str = Field(alias="quantity")
    datafile: DiskOnlyFileModel = Field(alias="dataFile")

    datafiletype: DataFileType = Field(alias="dataFileType")
    interpolationmethod: Optional[InterpolationMethod] = Field(
        alias="interpolationMethod"
    )
    operand: Optional[Operand] = Field(Operand.override.value, alias="operand")
    averagingtype: Optional[AveragingType] = Field(
        AveragingType.mean.value, alias="averagingType"
    )
    averagingrelsize: Optional[NonNegativeFloat] = Field(1.01, alias="averagingRelSize")
    averagingnummin: Optional[PositiveInt] = Field(1, alias="averagingNumMin")
    averagingpercentile: Optional[NonNegativeFloat] = Field(
        0, alias="averagingPercentile"
    )
    extrapolationmethod: Optional[bool] = Field(False, alias="extrapolationMethod")
    locationtype: Optional[LocationType] = Field(
        LocationType.all.value, alias="locationType"
    )
    value: Optional[float] = Field(alias="value")

    datafiletype_validator = get_enum_validator("datafiletype", enum=DataFileType)
    interpolationmethod_validator = get_enum_validator(
        "interpolationmethod", enum=InterpolationMethod
    )
    operand_validator = get_enum_validator("operand", enum=Operand)
    averagingtype_validator = get_enum_validator("averagingtype", enum=AveragingType)
    locationtype_validator = get_enum_validator("locationtype", enum=LocationType)

    @root_validator(allow_reuse=True)
    def validate_that_value_is_present_for_polygons(cls, values: Dict) -> Dict:
        """Validates that the value is provided when dealing with polygons."""
        return validate_required_fields(
            values,
            "value",
            conditional_field_name="datafiletype",
            conditional_value=DataFileType.polygon,
        )

    @validator("value", always=True)
    @classmethod
    def _validate_value_and_filetype(cls, v, values: dict):
        if v is not None and values.get("datafiletype") != DataFileType.polygon:
            raise ValueError(
                f"When value={v} is given, dataFileType={DataFileType.polygon} is required."
            )

        return v


class InitialField(AbstractSpatialField):
    """
    Initial condition field definition, represents an `[Initial]` block in
    an inifield file.
    Typically inside the definition list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.inifieldfile.initial[..]`

    All lowercased attributes match with the initial field input as described in
    [UM Sec.D.2](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.D.2).
    """

    _header: Literal["Initial"] = "Initial"


class ParameterField(AbstractSpatialField):
    """
    Parameter field definition, represents a `[Parameter]` block in
    an inifield file.
    Typically inside the definition list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.inifieldfile.parameter[..]`
    """

    _header: Literal["Parameter"] = "Parameter"


class IniFieldModel(INIModel):
    """
    The overall inifield model that contains the contents of one initial field and parameter file.

    This model is typically referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.inifieldfile[..]`.

    Attributes:
        general (IniFieldGeneral): `[General]` block with file metadata.
        initial (List[InitialField]): List of `[Initial]` blocks with initial condition definitions.
        parameter (List[ParameterField]): List of `[Parameter]` blocks with spatial parameter definitions.
    """

    general: IniFieldGeneral = IniFieldGeneral()
    initial: List[InitialField] = Field(default_factory=list)
    parameter: List[ParameterField] = Field(default_factory=list)

    _split_to_list = make_list_validator("initial", "parameter")

    @classmethod
    def _ext(cls) -> str:
        return ".ini"

    @classmethod
    def _filename(cls) -> str:
        return "fieldFile"
