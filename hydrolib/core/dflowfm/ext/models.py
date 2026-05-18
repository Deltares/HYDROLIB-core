"""Models for the external forcings file (new format) of D-Flow FM."""

from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional, Set, Union

from pydantic import (
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from strenum import StrEnum

from hydrolib.core.base._deprecation import DeprecatedAttributeAlias
from hydrolib.core.base.models import (
    DiskOnlyFileModel,
    set_default_disk_only_file_model,
)
from hydrolib.core.base.utils import resolve_file_model, str_is_empty_or_none
from hydrolib.core.dflowfm.bc.models import (
    ForcingBase,
    ForcingData,
    ForcingModel,
    RealTime,
)
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.serializer import INISerializerConfig
from hydrolib.core.dflowfm.ini.util import (
    LocationValidationConfiguration,
    UnknownKeywordErrorManager,
    enum_value_parser,
    make_list,
    split_string_on_delimiter,
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


def _coordinate_length(v) -> int:
    """Return the number of coordinates in a raw string or list."""
    result = 0
    if isinstance(v, str):
        result = len(v.split())
    elif isinstance(v, list):
        result = len(v)
    return result


def _is_dynamic_forcing_delta_key(key: Any) -> bool:
    """Return True if `key` names a dynamic `tracer<...>Delta`/`sedFrac<...>Delta` field.

    Per D-Flow FM User Manual Table C.8 (§C.6.2.4), `[SourceSink]` blocks
    accept any number of `tracer<tracername>Delta` and `sedFrac<fractionname>Delta`
    keys, each carrying a scalar Double or the name of a `.bc` file. They are
    case-insensitive on the wire. Comparison here is also case-insensitive so
    that both the camelCase Python kwarg form and the lowercased INI-parser
    form are recognised.
    """
    result = False
    if isinstance(key, str):
        lowered = key.lower()
        result = lowered.endswith("delta") and (
            lowered.startswith("tracer") or lowered.startswith("sedfrac")
        )
    return result


def _resolve_forcing_data(v: Any) -> float | RealTime | ForcingModel | None:
    """Coerce a raw value into a `ForcingData` member (float, RealTime, or ForcingModel).

    A string is tried as a float, then as the `RealTime` enum (case-insensitive),
    and finally resolved as a path to a `.bc` forcing file. A `Path` is always
    resolved as a forcing file. A `dict` is instantiated as a `ForcingModel`.
    Any other value (including `None`) is passed through unchanged so that
    Optional fields and already-validated values still work.

    Note: this helper returns `RealTime.realtime` for the realtime keyword, but
    Pydantic's `Union[float, RealTime, ForcingModel]` resolution stores it as
    the underlying string `"realtime"` on the model field. Compare with `==`
    (StrEnum equality), not `is`.
    """
    result = v
    if isinstance(v, str):
        try:
            result = float(v)
        except ValueError:
            try:
                result = RealTime(v.lower())
            except ValueError:
                result = resolve_file_model(v, ForcingModel)
    elif isinstance(v, Path):
        result = resolve_file_model(v, ForcingModel)
    elif isinstance(v, dict):
        result = ForcingModel(**v)
    return result


FILETYPE_FILEMODEL_MAPPING = {
    "bcascii": ForcingModel,
    "uniform": TimModel,
    "unimagdir": TimModel,
    "arcinfo": DiskOnlyFileModel,
    "spiderweb": DiskOnlyFileModel,
    "curvigrid": DiskOnlyFileModel,
    "netcdf": DiskOnlyFileModel,
    "polygon": PolyFile,
}


class Boundary(INIBasedModel):
    """A `[Boundary]` block for use inside an external forcings file.

    I.e., a [ExtModel][hydrolib.core.dflowfm.ext.models.ExtModel].

    All lowercased attributes match with the boundary input as described in
    [UM Sec.C.5.2.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.1).
    """

    _header: Literal["Boundary"] = "Boundary"
    quantity: str = Field(alias="quantity")
    nodeid: Optional[str] = Field(None, alias="nodeId")
    locationfile: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(None), alias="locationFile")
    forcingfile: ForcingModel = Field(alias="forcingFile")
    bndwidth1d: Optional[float] = Field(None, alias="bndWidth1D")
    bndbldepth: Optional[float] = Field(None, alias="bndBlDepth")
    returntime: Optional[float] = Field(None, alias="returnTime")

    def is_intermediate_link(self) -> bool:
        return True

    @field_validator("forcingfile", mode="before")
    @classmethod
    def validate_forcingfile(cls, data: Any) -> Any:
        if isinstance(data, (str, Path)):
            data = ForcingModel(filepath=data)
        elif not isinstance(data, ForcingModel):
            raise TypeError(
                "Forcing file must be a ForcingModel or a path to a forcing file."
            )
        return data

    @classmethod
    def _is_valid_locationfile_data(
        cls, elem: Union[None, str, Path, DiskOnlyFileModel]
    ) -> bool:
        return isinstance(elem, Path) or (
            isinstance(elem, DiskOnlyFileModel) and elem.filepath is not None
        )

    @classmethod
    def _exclude_from_validation(cls, input_data: Optional[dict] = None) -> Set:
        unknown_keywords = ["return_time"]
        return set(unknown_keywords)

    @model_validator(mode="before")
    @classmethod
    def rename_return_time_field(cls, values: Dict) -> Dict:
        """Renames the deprecated return_time field to returnTime.

        Args:
            values (Dict): Dictionary with raw, unvalidated input values.

        Returns:
            Dict: Validated dictionary of values for Boundary.
        """
        if "return_time" in values:
            values["returnTime"] = values.pop("return_time")
        return values

    @model_validator(mode="before")
    @classmethod
    def check_nodeid_or_locationfile_present(cls, values: Dict) -> Dict:
        """Verifies that either nodeid or locationfile properties have been set.

        Args:
            values (Dict): Dictionary with values already validated.

        Raises:
            ValueError: When none of the values are present.

        Returns:
            Dict: Validated dictionary of values for Boundary.
        """
        node_id = values.get("nodeid")
        location_file = values.get("locationfile")
        if str_is_empty_or_none(node_id) and not cls._is_valid_locationfile_data(
            location_file
        ):
            raise ValueError(
                "Either nodeId or locationFile fields should be specified."
            )
        return values

    def _get_identifier(self, data: dict) -> Optional[str]:
        """
        Retrieves the identifier for a boundary, which is the nodeid.

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
            ForcingBase: The corresponding forcing data, or None when no matching forcing block is found.
        """
        result = None
        for forcing in self.forcingfile.forcing:
            if self.nodeid == forcing.name and any(
                quantity.quantity.startswith(self.quantity)
                for quantity in forcing.quantityunitpair
            ):
                result = forcing
                break

        return result

    @model_validator(mode="before")
    @classmethod
    def validate_locationfile(cls, data: Any) -> Any:
        file_location = data.get("locationfile") or data.get("locationFile")
        data.pop("locationFile", None)  # Remove alias if present

        # Convert string to DiskOnlyFileModel if needed
        if isinstance(file_location, (str, Path)):
            data["locationfile"] = DiskOnlyFileModel(file_location)
        return data


class Lateral(INIBasedModel):
    """A `[Lateral]` block for use inside an external forcings file.

    I.e., a [ExtModel][hydrolib.core.dflowfm.ext.models.ExtModel].

    All lowercased attributes match with the lateral input as described in
    [UM Sec.C.5.2.2](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.2).
    """

    _header: Literal["Lateral"] = "Lateral"
    id: str = Field(alias="id")
    name: str = Field("", alias="name")
    locationtype: Optional[str] = Field(None, alias="locationType")
    nodeid: Optional[str] = Field(None, alias="nodeId")
    branchid: Optional[str] = Field(None, alias="branchId")
    chainage: Optional[float] = Field(None, alias="chainage")
    numcoordinates: Optional[int] = Field(None, alias="numCoordinates")
    xcoordinates: Optional[List[float]] = Field(None, alias="xCoordinates")
    ycoordinates: Optional[List[float]] = Field(None, alias="yCoordinates")
    discharge: ForcingData = Field(alias="discharge")

    def is_intermediate_link(self) -> bool:
        return True

    @field_validator("xcoordinates", "ycoordinates", mode="before")
    @classmethod
    def split_coordinates(cls, v, info: ValidationInfo) -> List[float]:
        return split_string_on_delimiter(cls, v, info)

    @field_validator("discharge", mode="before")
    @classmethod
    def validate_discharge(cls, v):
        return _resolve_forcing_data(v)

    @model_validator(mode="before")
    def validate_that_location_specification_is_correct(cls, values: Dict) -> Dict:
        """Validates that the correct location specification is given."""
        return validate_location_specification(
            values, config=LocationValidationConfiguration(minimum_num_coordinates=1)
        )

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("id") or data.get("name")

    @field_validator("locationtype", mode="before")
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
    """A `[SourceSink]` block for use inside an external forcings file.

    I.e., a [ExtModel][hydrolib.core.dflowfm.ext.models.SourceSink].

    All lowercased attributes match with the source-sink input as described in
    [UM Sec.C.5.2.4](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.4).
    """

    _header: Literal["SourceSink"] = "SourceSink"
    id: str = Field(alias="id")
    name: str = Field("", alias="name")
    locationfile: Optional[DiskOnlyFileModel] = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="locationFile"
    )

    numcoordinates: Optional[int] = Field(None, alias="numCoordinates")
    xcoordinates: Optional[List[float]] = Field(None, alias="xCoordinates")
    ycoordinates: Optional[List[float]] = Field(None, alias="yCoordinates")

    zsource: Optional[Union[float, List[float]]] = Field(None, alias="zSource")
    zsink: Optional[Union[float, List[float]]] = Field(None, alias="zSink")
    area: Optional[float] = Field(None, alias="Area")

    discharge: ForcingData = Field(alias="discharge")
    salinitydelta: Optional[ForcingData] = Field(None, alias="salinityDelta")
    temperaturedelta: Optional[ForcingData] = Field(None, alias="temperatureDelta")

    def is_intermediate_link(self) -> bool:
        return True

    @field_validator("xcoordinates", "ycoordinates", mode="before")
    @classmethod
    def split_coordinates(cls, v, info: ValidationInfo) -> List[float]:
        return split_string_on_delimiter(cls, v, info)

    @field_validator(
        "discharge", "salinitydelta", "temperaturedelta", mode="before"
    )
    @classmethod
    def validate_forcing_data(cls, v):
        return _resolve_forcing_data(v)

    @model_validator(mode="before")
    @classmethod
    def _resolve_dynamic_forcing_deltas(cls, values: Any) -> Any:
        """Apply `_resolve_forcing_data` to dynamic `tracer<...>Delta`/`sedFrac<...>Delta` keys.

        Per D-Flow FM User Manual Table C.8 (§C.6.2.4), `tracer<name>Delta` and
        `sedFrac<name>Delta` accept a scalar Double or the name of a `.bc`
        time-series file. The first-class `discharge`/`salinityDelta`/
        `temperatureDelta` fields are already handled by `validate_forcing_data`;
        this validator extends the same coercion to the dynamic Delta-suffix
        fields that arrive via `extra="allow"`.

        Legacy dynamic fields (`initialtracer_*`, `tracerbnd*`, `sedfracbnd_*`,
        `initialsedfrac_*`) do not end with `delta` and are left untouched.
        """
        if isinstance(values, dict):
            for key in list(values.keys()):
                if _is_dynamic_forcing_delta_key(key):
                    values[key] = _resolve_forcing_data(values[key])
        return values

    @classmethod
    def _exclude_from_validation(cls, input_data: Optional[dict] = None) -> Set:
        fields = cls.model_fields
        unknown_keywords = [
            key
            for key in input_data.keys()
            if key not in fields
            and (
                key.startswith(SOURCE_SINKS_QUANTITIES_VALID_PREFIXES)
                or _is_dynamic_forcing_delta_key(key)
            )
        ]
        return set(unknown_keywords)

    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        """Initialize SourceSink and set dynamic tracer attributes."""
        super().__init__(**data)
        # Add dynamic attributes for fields starting with 'tracer'
        for key, value in data.items():
            if isinstance(key, str) and key.startswith(
                SOURCE_SINKS_QUANTITIES_VALID_PREFIXES
            ):
                setattr(self, key, value)

    @model_validator(mode="before")
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
            and _coordinate_length(xcoordinates)
            == _coordinate_length(ycoordinates)
            == int(numcoordinates)
        )

        if not (has_locationfile or has_coordinates):
            raise ValueError(
                "Either `locationFile` or the combination of `numCoordinates`, `xCoordinates`, and `yCoordinates` "
                f"must be provided. for the SourceSink block `{values.get('id')}`."
            )

        return values

    @model_validator(mode="before")
    @classmethod
    def validate_locationfile(cls, data: Any) -> Any:
        file_location = data.get("locationfile") or data.get("locationFile")
        data.pop("locationFile", None)  # Remove alias if present

        # Convert string to DiskOnlyFileModel if needed
        if isinstance(file_location, (str, Path)):
            data["locationfile"] = DiskOnlyFileModel(file_location)
        else:
            data["locationfile"] = file_location
        return data


