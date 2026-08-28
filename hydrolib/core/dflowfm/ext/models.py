"""Models for the external forcings file (new format) of D-Flow FM."""

import warnings
from abc import ABC
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
from pydantic.types import NonNegativeFloat, PositiveInt
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
from hydrolib.core.dflowfm.common.models import LocationType, Operand
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
from hydrolib.core.dflowfm.inifield.models import (
    AveragingType,
    OperandInterpolationValidators,
    DataFileType,
    InterpolationMethod,
    LocationTypeDataFileTypeValidators,
)
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.tim.models import TimModel

# Deprecated aliases — MeteoForcingFileType and MeteoInterpolationMethod are merged
# into DataFileType and InterpolationMethod respectively. These aliases remain for
# backward compatibility and will be removed in a future release.
MeteoForcingFileType = DataFileType
MeteoInterpolationMethod = InterpolationMethod

SOURCE_SINKS_QUANTITIES_VALID_PREFIXES = (
    "initialtracer",
    "tracerbnd",
    "sedfracbnd",
    "initialsedfrac"
)
# Reserved key used to thread the caller-provided `dynamic_fields` list through
# Pydantic validation (via `SourceSink.__init__`) so `_exclude_from_validation`
# can whitelist those names. It is stripped from the instance after init.
_DYNAMIC_FIELDS_KEY = "__dynamic_fields__"
SOURCE_SINKS_IGNORE_QUANTITIES_PREFIXES = (
    "initialtracer",
    "initialsedfrac"
)

class TargetLayer(StrEnum):
    """Valid non-numeric values for the ``targetLayer`` attribute of a `[Spatial]` block.

    Corresponds to the ``LAYER`` value in the old external forcings file: ``bottom``
    (old ``-1``) and ``all`` (old ``0``). A positive integer layer number is also
    accepted; see ``Spatial.targetlayer``.
    """

    bottom = "bottom"
    all = "all"


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
        result = lowered.endswith("delta") and lowered.startswith(("tracer", "sedfrac"))
    return result


