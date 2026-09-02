"""Initial field model definitions for D-Flow FM inifield files."""

import logging
import warnings
from abc import ABC
from pathlib import Path
from typing import Annotated, Dict, List, Literal, Optional

from pydantic import (
    BeforeValidator,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
from pydantic.types import NonNegativeFloat, PositiveInt

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.common import LocationType
from hydrolib.core.dflowfm.common.models import (
    AveragingType,
    DataFileType,
    InterpolationMethod,
    Operand,
)
from hydrolib.core.dflowfm.ini.io_models import Section
from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.util import (
    enum_value_parser,
    make_list,
    validate_required_fields,
)

logger = logging.getLogger(__name__)


class IniFieldGeneral(INIGeneral):
    """The initial field file's `[General]` section with file meta data."""

    class Comments(INIBasedModel.Comments):
        """Comments for the IniFieldGeneral section fields."""

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


class OperandInterpolationValidators(ABC):
    """Field validators common to every spatial-field block.

    A plain validator mixin (not an `INIBasedModel` itself); the concrete block
    bases `SpatialForcingBase` and `AbstractSpatialField` bring in `INIBasedModel`.

    Holds the `operand` and `interpolationMethod` validators shared by all four
    spatial-field blocks: `Meteo` / `Spatial` (external forcings) and
    `InitialField` / `ParameterField` (inifield). It is inherited directly by the
    two concrete block bases `SpatialForcingBase` (for `Meteo` / `Spatial`) and
    `AbstractSpatialField` (for `InitialField` / `ParameterField`). The validators
    use ``check_fields=False`` so each applies only to the subclasses that declare
    the corresponding field.

    `averagingType` is intentionally not shared: `Meteo` reaches this base too and
    stores `averagingType` as a raw integer, so an enum validator on it must stay
    off `Meteo`.
    """

    @field_validator("operand", mode="before", check_fields=False)
    @classmethod
    def _validate_operand(cls, v):
        return enum_value_parser(v, Operand, Operand.legacy_alternatives())

    @field_validator("interpolationmethod", mode="before", check_fields=False)
    @classmethod
    def _validate_interpolationmethod(cls, v):
        return enum_value_parser(v, InterpolationMethod)


class LocationTypeDataFileTypeValidators(ABC):
    """Field validators shared by the data-file spatial blocks.

    An independent plain validator mixin holding the `locationType` and
    `dataFileType` validators shared by `Spatial` (external forcings) and
    `InitialField` / `ParameterField` (inifield). `Meteo` does not use it — it has
    a `forcingFileType` and no `locationType` field. It does not inherit
    `OperandInterpolationValidators`; classes that need both validator groups
    (`Spatial`, `AbstractSpatialField`) inherit both mixins directly.
    """

    @field_validator("locationtype", mode="before", check_fields=False)
    @classmethod
    def _validate_locationtype(cls, v):
        return enum_value_parser(v, LocationType)

    @field_validator("datafiletype", mode="before", check_fields=False)
    @classmethod
    def _validate_datafiletype(cls, v):
        result = v
        if v is not None:
            result = enum_value_parser(v, DataFileType)
        return result


class AbstractSpatialField(
    OperandInterpolationValidators, LocationTypeDataFileTypeValidators, INIBasedModel, ABC
):
    """Abstract base class for `[Initial]` and `[Parameter]` block data in inifield files.

    Defines all common fields. Used via subclasses InitialField and ParameterField.
    """

    class Comments(INIBasedModel.Comments):
        """Comments for the AbstractSpatialField section fields."""

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
    averagingtype: Optional[AveragingType] = Field(None, alias="averagingType")
    averagingrelsize: Optional[NonNegativeFloat] = Field(None, alias="averagingRelSize")
    averagingnummin: Optional[PositiveInt] = Field(None, alias="averagingNumMin")
    averagingpercentile: Optional[NonNegativeFloat] = Field(
        None, alias="averagingPercentile"
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

        if (values.get("interpolationmethod") == InterpolationMethod.constant and
                not values["quantity"].startswith("initialvertical")):
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

    @field_validator("averagingtype", mode="before")
    @classmethod
    def validate_average_type(cls, v):
        return enum_value_parser(v, AveragingType)

    @field_validator("datafile", mode="before")
    @classmethod
    def validate_datafile(cls, v):
        """Convert string values to DiskOnlyFileModel instances."""
        if isinstance(v, (str, Path)):
            return DiskOnlyFileModel(filepath=v)
        return v


class InitialField(AbstractSpatialField):
    """Initial condition field definition, represents an `[Initial]` block in an inifield file.

    Typically inside the definition list of a
    [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.inifieldfile.initial[..]`

    All lowercased attributes match with the initial field input as described in
    [UM Sec.D.2](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.D.2).

    .. deprecated:: 1.1.0
        `InitialField` and `[Initial]` blocks are deprecated. Use `Spatial` blocks
        in the external forcings file (``.ext``) instead.
    """

    _header: Literal["Initial"] = "Initial"

    @model_validator(mode="after")
    def _warn_initial_field_deprecated(self) -> "InitialField":
        """Emit a DeprecationWarning whenever an [Initial] block is instantiated.

        `[Initial]` blocks in inifield files are superseded by `[Spatial]` blocks
        in the external forcings file (``.ext``) as of version 1.1.0.
        """
        warnings.warn(
            "`InitialField` (and `[Initial]` blocks in inifield files) is deprecated "
            "since 1.1.0 and will be removed in 2.0.0; use `Spatial` (and `[Spatial]` "
            "blocks in the external forcings file) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self


class ParameterField(AbstractSpatialField):
    """Parameter field definition, represents a `[Parameter]` block in an inifield file.

    Typically inside the definition list of a
    [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.inifieldfile.parameter[..]`

    .. deprecated:: 1.1.0
        `ParameterField` and `[Parameter]` blocks are deprecated. Use `Spatial` blocks
        in the external forcings file (``.ext``) instead.
    """

    _header: Literal["Parameter"] = "Parameter"

    @model_validator(mode="after")
    def _warn_parameter_field_deprecated(self) -> "ParameterField":
        """Emit a DeprecationWarning whenever a [Parameter] block is instantiated.

        `[Parameter]` blocks in inifield files are superseded by `[Spatial]` blocks
        in the external forcings file (``.ext``) as of version 1.1.0.
        """
        warnings.warn(
            "`ParameterField` (and `[Parameter]` blocks in inifield files) is deprecated "
            "since 1.1.0 and will be removed in 2.0.0; use `Spatial` (and `[Spatial]` "
            "blocks in the external forcings file) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self


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
