from enum import IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import yaml
from pydantic import Field, field_validator, model_validator
from strenum import StrEnum

from hydrolib.core.base.models import (
    BaseModel,
    DiskOnlyFileModel,
    ModelSaveSettings,
    ParsableFileModel,
    SerializerConfig,
)
from hydrolib.core.base.utils import resolve_file_model
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.extold.parser import Parser
from hydrolib.core.dflowfm.extold.serializer import Serializer
from hydrolib.core.dflowfm.ini.util import enum_value_parser
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.tim.models import TimModel

EXT_OLD_MODULE_PATH = Path(__file__).parent / "data"

with (EXT_OLD_MODULE_PATH / "old-external-forcing-data.yaml").open("r") as fh:
    QUANTITIES_DATA = yaml.safe_load(fh)

with (EXT_OLD_MODULE_PATH / "header.txt").open("r") as f:
    HEADER = f.read()


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


ExtOldTracerQuantity = StrEnum(
    "ExtOldTracerQuantity", QUANTITIES_DATA["Tracer"]["quantity-names"]
)

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
    QUANTITIES_DATA["BoundaryCondition"]["quantity-names"],
    type=_ExtOldBoundaryQuantity,
)
ExtOldParametersQuantity = StrEnum(
    "ExtOldParametersQuantity", QUANTITIES_DATA["Parameter"]
)
ExtOldMeteoQuantity = StrEnum(
    "ExtOldMeteoQuantity",
    QUANTITIES_DATA["Meteo"],
)


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
    QUANTITIES_DATA["InitialConditions"]["quantity-names"],
    type=_ExtOldInitialConditionQuantity,
)

ExtOldSourcesSinks = StrEnum("ExtOldSourcesSinks", QUANTITIES_DATA["SourceSink"])

ALL_QUANTITIES = (
    QUANTITIES_DATA["BoundaryCondition"]["quantity-names"]
    | QUANTITIES_DATA["Meteo"]
    | QUANTITIES_DATA["Parameter"]
    | QUANTITIES_DATA["InitialConditions"]["quantity-names"]
    | QUANTITIES_DATA["SourceSink"]
    | QUANTITIES_DATA["Structure"]
    | QUANTITIES_DATA["Misellaneous"]
)

ExtOldQuantity = StrEnum("ExtOldQuantity", ALL_QUANTITIES)


ExtOldFileType = IntEnum("ExtOldFileType", QUANTITIES_DATA["FileType"])
ExtOldMethod = IntEnum("ExtOldMethod", QUANTITIES_DATA["OldMethods"])
ExtOldExtrapolationMethod = IntEnum(
    "ExtOldExtrapolationMethod", QUANTITIES_DATA["ExtrapolationMethod"]
)


