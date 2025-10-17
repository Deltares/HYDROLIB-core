"""Enum class containing the valid values for the Spatial parameter category
of the external forcings.

for more details check D-Flow FM User Manual 1D2D, Chapter D.3.1, Table D.2
https://content.oss.deltares.nl/delft3d/D-Flow_FM_User_Manual_1D2D.pdf
"""

from enum import IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import yaml
from pydantic.v1 import Field, root_validator, validator
from strenum import StrEnum

from hydrolib.core.base.models import (
    BaseModel,
    DiskOnlyFileModel,
    ModelSaveSettings,
    ParsableFileModel,
    SerializerConfig,
)
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.extold.parser import Parser
from hydrolib.core.dflowfm.extold.serializer import Serializer
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.tim.models import TimModel

EXT_OLD_MODULE_PATH = Path(__file__).parent / "data"

with (EXT_OLD_MODULE_PATH / "old-external-forcing-data.yaml").open("r") as fh:
    QUANTITIES_DATA = yaml.safe_load(fh)

with (EXT_OLD_MODULE_PATH / "header.txt").open("r") as f:
    HEADER = f.read()

INITIALTRACER = "initialtracer"

FILETYPE_FILEMODEL_MAPPING = {
    1: TimModel,
    2: TimModel,
    3: DiskOnlyFileModel,
    4: DiskOnlyFileModel,
    5: DiskOnlyFileModel,
    6: DiskOnlyFileModel,
    7: DiskOnlyFileModel,
    8: DiskOnlyFileModel,
    9: PolyFile,
    10: PolyFile,
    11: DiskOnlyFileModel,
    12: DiskOnlyFileModel,
}

BOUNDARY_CONDITION_QUANTITIES_VALID_PREFIXES = tuple(
    QUANTITIES_DATA["BoundaryCondition"]["prefixes"]
)


class _ExtOldBoundaryQuantity(StrEnum):

    @classmethod
    def _missing_(cls, value):
        """Custom implementation for handling missing values.

        the method parses any missing values and only allows the ones that start with "initialtracer".
        """
        # Allow strings starting with "tracer"
        if isinstance(value, str) and value.startswith(
            BOUNDARY_CONDITION_QUANTITIES_VALID_PREFIXES
        ):
            new_member = str.__new__(cls, value)
            new_member._value_ = value
            return new_member
        else:
            raise ValueError(
                f"{value} is not a valid {cls.__name__} possible quantities are {', '.join(cls.__members__)}, "
                f"and quantities that start with 'tracer'"
            )


ExtOldBoundaryQuantity = StrEnum(
    "ExtOldBoundaryQuantity",
    QUANTITIES_DATA["BoundaryCondition"]["quantity_names"],
    type=_ExtOldBoundaryQuantity,
)
ExtOldParametersQuantity = StrEnum(
    "ExtOldParametersQuantity", QUANTITIES_DATA["Parameter"]["quantity_names"]
)
PARAMETER_QUANTITIES_VALID_PREFIXES = tuple(QUANTITIES_DATA["Parameter"]["prefixes"])
ExtOldMeteoQuantity = StrEnum(
    "ExtOldMeteoQuantity",
    QUANTITIES_DATA["Meteo"]["quantity_names"],
)
ExtOldLateralQuantity = StrEnum("ExtOldLateralQuantity", QUANTITIES_DATA["Lateral"])


INITIAL_CONDITION_QUANTITIES_VALID_PREFIXES = tuple(
    QUANTITIES_DATA["InitialConditions"]["prefixes"]
)


class _ExtOldInitialConditionQuantity(StrEnum):
    """
    If there is a missing quantity that is mentioned in the "Accepted quantity names" section of the user manual
    [Sec.C.5.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.3).
    and [Sec.D.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.D.3).
    please open and issue in github.
    """

    @classmethod
    def _missing_(cls, value):
        """Custom implementation for handling missing values.

        the method parses any missing values and only allows the ones that start with "initialtracer".
        """
        # Allow strings starting with "tracer"
        if isinstance(value, str) and value.startswith(
            INITIAL_CONDITION_QUANTITIES_VALID_PREFIXES
        ):
            new_member = str.__new__(cls, value)
            new_member._value_ = value
            return new_member
        else:
            raise ValueError(
                f"{value} is not a valid {cls.__name__} possible quantities are {', '.join(cls.__members__)}, "
                f"and quantities that start with 'tracer'"
            )


ExtOldInitialConditionQuantity = StrEnum(
    "ExtOldInitialConditionQuantity",
    QUANTITIES_DATA["InitialConditions"]["quantity_names"],
    type=_ExtOldInitialConditionQuantity,
)

