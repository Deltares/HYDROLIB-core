from pathlib import Path
from typing import Dict, List, Literal, Optional, Set, Union

from pydantic.v1 import Field, root_validator, validator
from strenum import StrEnum

from hydrolib.core.base.models import (
    DiskOnlyFileModel,
    validator_set_default_disk_only_file_model_when_none,
)
from hydrolib.core.base.utils import str_is_empty_or_none
from hydrolib.core.dflowfm.bc.models import ForcingBase, ForcingData, ForcingModel
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.serializer import INISerializerConfig
from hydrolib.core.dflowfm.ini.util import (
    LocationValidationConfiguration,
    UnknownKeywordErrorManager,
    get_enum_validator,
    get_split_string_on_delimiter_validator,
    make_list_validator,
    validate_location_specification,
)
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.tim.models import TimModel

SOURCE_SINKS_QUANTITIES_VALID_PREFIXES = (
    "initialtracer",
    "tracerbnd",
    "sedfracbnd",
    "initialsedfrac",
)


class Boundary(INIBasedModel):
    """
    A `[Boundary]` block for use inside an external forcings file,
    i.e., a [ExtModel][hydrolib.core.dflowfm.ext.models.ExtModel].

    All lowercased attributes match with the boundary input as described in
    [UM Sec.C.5.2.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.1).
    """

    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    _header: Literal["Boundary"] = "Boundary"
    quantity: str = Field(alias="quantity")
    nodeid: Optional[str] = Field(alias="nodeId")
    locationfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="locationFile"
    )
    forcingfile: Union[ForcingModel, List[ForcingModel]] = Field(alias="forcingFile")
    bndwidth1d: Optional[float] = Field(alias="bndWidth1D")
    bndbldepth: Optional[float] = Field(alias="bndBlDepth")
    returntime: Optional[float] = Field(alias="returnTime")

    def is_intermediate_link(self) -> bool:
        return True

    @classmethod
    def _is_valid_locationfile_data(
        cls, elem: Union[None, str, Path, DiskOnlyFileModel]
    ) -> bool:
        return isinstance(elem, Path) or (
            isinstance(elem, DiskOnlyFileModel) and elem.filepath is not None
        )

    @root_validator
    @classmethod
    def check_nodeid_or_locationfile_present(cls, values: Dict):
        """
        Verifies that either nodeid or locationfile properties have been set.

        Args:
            values (Dict): Dictionary with values already validated.

        Raises:
            ValueError: When none of the values are present.

        Returns:
            Dict: Validated dictionary of values for Boundary.
        """
        node_id = values.get("nodeid", None)
        location_file = values.get("locationfile", None)
        if str_is_empty_or_none(node_id) and not cls._is_valid_locationfile_data(
            location_file
        ):
            raise ValueError(
                "Either nodeId or locationFile fields should be specified."
            )
        return values

    def _get_identifier(self, data: dict) -> Optional[str]:
        """
        Retrieves the identifier for a boundary, which is the nodeid

        Args:
            data (dict): Dictionary of values for this boundary.

        Returns:
            str: The nodeid value or None if not found.
        """
        return data.get("nodeid")

    @property
    def forcing(self) -> Union[ForcingBase, None]:
        """Retrieves the corresponding forcing data for this boundary.

        Returns:
            ForcingBase: The corresponding forcing data. None when this boundary does not have a forcing file or when the data cannot be found.
        """
        result = None
        if self.forcingfile is not None:
            for forcing in self.forcingfile.forcing:

                if self.nodeid == forcing.name and any(
                    quantity.quantity.startswith(self.quantity)
                    for quantity in forcing.quantityunitpair
                ):
                    result = forcing
                    break

        return result