class ExtOldForcing(BaseModel):
    """Class holding the external forcing values.

    This class is used to represent the external forcing values in the D-Flow FM model.

    Attributes:
        quantity (Union[ExtOldQuantity, str]):
            The name of the quantity.
        filename (Union[PolyFile, TimModel, DiskOnlyFileModel]):
            The file associated with this forcing.
        varname (Optional[str]):
            The variable name used in `filename` associated with this forcing; some input files may contain multiple variables.
        sourcemask (DiskOnlyFileModel):
            The file containing a mask.
        filetype (ExtOldFileType):
            Indication of the file type.
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
        method (ExtOldMethod):
            The method of interpolation.
            Options:
                1. Pass through (no interpolation)
                2. Interpolate time and space
                3. Interpolate time and space, save weights
                4. Interpolate space
                5. Interpolate time
                6. Averaging space
                7. Interpolate/Extrapolate time
        extrapolation_method (Optional[ExtOldExtrapolationMethod]):
            The extrapolation method.
                Options:
                    0. No spatial extrapolation.
                    1. Do spatial extrapolation outside of source data bounding box.
        maxsearchradius (Optional[float]):
            Search radius for model grid points that lie outside of the source data bounding box.
        operand (Operand):
            The operand to use for adding the provided values.

            Options:
                'O' Existing values are overwritten with the provided values.
                'A' Provided values are used where existing values are missing.
                '+' Existing values are summed with the provided values.
                '*' Existing values are multiplied with the provided values.
                'X' The maximum values of the existing values and provided values are used.
                'N' The minimum values of the existing values and provided values are used.
        value (Optional[float]):
            Custom coefficients for transformation.
        factor (Optional[float]):
            The conversion factor.
        ifrctyp (Optional[float]):
            The friction type.
        averagingtype (Optional[float]):
            The averaging type.
        relativesearchcellsize (Optional[float]):
            The relative search cell size for samples inside a cell.
        extrapoltol (Optional[float]):
            The extrapolation tolerance.
        percentileminmax (Optional[float]):
            Changes the min/max operator to an average of the highest/lowest data points.
            The value sets the percentage of the total set that is to be included.
        area (Optional[float]):
            The area for sources and sinks.
        nummin (Optional[int]):
            The minimum required number of source data points in each target cell.
    """

    quantity: Union[ExtOldQuantity, str] = Field(alias="QUANTITY")
    filename: Union[PolyFile, TimModel, DiskOnlyFileModel] = Field(
        None, alias="FILENAME"
    )
    varname: Optional[str] = Field(None, alias="VARNAME")
    sourcemask: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="SOURCEMASK"
    )
    filetype: ExtOldFileType = Field(alias="FILETYPE")
    method: ExtOldMethod = Field(alias="METHOD")
    extrapolation_method: Optional[ExtOldExtrapolationMethod] = Field(
        None, alias="EXTRAPOLATION_METHOD"
    )

    maxsearchradius: Optional[float] = Field(None, alias="MAXSEARCHRADIUS")
    operand: Operand = Field(alias="OPERAND")
    value: Optional[float] = Field(None, alias="VALUE")
    factor: Optional[float] = Field(None, alias="FACTOR")
    ifrctyp: Optional[float] = Field(None, alias="IFRCTYP")
    averagingtype: Optional[float] = Field(None, alias="AVERAGINGTYPE")

    relativesearchcellsize: Optional[float] = Field(
        None, alias="RELATIVESEARCHCELLSIZE"
    )
    extrapoltol: Optional[float] = Field(None, alias="EXTRAPOLTOL")
    percentileminmax: Optional[float] = Field(None, alias="PERCENTILEMINMAX")
    area: Optional[float] = Field(None, alias="AREA")
    nummin: Optional[int] = Field(None, alias="NUMMIN")

    tracerfallvelocity: Optional[float] = Field(None, alias="TRACERFALLVELOCITY")
    tracerdecaytime: Optional[float] = Field(None, alias="TRACERDECAYTIME")

    def is_intermediate_link(self) -> bool:
        return True

    @model_validator(mode="before")
    @classmethod
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

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity(cls, value) -> Any:
        if isinstance(value, ExtOldQuantity):
            return value

        def raise_error_tracer_name(quantity: ExtOldTracerQuantity):
            raise ValueError(
                f"QUANTITY '{quantity}' should be appended with a tracer name."
            )

        if isinstance(value, ExtOldTracerQuantity):
            raise_error_tracer_name(value)

        value_str = str(value)
        lower_value = value_str.lower()

        for tracer_quantity in ExtOldTracerQuantity:
            if lower_value.startswith(tracer_quantity):
                n = len(tracer_quantity)
                if n == len(value_str):
                    raise_error_tracer_name(tracer_quantity)
                return tracer_quantity + value_str[n:]

        if lower_value in list(ExtOldQuantity):
            return ExtOldQuantity(lower_value)

        supported_value_str = ", ".join(([x.value for x in ExtOldQuantity]))
        raise ValueError(
            f"QUANTITY '{value_str}' not supported. Supported values: {supported_value_str}"
        )

    @field_validator("operand", mode="before")
    @classmethod
    def validate_operand(cls, value):
        return enum_value_parser(value, Operand)

    @model_validator(mode="after")
    def validate_varname(self):
        if self.varname and self.filetype != ExtOldFileType.NetCDFGridData:
            raise ValueError(
                "VARNAME only allowed when FILETYPE is 11 (NetCDFGridData)"
            )
        return self

    @field_validator("extrapolation_method")
    @classmethod
    def validate_extrapolation_method(cls, v, info):
        method = info.data.get("method")
        valid_extrapolation_method = (
            ExtOldExtrapolationMethod.SpatialExtrapolationOutsideOfSourceDataBoundingBox
        )
        available_extrapolation_methods = [
            ExtOldMethod.InterpolateTimeAndSpaceSaveWeights,
            ExtOldMethod.Obsolete,
        ]
        if (
            v == valid_extrapolation_method
            and method not in available_extrapolation_methods
        ):
            raise ValueError(
                f"EXTRAPOLATION_METHOD only allowed to be {valid_extrapolation_method} when METHOD is "
                f"{available_extrapolation_methods[0]} or {available_extrapolation_methods[1]}"
            )
        return v

    @model_validator(mode="after")
    def validate_factor(self):
        quantity = self.quantity
        if self.factor is not None and not str(quantity).startswith(
            ExtOldTracerQuantity.InitialTracer
        ):
            raise ValueError(
                f"FACTOR only allowed when QUANTITY starts with {ExtOldTracerQuantity.InitialTracer}"
            )
        return self

    @model_validator(mode="after")
    def validate_ifrctyp(self):
        if (
            self.ifrctyp is not None
            and self.quantity != ExtOldQuantity.FrictionCoefficient
        ):
            raise ValueError(
                f"IFRCTYP only allowed when QUANTITY is {ExtOldQuantity.FrictionCoefficient}"
            )
        return self

    @model_validator(mode="after")
    def validate_averagingtype(self):
        if (
            self.averagingtype is not None
            and self.method != ExtOldMethod.AveragingSpace
        ):
            raise ValueError(
                f"AVERAGINGTYPE only allowed when METHOD is {ExtOldMethod.AveragingSpace}"
            )
        return self

    @model_validator(mode="after")
    def validate_relativesearchcellsize(self):
        if (
            self.relativesearchcellsize is not None
            and self.method != ExtOldMethod.AveragingSpace
        ):
            raise ValueError(
                f"RELATIVESEARCHCELLSIZE only allowed when METHOD is {ExtOldMethod.AveragingSpace}"
            )
        return self

    @model_validator(mode="after")
    def validate_extrapoltol(self):
        if self.extrapoltol is not None and self.method != ExtOldMethod.InterpolateTime:
            raise ValueError("EXTRAPOLTOL only allowed when METHOD is 5")
        return self

    @model_validator(mode="after")
    def validate_percentileminmax(self):
        if (
            self.percentileminmax is not None
            and self.method != ExtOldMethod.AveragingSpace
        ):
            raise ValueError(
                f"PERCENTILEMINMAX only allowed when METHOD is {ExtOldMethod.AveragingSpace}"
            )
        return self

    @model_validator(mode="after")
    def validate_area(self):
        if (
            self.area is not None
            and self.quantity != ExtOldQuantity.DischargeSalinityTemperatureSorSin
        ):
            raise ValueError(
                f"AREA only allowed when QUANTITY is {ExtOldQuantity.DischargeSalinityTemperatureSorSin}"
            )
        return self

    @model_validator(mode="after")
    def validate_nummin(self):
        if self.nummin is not None and self.method != ExtOldMethod.AveragingSpace:
            raise ValueError(
                f"NUMMIN only allowed when METHOD is {ExtOldMethod.AveragingSpace}"
            )
        return self

    @field_validator("maxsearchradius")
    def validate_maxsearchradius(cls, v, info):
        if v is not None:
            extrap = info.data.get("extrapolation_method")
            extrapolation_method_value = (
                ExtOldExtrapolationMethod.SpatialExtrapolationOutsideOfSourceDataBoundingBox
            )
            if extrap != extrapolation_method_value:
                raise ValueError(
                    f"MAXSEARCHRADIUS only allowed when EXTRAPOLATION_METHOD is {extrapolation_method_value}"
                )
        return v

    @field_validator("value")
    @classmethod
    def validate_value(cls, v, info):
        if v is not None:
            method = info.data.get("method")
            if method != ExtOldMethod.InterpolateSpace:
                raise ValueError(
                    f"VALUE only allowed when METHOD is {ExtOldMethod.InterpolateSpace} (InterpolateSpace)"
                )
        return v

    @model_validator(mode="before")
    @classmethod
    def choose_file_model(cls, values: Dict[str, Any]) -> Dict[str, Any]:
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

            if isinstance(raw_path, (Path, str)):
                model = FILETYPE_FILEMODEL_MAPPING.get(int(file_type))
                values[filename_var_name] = resolve_file_model(raw_path, model)

        return values

    @model_validator(mode="before")
    @classmethod
    def validate_sourcemask(cls, data: Any) -> Any:
        filetype = data.get("filetype")
        sourcemask = data.get("sourcemask")

        # Convert string to DiskOnlyFileModel if needed
        if isinstance(sourcemask, str):
            data["sourcemask"] = DiskOnlyFileModel(sourcemask)
            sourcemask = data["sourcemask"]

        if sourcemask and filetype not in [
            ExtOldFileType.ArcInfo,
            ExtOldFileType.CurvilinearData,
        ]:
            raise ValueError("SOURCEMASK only allowed when FILETYPE is 4 or 6")
        return data


class ExtOldModel(ParsableFileModel):
    """
    The overall external forcings model that contains the contents of one external forcings file (old format).

    This model is typically referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.external_forcing.extforcefile`.

    Attributes:
        comment (List[str]):
            The comments in the header of the external forcing file.
        forcing (List[ExtOldForcing]):
            The external forcing/QUANTITY blocks in the external forcing file.
    """

    comment: List[str] = Field(default=HEADER.splitlines()[1:])
    forcing: List[ExtOldForcing] = Field(default_factory=list)

    @classmethod
    def _ext(cls) -> str:
        return ".ext"

    @classmethod
    def _filename(cls) -> str:
        return "externalforcings"

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