ExtOldSourcesSinks = StrEnum("ExtOldSourcesSinks", QUANTITIES_DATA["SourceSink"])

ALL_QUANTITIES = (
    QUANTITIES_DATA["BoundaryCondition"]["quantity_names"]
    | QUANTITIES_DATA["Meteo"]["quantity_names"]
    | QUANTITIES_DATA["Parameter"]["quantity_names"]
    | QUANTITIES_DATA["InitialConditions"]["quantity_names"]
    | QUANTITIES_DATA["SourceSink"]
    | QUANTITIES_DATA["Structure"]
    | QUANTITIES_DATA["Misellaneous"]
    | QUANTITIES_DATA["Lateral"]
)

ALL_PREFIXES = (
    BOUNDARY_CONDITION_QUANTITIES_VALID_PREFIXES
    + INITIAL_CONDITION_QUANTITIES_VALID_PREFIXES
    + PARAMETER_QUANTITIES_VALID_PREFIXES
)

ExtOldQuantity = StrEnum("ExtOldQuantity", ALL_QUANTITIES)


ExtOldFileType = IntEnum("ExtOldFileType", QUANTITIES_DATA["FileType"])
ExtOldMethod = IntEnum("ExtOldMethod", QUANTITIES_DATA["OldMethods"])
ExtOldExtrapolationMethod = IntEnum(
    "ExtOldExtrapolationMethod", QUANTITIES_DATA["ExtrapolationMethod"]
)