class Lateral(INIBasedModel):
    """
    A `[Lateral]` block for use inside an external forcings file,
    i.e., a [ExtModel][hydrolib.core.dflowfm.ext.models.ExtModel].

    All lowercased attributes match with the lateral input as described in
    [UM Sec.C.5.2.2](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.2).
    """

    _header: Literal["Lateral"] = "Lateral"
    id: str = Field(alias="id")
    name: str = Field("", alias="name")
    locationtype: Optional[str] = Field(alias="locationType")
    nodeid: Optional[str] = Field(alias="nodeId")
    branchid: Optional[str] = Field(alias="branchId")
    chainage: Optional[float] = Field(alias="chainage")
    numcoordinates: Optional[int] = Field(alias="numCoordinates")
    xcoordinates: Optional[List[float]] = Field(alias="xCoordinates")
    ycoordinates: Optional[List[float]] = Field(alias="yCoordinates")
    discharge: ForcingData = Field(alias="discharge")

    def is_intermediate_link(self) -> bool:
        return True

    _split_to_list = get_split_string_on_delimiter_validator(
        "xcoordinates", "ycoordinates"
    )

    @root_validator(allow_reuse=True)
    def validate_that_location_specification_is_correct(cls, values: Dict) -> Dict:
        """Validates that the correct location specification is given."""
        return validate_location_specification(
            values, config=LocationValidationConfiguration(minimum_num_coordinates=1)
        )

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("id") or data.get("name")

    @validator("locationtype")
    @classmethod
    def validate_location_type(cls, v: str) -> str:
        """
        Method to validate whether the specified location type is correct.

        Args:
            v (str): Given value for the locationtype field.

        Raises:
            ValueError: When the value given for locationtype is unknown.

        Returns:
            str: Validated locationtype string.
        """
        possible_values = ["1d", "2d", "all"]
        if v.lower() not in possible_values:
            raise ValueError(
                "Value given ({}) not accepted, should be one of: {}".format(
                    v, ", ".join(possible_values)
                )
            )
        return v


class SourceSink(INIBasedModel):
    """
    A `[SourceSink]` block for use inside an external forcings file,
    i.e., a [ExtModel][hydrolib.core.dflowfm.ext.models.SourceSink].

    All lowercased attributes match with the source-sink input as described in
    [UM Sec.C.5.2.4](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.4).
    """

    _header: Literal["SourceSink"] = "SourceSink"
    id: str = Field(alias="id")
    name: str = Field("", alias="name")
    locationfile: Optional[DiskOnlyFileModel] = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="locationFile"
    )

    numcoordinates: Optional[int] = Field(alias="numCoordinates")
    xcoordinates: Optional[List[float]] = Field(alias="xCoordinates")
    ycoordinates: Optional[List[float]] = Field(alias="yCoordinates")

    zsource: Optional[Union[float, List[float]]] = Field(alias="zSource")
    zsink: Optional[Union[float, List[float]]] = Field(alias="zSink")
    area: Optional[float] = Field(alias="Area")

    discharge: ForcingData = Field(alias="discharge")
    salinitydelta: Optional[ForcingData] = Field(alias="salinityDelta")
    temperaturedelta: Optional[ForcingData] = Field(alias="temperatureDelta")

    def is_intermediate_link(self) -> bool:
        return True

    @classmethod
    def _exclude_from_validation(cls, input_data: Optional[dict] = None) -> Set:
        fields = cls.__fields__
        unknown_keywords = [
            key
            for key in input_data.keys()
            if key not in fields
            and key.startswith(SOURCE_SINKS_QUANTITIES_VALID_PREFIXES)
        ]
        return set(unknown_keywords)

    class Config:
        """
        Config class to tell Pydantic to accept fields not explicitly declared in the model.
        """

        # Allow dynamic fields
        extra = "allow"

    def __init__(self, **data):
        super().__init__(**data)
        # Add dynamic attributes for fields starting with 'tracer'
        for key, value in data.items():
            if isinstance(key, str) and key.startswith(
                SOURCE_SINKS_QUANTITIES_VALID_PREFIXES
            ):
                setattr(self, key, value)

    @root_validator(pre=True)
    def validate_location_specification(cls, values):
        """
        Ensures that either `locationfile` or a valid set of coordinates is provided.

         This validation enforces that at least one of the following conditions is met:
         1. `locationfile` is provided.
         2. The combination of `numcoordinates`, `xcoordinates`, and `ycoordinates` is valid:
             - `xcoordinates` and `ycoordinates` must be lists of equal length.
             - The length of `xcoordinates` and `ycoordinates` must match `numcoordinates`.

         Raises:
             ValueError: If neither `locationfile` nor a valid coordinate set is provided.

         Returns:
             Dict: The validated input values.
        """
        locationfile = values.get("locationfile", values.get("locationFile"))

        numcoordinates = values.get("numcoordinates", values.get("numCoordinates"))
        xcoordinates = values.get("xcoordinates", values.get("xCoordinates"))
        ycoordinates = values.get("ycoordinates", values.get("yCoordinates"))

        has_locationfile = locationfile is not None
        has_coordinates = (
            numcoordinates is not None
            and xcoordinates is not None
            and ycoordinates is not None
            and len(xcoordinates) == len(ycoordinates) == numcoordinates
        )

        if not (has_locationfile or has_coordinates):
            raise ValueError(
                "Either `locationFile` or the combination of `numCoordinates`, `xCoordinates`, and `yCoordinates` "
                f"must be provided. for the SourceSink block `{values.get('id')}`."
            )

        return values


