import logging
from abc import ABC
from pathlib import Path
from typing import Annotated, Dict, List, Literal, Optional, Set

from pydantic import (
    BeforeValidator,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from pydantic.types import NonNegativeFloat, PositiveInt
from strenum import StrEnum

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.common import LocationType
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.ini.io_models import Section
from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.util import (
    enum_value_parser,
    make_list,
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
        None, alias="interpolationMethod"
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
    value: Optional[float] = Field(None, alias="value")

    model_config = ConfigDict(extra="allow")

    @classmethod
    def _process_section_values(cls, values):
        """Process Section objects and extract/convert values as needed.

        Args:
            values: The values to process, which may be a Section object or a dictionary.

        Returns:
            A dictionary containing the processed values.
        """
        # If values is a Section object, we need to handle it specially
        if isinstance(values, Section):
            # Extract the datafile value if present
            data_file = super()._extract_file_model_from_section(
                values, "datafile", DiskOnlyFileModel
            )

            # Convert Section to dictionary
            values_dict = super()._convert_section_to_dict(values)

            # If we found a datafile, add it to the dictionary
            if data_file is not None:
                values_dict["datafile"] = data_file

            return values_dict

        return values

    tracerfallvelocity: Optional[float] = Field(None, alias="tracerFallVelocity")
    tracerdecaytime: Optional[float] = Field(None, alias="tracerDecayTime")

    @model_validator(mode="before")
    @classmethod
    def validate_that_value_is_present_for_polygons(cls, values: Dict) -> Dict:
        """Validates that the value is provided when dealing with polygons."""
        # Process Section objects if needed
        values = cls._process_section_values(values)

        # Process dictionary-like objects
        data_file = values.get("datafile")
        if isinstance(data_file, (str, Path)):
            data_file = DiskOnlyFileModel(data_file)
            values["datafile"] = data_file

        validate_required_fields(
            values,
            "value",
            conditional_field_name="datafiletype",
            conditional_value=DataFileType.polygon,
        )

        value_field_value = values.get("value")
        datafiletype_field_value = values.get("datafiletype")
        if (
            value_field_value is not None
            and datafiletype_field_value is not None
            and datafiletype_field_value.lower() != DataFileType.polygon
        ):
            raise ValueError(
                f"When value={value_field_value} is given, dataFileType={DataFileType.polygon} is required."
            )

        return values

    @field_validator("locationtype", mode="before")
    @classmethod
    def validate_location_type(cls, v):
        return enum_value_parser(v, LocationType)

    @field_validator("averagingtype", mode="before")
    @classmethod
    def validate_average_type(cls, v):
        return enum_value_parser(v, AveragingType)

    @field_validator("datafiletype", mode="before")
    @classmethod
    def validate_data_file_type(cls, v):
        return enum_value_parser(v, DataFileType)

    @field_validator("operand", mode="before")
    @classmethod
    def validate_operand(cls, v):
        return enum_value_parser(v, Operand)

    @field_validator("interpolationmethod", mode="before")
    @classmethod
    def validate_interpolation_method(cls, v):
        return enum_value_parser(v, InterpolationMethod)

    @field_validator("datafile", mode="before")
    @classmethod
    def validate_datafile(cls, v):
        """Convert string values to DiskOnlyFileModel instances."""
        if isinstance(v, (str, Path)):
            return DiskOnlyFileModel(filepath=v)
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
    initial: Annotated[List[InitialField], BeforeValidator(make_list)] = Field(
        default_factory=list
    )
    parameter: Annotated[List[ParameterField], BeforeValidator(make_list)] = Field(
        default_factory=list
    )

    @classmethod
    def _ext(cls) -> str:
        return ".ini"

    @classmethod
    def _filename(cls) -> str:
        return "fieldFile"