class MeteoForcingFileType(StrEnum):
    """Enum class containing the valid values for the forcingFileType attribute in Meteo class."""

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

    polygon = "polygon"
    """str: Polygon-based time series in <*.pol> file."""

    allowedvaluestext = "Possible values: bcAscii, uniform, uniMagDir, arcInfo, spiderweb, curviGrid, netcdf, polygon."


class MeteoInterpolationMethod(StrEnum):
    """Enum class containing the valid values for the interpolationMethod attribute in Meteo class."""

    nearestnb = "nearestNb"
    """str: Nearest-neighbour interpolation, only with station-data in forcingFileType=netcdf"""
    linearSpaceTime = "linearSpaceTime"
    """str: Linear interpolation in space and time."""
    constant = "constant"
    allowedvaluestext = "Possible values: nearestNb, linearSpaceTime, constant."


class Meteo(INIBasedModel):
    """A `[Meteo]` block for use inside an external forcings file.

    I.e., a [ExtModel][hydrolib.core.dflowfm.ext.models.ExtModel].

    All lowercased attributes match with the meteo input as described in
    [UM Sec.C.5.2.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.3).
    """

    class Comments(INIBasedModel.Comments):
        """Comments for the Meteo block fields."""

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
        forcingvariablename: Optional[str] = Field(
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
        extrapolationallowed: Optional[str] = Field(
            "Optionally allow nearest neighbour extrapolation in space (0: no, 1: yes). Default off.",
            alias="extrapolationAllowed",
        )
        extrapolationsearchradius: Optional[str] = Field(
            "Maximum search radius for nearest neighbor extrapolation in space.",
            alias="extrapolationSearchRadius",
        )

    comments: Comments = Comments()

    @classmethod
    def _get_unknown_keyword_error_manager(cls) -> Optional[UnknownKeywordErrorManager]:
        """The Meteo does not currently support raising an error on unknown keywords."""
        return None

    _header: Literal["Meteo"] = "Meteo"
    quantity: str = Field(alias="quantity")
    forcingfile: Union[TimModel, ForcingModel, DiskOnlyFileModel, PolyFile] = Field(
        alias="forcingFile"
    )
    forcingvariablename: Optional[str] = Field(None, alias="forcingVariableName")
    forcingfiletype: MeteoForcingFileType = Field(alias="forcingFileType")
    targetmaskfile: Optional[PolyFile] = Field(None, alias="targetMaskFile")
    targetmaskinvert: Optional[bool] = Field(None, alias="targetMaskInvert")
    interpolationmethod: Optional[MeteoInterpolationMethod] = Field(
        None, alias="interpolationMethod"
    )
    operand: Optional[Operand] = Field(Operand.override.value, alias="operand")
    extrapolationallowed: Optional[bool] = Field(None, alias="extrapolationAllowed")
    extrapolationsearchradius: Optional[float] = Field(
        None, alias="extrapolationSearchRadius"
    )
    averagingtype: Optional[int] = Field(None, alias="averagingType")
    averagingnummin: Optional[float] = Field(None, alias="averagingNumMin")
    averagingpercentile: Optional[float] = Field(None, alias="averagingPercentile")

    # Deprecated camelCase aliases — intentional case clash with the fields above; remove in 2.0.0 (docs/migration.md).
    forcingVariableName = DeprecatedAttributeAlias(  # NOSONAR S1845
        "forcingvariablename", removed_in="2.0.0", since="1.1.0"
    )
    extrapolationAllowed = DeprecatedAttributeAlias(  # NOSONAR S1845
        "extrapolationallowed", removed_in="2.0.0", since="1.1.0"
    )
    extrapolationSearchRadius = DeprecatedAttributeAlias(  # NOSONAR S1845
        "extrapolationsearchradius", removed_in="2.0.0", since="1.1.0"
    )
    averagingType = DeprecatedAttributeAlias(  # NOSONAR S1845
        "averagingtype", removed_in="2.0.0", since="1.1.0"
    )
    averagingNumMin = DeprecatedAttributeAlias(  # NOSONAR S1845
        "averagingnummin", removed_in="2.0.0", since="1.1.0"
    )
    averagingPercentile = DeprecatedAttributeAlias(  # NOSONAR S1845
        "averagingpercentile", removed_in="2.0.0", since="1.1.0"
    )

    @model_validator(mode="before")
    @classmethod
    def choose_file_model(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Root-level validator to the right class for the filename parameter based on the filetype.

        The validator chooses the right class for the filename parameter based on the FileType_FileModel_mapping
        dictionary.

        FILETYPE_FILEMODEL_MAPPING = {
            "bcascii": ForcingModel,
            "uniform": TimModel,
            "unimagdir": TimModel,
            "arcinfo": DiskOnlyFileModel,
            "spiderweb": DiskOnlyFileModel,
            "curvigrid": DiskOnlyFileModel,
            "netcdf": DiskOnlyFileModel,
            "polygon": PolyFile,
        }
        """
        # if the filetype and the filename are present in the values
        if any(par in values for par in ["forcingfiletype", "forcingFileType"]) and any(
            par in values for par in ["forcingfile", "forcingFile"]
        ):
            file_type_var_name = (
                "forcingfiletype" if "forcingfiletype" in values else "forcingFileType"
            )
            filename_var_name = (
                "forcingfile" if "forcingfile" in values else "forcingFile"
            )
            file_type = values.get(file_type_var_name)
            file_type = str(file_type).lower() if file_type is not None else None
            raw_path = values.get(filename_var_name)
            if isinstance(raw_path, (Path, str)):
                model = FILETYPE_FILEMODEL_MAPPING.get(file_type)
                values[filename_var_name] = resolve_file_model(raw_path, model)

        return values

    def is_intermediate_link(self) -> bool:
        return True

    @field_validator("forcingfiletype", mode="before")
    @classmethod
    def forcingfiletype_validator(cls, v):
        return enum_value_parser(v, MeteoForcingFileType)

    @field_validator("interpolationmethod", mode="before")
    @classmethod
    def interpolationmethod_validator(cls, v):
        return enum_value_parser(v, MeteoInterpolationMethod)


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
    boundary: Annotated[List[Boundary], BeforeValidator(make_list)] = Field(
        default_factory=list
    )
    lateral: Annotated[List[Lateral], BeforeValidator(make_list)] = Field(
        default_factory=list
    )
    sourcesink: Annotated[List[SourceSink], BeforeValidator(make_list)] = Field(
        default_factory=list
    )
    meteo: Annotated[List[Meteo], BeforeValidator(make_list)] = Field(
        default_factory=list
    )
    serializer_config: INISerializerConfig = INISerializerConfig(
        section_indent=0, property_indent=0
    )

    @classmethod
    def _ext(cls) -> str:
        return ".ext"

    @classmethod
    def _filename(cls) -> str:
        return "bnd"


class SourceSinkError(Exception):
    """SourceSinkError."""

    def __init__(self, error_message: str):
        """Initialize with an error message."""
        super().__init__(error_message)


class InitialFieldError(Exception):
    """InitialFieldError."""

    def __init__(self, error_message: str):
        """Initialize with an error message."""
        super().__init__(error_message)


class MeteoError(Exception):
    """MeteoError."""

    def __init__(self, error_message: str):
        """Initialize with an error message."""
        super().__init__(error_message)


class BoundaryError(Exception):
    """BoundaryError."""

    def __init__(self, error_message: str):
        """Initialize with an error message."""
        super().__init__(error_message)


class ParameterFieldError(Exception):
    """ParameterFieldError."""

    def __init__(self, error_message: str):
        """Initialize with an error message."""
        super().__init__(error_message)