def _resolve_forcing_data(
    v: Any, *, allow_realtime: bool = True
) -> float | RealTime | ForcingModel | None | DiskOnlyFileModel:
    """Coerce a raw value into a `ForcingData` member (float, RealTime, ForcingModel, or DiskOnlyFileModel).

    A string is tried as a float, then as the `RealTime` enum (case-insensitive),
    and finally resolved as a path to a `.bc` forcing file. A `Path` is always
    resolved as a forcing file. A `dict` is instantiated as a `ForcingModel`.
    Any other value (including `None`) is passed through unchanged so that
    Optional fields and already-validated values still work.

    When the active file-load context has ``recurse=False``, the path resolution
    step returns a ``DiskOnlyFileModel`` instead of fully parsing the `.bc` file
    into a ``ForcingModel``. This lightweight placeholder avoids expensive I/O
    during non-recursive loads while still satisfying the ``ForcingData`` type
    annotation. An ``AfterValidator`` on ``ForcingData`` ensures that a
    ``DiskOnlyFileModel`` can never slip through under a recursive load
    (``recurse=True``), where the `.bc` file is expected to be fully parsed.

    Args:
        v: The raw value to coerce.
        allow_realtime: When `False`, the `realtime` keyword is rejected with a
            `ValueError` instead of mapped to `RealTime.realtime`. The
            D-Flow FM User Manual Table C.8 (§C.6.2.4) states that
            `realtime` is "not (yet) available for sediment fractions and
            tracers", so callers handling `tracer<...>Delta` /
            `sedFrac<...>Delta` keys should pass `allow_realtime=False`.

    Returns:
        float | RealTime | ForcingModel | DiskOnlyFileModel | None:
            The resolved forcing data value. ``DiskOnlyFileModel`` is returned
            only when ``recurse=False`` in the active file-load context.

    Raises:
        ValueError: When `v` is the `realtime` keyword (any case) and
            `allow_realtime=False`.

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
                realtime_match = RealTime(v.lower())
            except ValueError:
                result = resolve_file_model(v, ForcingModel)
            else:
                if not allow_realtime:
                    raise ValueError(
                        "The 'realtime' keyword is not supported for this field. "
                        "Per D-Flow FM User Manual Table C.8 (§C.6.2.4), realtime "
                        "is not (yet) available for sediment fractions and tracers."
                    )
                result = realtime_match
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
    nodeid: str | None = Field(None, alias="nodeId")
    locationfile: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(None), alias="locationFile")
    forcingfile: ForcingModel = Field(alias="forcingFile")
    bndwidth1d: float | None = Field(None, alias="bndWidth1D")
    bndbldepth: float | None = Field(None, alias="bndBlDepth")
    returntime: float | None = Field(None, alias="returnTime")
    operand: Operand | None = Field(None, alias="operand")

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

    @field_validator("operand", mode="before")
    @classmethod
    def validate_operand(cls, v: Any):
        return enum_value_parser(v, Operand, Operand.legacy_alternatives())


def _is_non_null_location_file(raw: Any) -> bool:
    """Return True when *raw* represents a non-null locationFile value.

    Accepts a ``Path``, a non-empty ``str``, or a ``DiskOnlyFileModel``-style
    dict whose ``filepath`` key is not *None*.  Returns False for *None*, an
    empty string, or a dict with ``filepath=None``.
    """
    if raw is None:
        return False
    if isinstance(raw, str):
        return raw.strip() != ""
    if isinstance(raw, Path):
        return True
    if isinstance(raw, dict):
        return raw.get("filepath") is not None
    # DiskOnlyFileModel instance
    if hasattr(raw, "filepath"):
        return raw.filepath is not None
    return False


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
    locationfile: Optional[
        Annotated[DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)]
    ] = Field(None, alias="locationFile")
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
        """Validates that the correct location specification is given.

        A ``locationFile`` referencing a polygon file is accepted as a complete
        location specification on its own (no coordinates or nodeId/branchId needed).
        All other combinations are validated by the generic
        :func:`validate_location_specification` helper.
        """
        # A non-null locationFile is a self-contained location specification.
        # raw_loc_file = values.get("locationfile") or values.get("locationFile")
        # if _is_non_null_location_file(raw_loc_file):
        #     return values

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
    model_config = ConfigDict(extra="allow")

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
    salinity: Optional[ForcingData] = Field(None, alias="salinity")
    temperature: Optional[ForcingData] = Field(None, alias="temperature")

    def is_intermediate_link(self) -> bool:
        return True

    @field_validator("xcoordinates", "ycoordinates", mode="before")
    @classmethod
    def split_coordinates(cls, v, info: ValidationInfo) -> List[float]:
        return split_string_on_delimiter(cls, v, info)

    @field_validator(
        "discharge", "salinity", "temperature", mode="before"
    )
    @classmethod
    def validate_forcing_data(cls, v):
        return _resolve_forcing_data(v)

    @model_validator(mode="before")
    @classmethod
    def _resolve_dynamic_forcing_deltas(cls, values: Any) -> Any:
        """Apply `_resolve_forcing_data` to dynamic `tracer<...>Delta`/`sedFrac<...>Delta` keys.

        Also renames legacy `salinitydelta`/`temperaturedelta` keys (produced by
        the INI parser from old-format `salinityDelta`/`temperatureDelta`) to the
        current field names `salinity`/`temperature` for backward compatibility.

        Per D-Flow FM User Manual Table C.8 (§C.6.2.4), `tracer<name>Delta` and
        `sedFrac<name>Delta` accept a scalar Double or the name of a `.bc`
        time-series file. The first-class `discharge`/`salinity`/
        `temperature` fields are already handled by `validate_forcing_data`;
        this validator extends the same coercion to the dynamic Delta-suffix
        fields that arrive via `extra="allow"`.

        Legacy dynamic fields (`initialtracer_*`, `tracerbnd*`, `sedfracbnd_*`,
        `initialsedfrac_*`) do not end with `delta` and are left untouched.
        """
        if isinstance(values, dict):
            # Migrate legacy salinityDelta/temperatureDelta keys (any casing) from old-format ext files.
            lowercase_map = {k.lower(): k for k in values}
            if "salinitydelta" in lowercase_map and "salinity" not in values:
                values["salinity"] = values.pop(lowercase_map["salinitydelta"])
            if "temperaturedelta" in lowercase_map and "temperature" not in values:
                values["temperature"] = values.pop(lowercase_map["temperaturedelta"])
            for key in values:
                if _is_dynamic_forcing_delta_key(key):
                    values[key] = _resolve_forcing_data(
                        values[key], allow_realtime=False
                    )
        return values

    @classmethod
    def _exclude_from_validation(cls, input_data: dict | None = None) -> Set:
        input_data = input_data or {}
        fields = cls.model_fields
        dynamic_fields = input_data.get(_DYNAMIC_FIELDS_KEY) or []
        unknown_keywords = [
            key
            for key in input_data.keys()
            if key not in fields
            and (
                key.startswith(SOURCE_SINKS_QUANTITIES_VALID_PREFIXES)
                or _is_dynamic_forcing_delta_key(key)
                or key in dynamic_fields
                or key == _DYNAMIC_FIELDS_KEY
            )
        ]
        return set(unknown_keywords)

    def __init__(self, dynamic_fields: Optional[List[str]] = None, **data):
        """Initialize SourceSink and set dynamic fields as instance attributes.

        When `dynamic_fields` is provided, exactly those names (whose values are passed
        in `data`) are attached onto this instance. When it is omitted, the legacy
        behaviour applies: every key in `data` that starts with one of
        `SOURCE_SINKS_QUANTITIES_VALID_PREFIXES` is attached. In both cases the values
        are stored as-is on the instance (in `model_extra`); no coercion is applied yet.
        Args:
            dynamic_fields: Names of extra fields (whose values are passed in `data`)
                to attach onto this instance. If `None`, the prefix-based detection is
                used instead.
            **data: The regular SourceSink field values, plus the values for any dynamic
                fields.
        """
        # Thread the dynamic field names through validation so that
        # `_exclude_from_validation` can whitelist them as known keywords.
        if dynamic_fields is not None:
            data[_DYNAMIC_FIELDS_KEY] = list(dynamic_fields)

        super().__init__(**data)

        # Drop the reserved key so it does not linger as an instance attribute.
        if self.__pydantic_extra__ is not None:
            self.__pydantic_extra__.pop(_DYNAMIC_FIELDS_KEY, None)

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


class SpatialForcingBase(OperandInterpolationValidators, INIBasedModel, ABC):
    """Shared behaviour for the `[Meteo]` and `[Spatial]` external-forcing blocks.

    `Meteo` (legacy) and `Spatial` (its successor) share the same data-file model
    resolution logic and unknown-keyword handling. This abstract base holds that
    common behaviour so a single fix applies to both.

    The `operand` / `interpolationMethod` validators are inherited from
    `OperandInterpolationValidators` (common to all four spatial-field blocks). `Spatial`
    additionally inherits `LocationTypeDataFileTypeValidators` for the `locationType` /
    `dataFileType` validators it shares with the inifield blocks; `Meteo` does not,
    as it has neither field.

    Field declarations remain on the concrete subclasses: their keyword names
    differ (`forcing*` versus `data*`) and their serialization order must be
    preserved, so only behaviour (not fields) is hoisted here.
    """

    class Comments(INIBasedModel.Comments):
        """Comments shared by the `[Meteo]` and `[Spatial]` block fields.

        Only the descriptions that are identical in both blocks live here. The
        file-specific ones (`forcingFile`/`dataFile`, `extrapolationSearchRadius`)
        stay on the subclasses because their wording differs.
        """

        quantity: Optional[str] = Field(
            "Name of the quantity. See UM Section C.5.3", alias="quantity"
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

    @classmethod
    def _get_unknown_keyword_error_manager(cls) -> Optional[UnknownKeywordErrorManager]:
        """Neither block currently raises an error on unknown keywords."""
        return None

    @staticmethod
    def _resolve_file_models(
        values: Dict[str, Any], file_keys: tuple, type_keys: tuple
    ) -> Dict[str, Any]:
        """Select the concrete file model for the data/forcing file from its type.

        Mirrors the historical per-class ``choose_file_model`` bodies: when both a
        file keyword and its type keyword are present and the file is still a raw
        path, the path is resolved into the model class from
        ``FILETYPE_FILEMODEL_MAPPING`` (types not in the mapping fall back to
        ``DiskOnlyFileModel``).

        Args:
            values: Raw, unvalidated input values for the block.
            file_keys: The lowercase and camelCase names of the file keyword,
                e.g. ``("datafile", "dataFile")``.
            type_keys: The lowercase and camelCase names of the file-type keyword,
                e.g. ``("datafiletype", "dataFileType")``.

        Returns:
            Dict[str, Any]: The (possibly updated) values dictionary.
        """
        if any(key in values for key in type_keys) and any(
            key in values for key in file_keys
        ):
            type_key = type_keys[0] if type_keys[0] in values else type_keys[1]
            file_key = file_keys[0] if file_keys[0] in values else file_keys[1]

            file_type = values.get(type_key)
            file_type = str(file_type).lower() if file_type is not None else None

            raw_path = values.get(file_key)
            if isinstance(raw_path, (Path, str)):
                model = FILETYPE_FILEMODEL_MAPPING.get(file_type)
                if model is None:
                    values[file_key] = DiskOnlyFileModel(raw_path)
                else:
                    values[file_key] = resolve_file_model(raw_path, model)

        return values


class Meteo(SpatialForcingBase):
    """A `[Meteo]` block for use inside an external forcings file.

    I.e., a [ExtModel][hydrolib.core.dflowfm.ext.models.ExtModel].

    All lowercased attributes match with the meteo input as described in
    [UM Sec.C.5.2.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.3).
    """

    class Comments(SpatialForcingBase.Comments):
        """Comments for the Meteo block fields.

        Inherits the shared descriptions from `SpatialForcingBase.Comments`; only
        the `forcing*` file keywords and the `extrapolationSearchRadius` wording are
        specific to this block.
        """

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
        extrapolationsearchradius: Optional[str] = Field(
            "Maximum search radius for nearest neighbor extrapolation in space.",
            alias="extrapolationSearchRadius",
        )

    comments: Comments = Comments()

    _header: Literal["Meteo"] = "Meteo"
    quantity: str = Field(alias="quantity")
    forcingfile: Union[TimModel, ForcingModel, DiskOnlyFileModel, PolyFile] = Field(
        alias="forcingFile"
    )
    forcingvariablename: str | None = Field(None, alias="forcingVariableName")
    forcingfiletype: MeteoForcingFileType = Field(alias="forcingFileType")
    targetmaskfile: PolyFile | None = Field(None, alias="targetMaskFile")
    targetmaskinvert: bool | None = Field(None, alias="targetMaskInvert")
    interpolationmethod: MeteoInterpolationMethod | None = Field(
        None, alias="interpolationMethod"
    )
    operand: Operand | None = Field(Operand.override.value, alias="operand")
    extrapolationallowed: bool | None = Field(None, alias="extrapolationAllowed")
    extrapolationsearchradius: float | None = Field(
        None, alias="extrapolationSearchRadius"
    )
    averagingtype: int | None = Field(None, alias="averagingType")
    averagingnummin: PositiveInt | None = Field(None, alias="averagingNumMin")
    averagingpercentile: float | None = Field(None, alias="averagingPercentile")

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
        """Select the right class for the forcingFile parameter based on forcingFileType.

        Uses the shared ``SpatialForcingBase._resolve_file_models`` helper against
        this block's ``forcingFile``/``forcingFileType`` keywords.
        """
        return cls._resolve_file_models(
            values,
            ("forcingfile", "forcingFile"),
            ("forcingfiletype", "forcingFileType"),
        )

    def is_intermediate_link(self) -> bool:
        return True

    @field_validator("forcingfiletype", mode="before")
    @classmethod
    def forcingfiletype_validator(cls, v):
        return enum_value_parser(v, MeteoForcingFileType)


class Spatial(SpatialForcingBase, LocationTypeDataFileTypeValidators):
    """A `[Spatial]` block for use inside an external forcings file.

    I.e., a [ExtModel][hydrolib.core.dflowfm.ext.models.ExtModel].

    This block replaces both the legacy `[Meteo]` block (for meteorological
    forcings) and the `[Initial]` / `[Parameter]` blocks in inifield files
    (for initial conditions and spatial parameters).

    All lowercased attributes match with the spatial input as described in
    [UM Sec.C.5.2.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.3).
    """

    class Comments(SpatialForcingBase.Comments):
        """Comments for the Spatial block fields.

        Inherits the shared descriptions from `SpatialForcingBase.Comments`; only
        the `data*` file keywords, the `extrapolationSearchRadius` wording, and the
        fields unique to the Spatial block are declared here.
        """

        datafile: str | None = Field(
            "Name of file containing the data for this spatial quantity.",
            alias="dataFile",
        )
        datafiletype: str | None = Field(
            "Type of dataFile.", alias="dataFileType"
        )
        datavariablename: str | None = Field(
            "Variable name used in dataFile associated with this quantity.",
            alias="dataVariableName",
        )
        targetmaskfile: str | None = Field(
            "Name of <*.pol> file to be used as mask. Grid parts inside any polygon will receive the spatial forcing.",
            alias="targetMaskFile",
        )
        extrapolationsearchradius: str | None = Field(
            "Maximum search radius for nearest neighbour extrapolation in space.",
            alias="extrapolationSearchRadius",
        )
        averagingtype: str | None = Field(
            "Type of averaging, if interpolationMethod=averaging.",
            alias="averagingType",
        )
        averagingrelsize: str | None = Field(
            "Relative search cell size for averaging.", alias="averagingRelSize"
        )
        averagingnummin: str | None = Field(
            "Minimum number of points in averaging. Must be ≥ 1.",
            alias="averagingNumMin",
        )
        averagingpercentile: str | None = Field(
            "Percentile value for which data values to include in averaging. 0.0 means off.",
            alias="averagingPercentile",
        )
        locationtype: str | None = Field(
            "Target location of interpolation.", alias="locationType"
        )
        datavalue: str | None = Field(
            "Constant value to be set inside all model points inside the polygon, "
            "used when no dataFile/dataFileType is specified. "
            "Requires targetMaskFile=*.pol and interpolationMethod=constant.",
            alias="dataValue",
        )
        frictiontype: str | None = Field(
            "Only for quantity=frictionCoefficient. The friction type.", alias="frictionType"
        )
        tracerfallvelocity: str | None = Field(
            "Only for initialtracer<tracername>. Fall velocity of the tracer.",
            alias="tracerFallVelocity",
        )
        tracerdecaytime: str | None = Field(
            "Only for initialtracer<tracername>. Decay time of the tracer.",
            alias="tracerDecayTime",
        )
        targetlayer: str | None = Field(
            "Target layer for the data: bottom, all, or a positive layer number.",
            alias="targetLayer",
        )

    comments: Comments = Comments()

    _header: Literal["Spatial"] = "Spatial"
    quantity: str = Field(alias="quantity")
    datafile: TimModel | ForcingModel | DiskOnlyFileModel | PolyFile | None = Field(
        None, alias="dataFile"
    )
    datafiletype: DataFileType | None = Field(None, alias="dataFileType")
    datavariablename: str | None = Field(None, alias="dataVariableName")
    targetmaskfile: PolyFile | DiskOnlyFileModel | None = Field(None, alias="targetMaskFile")
    targetmaskinvert: bool | None = Field(None, alias="targetMaskInvert")
    interpolationmethod: InterpolationMethod | None = Field(
        None, alias="interpolationMethod"
    )
    operand: Operand | None = Field(Operand.override.value, alias="operand")
    extrapolationallowed: bool | None = Field(False, alias="extrapolationAllowed")
    extrapolationsearchradius: float | None = Field(
        None, alias="extrapolationSearchRadius"
    )
    averagingtype: AveragingType | None = Field(None, alias="averagingType")
    averagingrelsize: NonNegativeFloat | None = Field(None, alias="averagingRelSize")
    averagingnummin: PositiveInt | None = Field(None, alias="averagingNumMin")
    averagingpercentile: NonNegativeFloat | None = Field(None, alias="averagingPercentile")
    locationtype: LocationType | None = Field(
        LocationType.all.value, alias="locationType"
    )
    datavalue: float | None = Field(None, alias="dataValue")
    frictiontype: str | None = Field(None, alias="frictionType")
    tracerfallvelocity: float | None = Field(None, alias="tracerFallVelocity")
    tracerdecaytime: float | None = Field(None, alias="tracerDecayTime")
    targetlayer: TargetLayer | int | None = Field(None, alias="targetLayer")

    @classmethod
    def _normalize_spatial_keys(cls, values: Dict) -> Dict:
        """Normalize camelCase aliases and coerce any unresolved datafile to DiskOnlyFileModel.

        ``dataFile`` is normally resolved to its concrete file model earlier in the
        validation flow (see ``_resolve_file_models``). This fallback only wraps a
        path that is still raw (e.g. no ``dataFileType`` was supplied) so that the
        field always holds a file model rather than a bare string.
        """
        data_file = values.get("datafile") or values.get("dataFile")
        if isinstance(data_file, (str, Path)):
            data_file = DiskOnlyFileModel(data_file)
            values.pop("dataFile", None)
            values["datafile"] = data_file

        if "dataValue" in values and "datavalue" not in values:
            values["datavalue"] = values.pop("dataValue")
        if "targetMaskFile" in values and "targetmaskfile" not in values:
            values["targetmaskfile"] = values.pop("targetMaskFile")
        return values

    @classmethod
    def _validate_datavalue_path(
        cls, values: Dict, has_datafile: bool, has_datafiletype: bool
    ) -> None:
        """Validate the ``dataValue`` usage path (constant value inside polygon)."""
        if has_datafile or has_datafiletype:
            raise ValueError(
                "When 'dataValue' is provided, 'dataFile' and 'dataFileType' must not be specified."
            )
        interp = values.get("interpolationmethod") or values.get("interpolationMethod")
        if interp is None:
            values["interpolationmethod"] = InterpolationMethod.constant
        elif str(interp).lower() != str(InterpolationMethod.constant).lower():
            raise ValueError(
                f"When 'dataValue' is provided, 'interpolationMethod' must be "
                f"'{InterpolationMethod.constant}', got '{interp}'."
            )

    @classmethod
    def _validate_datafile_path(
        cls, values: Dict, has_datafile: bool, has_datafiletype: bool
    ) -> None:
        """Validate the ``dataFile`` usage path and emit deprecation warning when needed."""
        if not has_datafile:
            raise ValueError("'dataFile' is required when 'dataValue' is not specified.")
        if not has_datafiletype:
            raise ValueError("'dataFileType' is required when 'dataValue' is not specified.")

        raw_filetype = values.get("datafiletype") or values.get("dataFileType")
        quantity = values.get("quantity") or ""
        if (
            raw_filetype is not None
            and str(raw_filetype).lower() == DataFileType.polygon
            and not str(quantity).startswith("initialvertical")
        ):
            warnings.warn(
                "Using dataFileType=polygon for 'inside polygon' data is deprecated. "
                "Use dataValue + targetMaskFile=<*.pol> + interpolationMethod=constant instead. "
                "The polygon dataFileType remains supported only for initialvertical* quantities "
                "(e.g. initialverticalsalinityprofile).",
                DeprecationWarning,
                stacklevel=2,
            )

    @classmethod
    def _process_section_values(cls, values):
        """Flatten a Section object into a dictionary of raw values.

        The raw ``dataFile`` value is left as a path/string so that the subsequent
        ``_resolve_file_models`` step can select the concrete file model from
        ``dataFileType`` (rather than being forced to ``DiskOnlyFileModel`` here).

        Args:
            values: The values to process, which may be a Section object or a dictionary.

        Returns:
            A dictionary containing the processed values.
        """
        return cls._convert_section_to_dict(values)

    @model_validator(mode="before")
    @classmethod
    def validate_datavalue_or_datafile(cls, values: Dict) -> Dict:
        """Validates the two mutually exclusive usage paths of a Spatial block.

        When ``dataValue`` is provided the block describes a constant value applied
        inside a polygon mask.  In this mode:
        - ``dataFile`` and ``dataFileType`` must **not** be specified.
        - ``targetMaskFile`` (a ``.pol`` file) is optional but often used.
        - ``interpolationMethod`` must be ``constant`` (set automatically when omitted).

        When ``dataValue`` is absent, ``dataFile`` and ``dataFileType`` are both
        required.

        Note: using ``dataFileType=polygon`` for "inside polygon" initial-condition
        data is **deprecated**.  Use ``dataValue`` + ``targetMaskFile=*.pol`` +
        ``interpolationMethod=constant`` instead.  The ``polygon`` dataFileType
        remains supported for quantities such as ``initialvertical*`` (e.g.
        ``initialverticalsalinityprofile``) that use polygon files for a different
        purpose and have no new alternative yet.

        The data file is resolved to its concrete file model only on the ``dataFile``
        path (``dataValue`` absent). This prevents an invalid combination
        (``dataValue`` together with ``dataFile``) from parsing a file before the
        mutual-exclusion check rejects it, so callers get the exclusion error rather
        than a file-parse error.
        """
        values = cls._process_section_values(values)

        on_datavalue_path = (
            values.get("datavalue") is not None or values.get("dataValue") is not None
        )
        if not on_datavalue_path:
            values = cls._resolve_file_models(
                values,
                ("datafile", "dataFile"),
                ("datafiletype", "dataFileType"),
            )

        values = cls._normalize_spatial_keys(values)

        datavalue = values.get("datavalue")
        has_datafile = (values.get("datafile") or values.get("dataFile")) is not None
        has_datafiletype = (values.get("datafiletype") or values.get("dataFileType")) is not None

        if datavalue is not None:
            cls._validate_datavalue_path(values, has_datafile, has_datafiletype)
        else:
            cls._validate_datafile_path(values, has_datafile, has_datafiletype)

        return values

    def is_intermediate_link(self) -> bool:
        return True

    @field_validator("targetmaskfile", mode="before")
    @classmethod
    def validate_targetmaskfile(cls, v: Any) -> Any:
        if isinstance(v, (str, Path)):
            return resolve_file_model(v, PolyFile)
        return v

    @field_validator("averagingtype", mode="before")
    @classmethod
    def validate_average_type(cls, v):
        return enum_value_parser(v, AveragingType)

    @field_validator("targetlayer", mode="before")
    @classmethod
    def validate_targetlayer(cls, v):
        """Coerce targetLayer to a TargetLayer member or a positive integer layer number.

        Accepts ``bottom`` and ``all`` (case-insensitive) or a positive integer. The
        old external-forcings ``LAYER`` values ``-1`` and ``0`` are represented by
        ``bottom`` and ``all`` respectively and are not accepted as integers here.
        """
        result = v
        if v is not None and not isinstance(v, TargetLayer):
            text = str(v).strip()
            if text.lower() in (TargetLayer.bottom.value, TargetLayer.all.value):
                result = TargetLayer(text.lower())
            elif text.lstrip("+").isdigit() and int(text) > 0:
                result = int(text)
            else:
                raise ValueError(
                    "targetLayer must be 'bottom', 'all', or a positive integer, "
                    f"got '{v}'."
                )
        return result


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
        meteo (List[Meteo]): List of `[Meteo]` blocks for legacy meteorological forcings.
            Deprecated: use `spatial` instead.
        spatial (List[Spatial]): List of `[Spatial]` blocks for spatial forcings (meteo,
            initial conditions, and spatial parameters).
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
    spatial: Annotated[List[Spatial], BeforeValidator(make_list)] = Field(
        default_factory=list
    )
    serializer_config: INISerializerConfig = INISerializerConfig(
        section_indent=0, property_indent=0
    )

    @model_validator(mode="after")
    def _warn_on_meteo(self) -> "ExtModel":
        """Emit a DeprecationWarning when [Meteo] blocks are present.

        The `[Meteo]` block is superseded by the `[Spatial]` block. New models
        should use `ExtModel.spatial` instead of `ExtModel.meteo`.
        """
        if self.meteo:
            warnings.warn(
                "`ExtModel.meteo` is deprecated; use `ExtModel.spatial` instead. "
                "`[Meteo]` blocks should be replaced by `[Spatial]` blocks.",
                DeprecationWarning,
                stacklevel=2,
            )
        return self

    @property
    def n_forcing_blocks(self) -> int:
        """Total number of forcing blocks held across all block types.

        Sums every `[Boundary]`, `[Lateral]`, `[SourceSink]`, `[Meteo]` and
        `[Spatial]` block, whether produced by conversion or loaded from an existing
        file. Use this to decide whether the model has any content worth writing;
        counting the individual lists by hand is error-prone and has silently
        dropped block types before.
        """
        return (
            len(self.boundary)
            + len(self.lateral)
            + len(self.sourcesink)
            + len(self.meteo)
            + len(self.spatial)
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


class SpatialError(Exception):
    """SpatialError."""

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


class LateralError(Exception):
    """LateralError."""

    def __init__(self, error_message: str):
        """Initialize with an error message."""
        super().__init__(error_message)