class ExtOldForcing(BaseModel):
    """Class holding the external forcing values."""

    quantity: Union[ExtOldQuantity, str] = Field(alias="QUANTITY")
    """Union[Quantity, str]: The name of the quantity."""

    filename: Union[PolyFile, TimModel, DiskOnlyFileModel] = Field(
        None, alias="FILENAME"
    )
    """Union[PolyFile, TimModel, DiskOnlyFileModel]: The file associated to this forcing."""

    varname: Optional[str] = Field(None, alias="VARNAME")
    """Optional[str]: The variable name used in `filename` associated with this forcing; some input files may contain multiple variables."""

    sourcemask: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="SOURCEMASK"
    )
    """DiskOnlyFileModel: The file containing a mask."""

    filetype: ExtOldFileType = Field(alias="FILETYPE")
    """FileType: Indication of the file type.

    Options:
    1. Time series
    2. Time series magnitude and direction
    3. Spatially varying weather
    4. ArcInfo
    5. Spiderweb data (cyclones)
    6. Curvilinear data
    7. Samples (C.3)
    8. Triangulation magnitude and direction
    9. Polyline (<*.pli>-file, C.2)
    11. NetCDF grid data (e.g. meteo fields)
    14. NetCDF wave data
    """

    method: ExtOldMethod = Field(alias="METHOD")
    """ExtOldMethod: The method of interpolation.

    Options:
    1. Pass through (no interpolation)
    2. Interpolate time and space
    3. Interpolate time and space, save weights
    4. Interpolate space
    5. Interpolate time
    6. Averaging space
    7. Interpolate/Extrapolate time
    """

    extrapolation_method: Optional[ExtOldExtrapolationMethod] = Field(
        None, alias="EXTRAPOLATION_METHOD"
    )
    """Optional[ExtOldExtrapolationMethod]: The extrapolation method.

    Options:
    0. No spatial extrapolation.
    1. Do spatial extrapolation outside of source data bounding box.
    """

    maxsearchradius: Optional[float] = Field(None, alias="MAXSEARCHRADIUS")
    """Optional[float]: Search radius (in m) for model grid points that lie outside of the source data bounding box."""

    operand: Operand = Field(alias="OPERAND")
    """Operand: The operand to use for adding the provided values.

    Options:
    'O' Existing values are overwritten with the provided values.
    'A' Provided values are used where existing values are missing.
    '+' Existing values are summed with the provided values.
    '*' Existing values are multiplied with the provided values.
    'X' The maximum values of the existing values and provided values are used.
    'N' The minimum values of the existing values and provided values are used.
    """

    value: Optional[float] = Field(None, alias="VALUE")
    """Optional[float]: Custom coefficients for transformation."""

    factor: Optional[float] = Field(None, alias="FACTOR")
    """Optional[float]: The conversion factor."""

    ifrctyp: Optional[float] = Field(None, alias="IFRCTYP")
    """Optional[float]: The friction type."""

    averagingtype: Optional[float] = Field(None, alias="AVERAGINGTYPE")
    """Optional[float]: The averaging type."""

    relativesearchcellsize: Optional[float] = Field(
        None, alias="RELATIVESEARCHCELLSIZE"
    )
    """Optional[float]: The relative search cell size for samples inside a cell."""

    extrapoltol: Optional[float] = Field(None, alias="EXTRAPOLTOL")
    """Optional[float]: The extrapolation tolerance."""

    percentileminmax: Optional[float] = Field(None, alias="PERCENTILEMINMAX")
    """Optional[float]: Changes the min/max operator to an average of the highest/lowest data points. The value sets the percentage of the total set that is to be included.."""

    area: Optional[float] = Field(None, alias="AREA")
    """Optional[float]: The area for sources and sinks."""

    nummin: Optional[int] = Field(None, alias="NUMMIN")
    """Optional[int]: The minimum required number of source data points in each target cell."""

    tracerfallvelocity: Optional[float] = Field(None, alias="TRACERFALLVELOCITY")
    tracerdecaytime: Optional[float] = Field(None, alias="TRACERDECAYTIME")

    def is_intermediate_link(self) -> bool:
        return True

    @root_validator(pre=True)
    def handle_case_insensitive_tracer_fields(cls, values):
        """Handle case-insensitive matching for tracer fields."""
        values_copy = dict(values)

        # Define the field names and their aliases
        tracer_fields = ["tracerfallvelocity", "tracerdecaytime"]

        for field_i in values.keys():
            if field_i.lower() in tracer_fields:
                # if the field is already lowercase no need to change it
                if field_i != field_i.lower():
                    # If the key is not in the expected lowercase format, add it with the correct format
                    values_copy[field_i.lower()] = values_copy[field_i]
                    # Remove the original key to avoid "extra fields not permitted" error
                    values_copy.pop(field_i)

        return values_copy

    @classmethod
    def validate_quantity_prefix(
        cls, lower_value: str, value_str: str
    ) -> Optional[str]:
        """Checks if the provided quantity string starts with any known valid prefix.

        If the quantity matches a prefix, ensures it is followed by a name.
        Returns the full quantity string if valid, otherwise None.

        Args:
            lower_value (str): The quantity string in lowercase.
            value_str (str): The original quantity string.

        Raises:
            ValueError: If the quantity is only the prefix without a name.
        """
        value = None
        for prefix in ALL_PREFIXES:
            if lower_value.startswith(prefix):
                n = len(prefix)
                if n == len(value_str):
                    raise ValueError(
                        f"QUANTITY '{value_str}' should be appended with a valid name."
                    )
                value = prefix + value_str[n:]
                break

        return value

    @validator("quantity", pre=True)
    def validate_quantity(cls, value):
        if not isinstance(value, ExtOldQuantity):
            found = False
            value_str = str(value)
            lower_value = value_str.lower()

            quantity = cls.validate_quantity_prefix(lower_value, value_str)
            if quantity is not None:
                value = quantity
                found = True
            elif lower_value in list(ExtOldQuantity):
                value = ExtOldQuantity(lower_value)
                found = True
            elif value_str in list(ExtOldQuantity):
                value = ExtOldQuantity(value_str)
                found = True

            if not found:
                supported_value_str = ", ".join(([x.value for x in ExtOldQuantity]))
                raise ValueError(
                    f"QUANTITY '{value_str}' not supported. Supported values: {supported_value_str}"
                )
        return value

    @validator("operand", pre=True)
    def validate_operand(cls, value):
        if isinstance(value, Operand):
            return value

        if isinstance(value, str):

            for operand in Operand:
                if value.lower() == operand.value.lower():
                    return operand

            supported_value_str = ", ".join(([x.value for x in Operand]))
            raise ValueError(
                f"OPERAND '{value}' not supported. Supported values: {supported_value_str}"
            )

        return value

    @root_validator(skip_on_failure=True)
    def validate_forcing(cls, values):
        class _Field:
            def __init__(self, key: str) -> None:
                self.alias = cls.__fields__[key].alias
                self.value = values[key]

        def raise_error_only_allowed_when(
            field: _Field, dependency: _Field, valid_dependency_value: str
        ):
            error = f"{field.alias} only allowed when {dependency.alias} is {valid_dependency_value}"
            raise ValueError(error)

        def only_allowed_when(
            field: _Field, dependency: _Field, valid_dependency_value: Any
        ):
            """This function checks if a particular field is allowed to have a value only when a dependency field has a specific value."""

            if field.value is None or dependency.value == valid_dependency_value:
                return

            raise_error_only_allowed_when(field, dependency, valid_dependency_value)

        quantity = _Field("quantity")
        varname = _Field("varname")
        sourcemask = _Field("sourcemask")
        filetype = _Field("filetype")
        method = _Field("method")
        extrapolation_method = _Field("extrapolation_method")
        maxsearchradius = _Field("maxsearchradius")
        value = _Field("value")
        factor = _Field("factor")
        ifrctype = _Field("ifrctyp")
        averagingtype = _Field("averagingtype")
        relativesearchcellsize = _Field("relativesearchcellsize")
        extrapoltol = _Field("extrapoltol")
        percentileminmax = _Field("percentileminmax")
        area = _Field("area")
        nummin = _Field("nummin")

        only_allowed_when(varname, filetype, ExtOldFileType.NetCDFGridData)

        if sourcemask.value.filepath is not None and filetype.value not in [
            ExtOldFileType.ArcInfo,
            ExtOldFileType.CurvilinearData,
        ]:
            raise_error_only_allowed_when(
                sourcemask, filetype, valid_dependency_value="4 or 6"
            )

        if (
            extrapolation_method.value
            == ExtOldExtrapolationMethod.SpatialExtrapolationOutsideOfSourceDataBoundingBox
            and method.value != ExtOldMethod.InterpolateTimeAndSpaceSaveWeights
            and method.value != ExtOldMethod.Obsolete
        ):
            error = f"{extrapolation_method.alias} only allowed to be 1 when {method.alias} is 3"
            raise ValueError(error)

        only_allowed_when(
            maxsearchradius,
            extrapolation_method,
            ExtOldExtrapolationMethod.SpatialExtrapolationOutsideOfSourceDataBoundingBox,
        )
        only_allowed_when(value, method, ExtOldMethod.InterpolateSpace)

        if factor.value is not None and not quantity.value.startswith(INITIALTRACER):
            error = f"{factor.alias} only allowed when {quantity.alias} starts with {INITIALTRACER}"
            raise ValueError(error)

        only_allowed_when(ifrctype, quantity, ExtOldQuantity.FrictionCoefficient)
        only_allowed_when(averagingtype, method, ExtOldMethod.AveragingSpace)
        only_allowed_when(relativesearchcellsize, method, ExtOldMethod.AveragingSpace)
        only_allowed_when(extrapoltol, method, ExtOldMethod.InterpolateTime)
        only_allowed_when(percentileminmax, method, ExtOldMethod.AveragingSpace)
        only_allowed_when(
            area, quantity, ExtOldQuantity.DischargeSalinityTemperatureSorSin
        )
        only_allowed_when(nummin, method, ExtOldMethod.AveragingSpace)

        return values

    @root_validator(pre=True)
    def choose_file_model(cls, values):
        """Root-level validator to the right class for the filename parameter based on the filetype.

        The validator chooses the right class for the filename parameter based on the FileType_FileModel_mapping
        dictionary.

        FileType_FileModel_mapping = {
            1: TimModel,
            2: TimModel,
            3: DiskOnlyFileModel,
            4: DiskOnlyFileModel,
            5: DiskOnlyFileModel,
            6: DiskOnlyFileModel,
            7: DiskOnlyFileModel,
            8: DiskOnlyFileModel,
            9: PolyFile,
            10: PolyFile,
            11: DiskOnlyFileModel,
            12: DiskOnlyFileModel,
        }
        """
        # if the filetype and the filename are present in the values
        if any(par in values for par in ["filetype", "FILETYPE"]) and any(
            par in values for par in ["filename", "FILENAME"]
        ):
            file_type_var_name = "filetype" if "filetype" in values else "FILETYPE"
            filename_var_name = "filename" if "filename" in values else "FILENAME"
            file_type = values.get(file_type_var_name)
            raw_path = values.get(filename_var_name)
            model = FILETYPE_FILEMODEL_MAPPING.get(int(file_type))

            if not isinstance(raw_path, model):
                raw_path = model(raw_path)

            values[filename_var_name] = raw_path

        return values


class ExtOldModel(ParsableFileModel):
    """
    The overall external forcings model that contains the contents of one external forcings file (old format).

    This model is typically referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.external_forcing.extforcefile`.
    """

    comment: List[str] = Field(default=HEADER.splitlines()[1:])
    """List[str]: The comments in the header of the external forcing file."""
    forcing: List[ExtOldForcing] = Field(default_factory=list)
    """List[ExtOldForcing]: The external forcing/QUANTITY blocks in the external forcing file."""

    @classmethod
    def _ext(cls) -> str:
        return ".ext"

    @classmethod
    def _filename(cls) -> str:
        return "externalforcings"

    def dict(self, *args, **kwargs):
        return dict(comment=self.comment, forcing=[dict(f) for f in self.forcing])

    @classmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, SerializerConfig, ModelSaveSettings], None]:
        return Serializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return Parser.parse

    @property
    def quantities(self) -> List[str]:
        """List all the quantities in the external forcings file."""
        return [forcing.quantity for forcing in self.forcing]