class MeteoForcingFileType(StrEnum):
    """
    Enum class containing the valid values for the forcingFileType
    attribute in Meteo class.
    """

    bcascii = "bcAscii"
    """str: Space-uniform time series in <*.bc> file."""

    uniform = "uniform"
    """str: Space-uniform time series in <*.tim> file."""

    unimagdir = "uniMagDir"
    """str: Space-uniform wind magnitude+direction in <*.tim> file."""

    arcinfo = "arcInfo"
    """str: Space- and time-varying wind and pressure on an equidistant grid in <*.amu/v/p> files."""

    spiderweb = "spiderweb"
    """str: Space- and time-varying cyclone wind and pressure in <*.spw> files."""

    curvigrid = "curviGrid"
    """str: Space- and time-varying wind and pressure on a curvilinear grid in <*.grd+*.amu/v/p> files."""

    netcdf = "netcdf"
    """str: NetCDF, either with gridded data, or multiple station time series."""

    allowedvaluestext = "Possible values: bcAscii, uniform, uniMagDir, arcInfo, spiderweb, curviGrid, netcdf."


class MeteoInterpolationMethod(StrEnum):
    """
    Enum class containing the valid values for the interpolationMethod
    attribute in Meteo class.
    """

    nearestnb = "nearestNb"
    """str: Nearest-neighbour interpolation, only with station-data in forcingFileType=netcdf"""
    linearSpaceTime = "linearSpaceTime"
    """str: Linear interpolation in space and time."""
    allowedvaluestext = "Possible values: nearestNb, linearSpaceTime."


class Meteo(INIBasedModel):
    """
    A `[Meteo]` block for use inside an external forcings file,
    i.e., a [ExtModel][hydrolib.core.dflowfm.ext.models.ExtModel].

    All lowercased attributes match with the meteo input as described in
    [UM Sec.C.5.2.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.3).
    """

    class Comments(INIBasedModel.Comments):
        quantity: Optional[str] = Field(
            "Name of the quantity. See UM Section C.5.3", alias="quantity"
        )
        forcingfile: Optional[str] = Field(
            "Name of file containing the forcing for this meteo quantity.",
            alias="forcingFile",
        )
        forcingfiletype: Optional[str] = Field(
            "Type of forcingFile.", alias="forcingFileType"
        )
        forcingVariableName: Optional[str] = Field(
            "Variable name used in forcingfile associated with this forcing. See UM Section C.5.3",
            alias="forcingVariableName",
        )
        targetmaskfile: Optional[str] = Field(
            "Name of <*.pol> file to be used as mask. Grid parts inside any polygon will receive the meteo forcing.",
            alias="targetMaskFile",
        )
        targetmaskinvert: Optional[str] = Field(
            "Flag indicating whether the target mask should be inverted, i.e., outside of all polygons: no or yes.",
            alias="targetMaskInvert",
        )
        interpolationmethod: Optional[str] = Field(
            "Type of (spatial) interpolation.", alias="interpolationMethod"
        )
        operand: Optional[str] = Field(
            "How this data is combined with previous data for the same quantity (if any).",
            alias="operand",
        )
        extrapolationAllowed: Optional[str] = Field(
            "Optionally allow nearest neighbour extrapolation in space (0: no, 1: yes). Default off.",
            alias="extrapolationAllowed",
        )
        extrapolationSearchRadius: Optional[str] = Field(
            "Maximum search radius for nearest neighbor extrapolation in space.",
            alias="extrapolationSearchRadius",
        )

    comments: Comments = Comments()

    @classmethod
    def _get_unknown_keyword_error_manager(cls) -> Optional[UnknownKeywordErrorManager]:
        """
        The Meteo does not currently support raising an error on unknown keywords.
        """
        return None

    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    _header: Literal["Meteo"] = "Meteo"
    quantity: str = Field(alias="quantity")
    forcingfile: Union[TimModel, ForcingModel, DiskOnlyFileModel] = Field(
        alias="forcingFile"
    )
    forcingVariableName: Optional[str] = Field(alias="forcingVariableName")
    forcingfiletype: MeteoForcingFileType = Field(alias="forcingFileType")
    targetmaskfile: Optional[PolyFile] = Field(None, alias="targetMaskFile")
    targetmaskinvert: Optional[bool] = Field(None, alias="targetMaskInvert")
    interpolationmethod: Optional[MeteoInterpolationMethod] = Field(
        alias="interpolationMethod"
    )
    operand: Optional[Operand] = Field(Operand.override.value, alias="operand")
    extrapolationAllowed: Optional[bool] = Field(alias="extrapolationAllowed")
    extrapolationSearchRadius: Optional[float] = Field(
        alias="extrapolationSearchRadius"
    )
    averagingType: Optional[int] = Field(alias="averagingType")
    averagingNumMin: Optional[float] = Field(alias="averagingNumMin")
    averagingPercentile: Optional[float] = Field(alias="averagingPercentile")

    def is_intermediate_link(self) -> bool:
        return True

    forcingfiletype_validator = get_enum_validator(
        "forcingfiletype", enum=MeteoForcingFileType
    )
    interpolationmethod_validator = get_enum_validator(
        "interpolationmethod", enum=MeteoInterpolationMethod
    )


class ExtGeneral(INIGeneral):
    """The external forcing file's `[General]` section with file meta-data."""

    _header: Literal["General"] = "General"
    fileversion: str = Field("2.01", alias="fileVersion")
    filetype: Literal["extForce"] = Field("extForce", alias="fileType")


class ExtModel(INIModel):
    """
    The overall external forcings model that contains the contents of one external forcings file (new format).

    This model is typically referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.external_forcing.extforcefilenew`.

    Attributes:
        general (ExtGeneral): `[General]` block with file metadata.
        boundary (List[Boundary]): List of `[Boundary]` blocks for all boundary conditions.
        lateral (List[Lateral]): List of `[Lateral]` blocks for all lateral discharges.
        sourcesink (List[SourceSink]): List of `[SourceSink]` blocks for all source/sink terms.
        meteo (List[Meteo]): List of `[Meteo]` blocks for all meteorological forcings.
    """

    general: ExtGeneral = ExtGeneral()
    boundary: List[Boundary] = Field(default_factory=list)
    lateral: List[Lateral] = Field(default_factory=list)
    sourcesink: List[SourceSink] = Field(default_factory=list)
    meteo: List[Meteo] = Field(default_factory=list)
    serializer_config: INISerializerConfig = INISerializerConfig(
        section_indent=0, property_indent=0
    )
    _split_to_list = make_list_validator("boundary", "lateral", "meteo", "sourcesink")

    @classmethod
    def _ext(cls) -> str:
        return ".ext"

    @classmethod
    def _filename(cls) -> str:
        return "bnd"


class SourceSinkError(Exception):
    """SourceSinkError."""

    def __init__(self, error_message: str):
        """SourceSinkError constructor."""
        print(error_message)


class InitialFieldError(Exception):
    """InitialFieldError."""

    def __init__(self, error_message: str):
        """InitialFieldError constructor."""
        print(error_message)


class MeteoError(Exception):
    """MeteoError."""

    def __init__(self, error_message: str):
        """MeteoError constructor."""
        print(error_message)


class BoundaryError(Exception):
    """BoundaryError."""

    def __init__(self, error_message: str):
        """BoundaryError constructor."""
        print(error_message)


class ParameterFieldError(Exception):
    """ParameterFieldError."""

    def __init__(self, error_message: str):
        """ParameterFieldError constructor."""
        print(error_message)
