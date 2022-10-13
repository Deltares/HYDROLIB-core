"""Representation of a .bc file in various classes.

    Most relevant classes are:

    *   ForcingModel: toplevel class containing the whole .bc file contents.
    *   ForcingBase subclasses: containing the actual data columns, for example:
        TimeSeries, HarmonicComponent, AstronomicComponent, HarmonicCorrection,
        AstronomicCorrection, Constant, T3D.

"""
import logging
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Literal, Optional, Set, Union

from pydantic import Extra
from pydantic.class_validators import root_validator, validator
from pydantic.fields import Field

from hydrolib.core.io.ini.io_models import Property, Section
from hydrolib.core.io.ini.models import (
    BaseModel,
    DataBlockINIBasedModel,
    INIGeneral,
    INIModel,
)
from hydrolib.core.io.ini.parser import Parser, ParserConfig
from hydrolib.core.io.ini.serializer import SerializerConfig, write_ini
from hydrolib.core.io.ini.util import (
    get_enum_validator,
    get_from_subclass_defaults,
    get_key_renaming_root_validator,
    get_split_string_on_delimiter_validator,
    make_list_validator,
)

logger = logging.getLogger(__name__)


class VerticalInterpolation(str, Enum):
    """Enum class containing the valid values for the vertical position type,
    which defines what the numeric values for vertical position specification mean.
    """

    linear = "linear"
    """str: Linear interpolation between vertical positions."""

    log = "log"
    """str: Logarithmic interpolation between vertical positions (e.g. vertical velocity profiles)."""

    block = "block"
    """str: Equal to the value at the directly lower specified vertical position."""


class VerticalPositionType(str, Enum):
    """Enum class containing the valid values for the vertical position type."""

    percentage_bed = "percBed"
    """str: Percentage with respect to the water depth from the bed upward."""

    z_bed = "ZBed"
    """str: Absolute distance from the bed upward."""

    z_datum = "ZDatum"
    """str: z-coordinate with respect to the reference level of the model."""

    z_surf = "ZSurf"
    """str: Absolute distance from the free surface downward."""


class TimeInterpolation(str, Enum):
    """Enum class containing the valid values for the time interpolation."""

    linear = "linear"
    """str: Linear interpolation between times."""

    block_from = "blockFrom"
    """str: Equal to that at the start of the time interval (latest specified time value)."""

    block_to = "blockTo"
    """str: Equal to that at the end of the time interval (upcoming specified time value)."""


class QuantityUnitPair(BaseModel):
    """A .bc file header lines tuple containing a quantity name, its unit and optionally a vertical position index."""

    quantity: str
    """str: Name of quantity."""

    unit: str
    """str: Unit of quantity."""

    vertpositionindex: Optional[int] = Field(alias="vertPositionIndex")
    """int (optional): This is a (one-based) index into the verticalposition-specification, assigning a vertical position to the quantity (t3D-blocks only)."""

    def _to_properties(self):
        yield Property(key="quantity", value=self.quantity)
        yield Property(key="unit", value=self.unit)
        if self.vertpositionindex is not None:
            yield Property(key="vertPositionIndex", value=self.vertpositionindex)


class ForcingBase(DataBlockINIBasedModel):
    """
    The base class of a single [Forcing] block in a .bc forcings file.

    Typically subclassed, for the specific types of forcing data, e.g, TimeSeries.
    This model is for example referenced under a
    [ForcingModel][hydrolib.core.io.bc.models.ForcingModel]`.forcing[..]`.
    """

    _header: Literal["Forcing"] = "Forcing"
    name: str = Field(alias="name")
    """str: Unique identifier that identifies the location for this forcing data."""

    function: str = Field(alias="function")
    """str: Function type of the data in the actual datablock."""

    quantityunitpair: List[QuantityUnitPair]
    """List[QuantityUnitPair]: List of header lines for one or more quantities and their unit. Describes the columns in the actual datablock."""

    def _exclude_fields(self) -> Set:
        return {"quantityunitpair"}.union(super()._exclude_fields())

    @classmethod
    def _supports_comments(cls):
        return True

    @classmethod
    def _duplicate_keys_as_list(cls):
        return True

    @root_validator(pre=True)
    def _validate_quantityunitpair(cls, values):
        quantityunitpairkey = "quantityunitpair"

        if values.get(quantityunitpairkey) is not None:
            return values

        quantities = values.get("quantity")
        if quantities is None:
            raise ValueError("quantity is not provided")
        units = values.get("unit")
        if units is None:
            raise ValueError("unit is not provided")

        if isinstance(quantities, str) and isinstance(units, str):
            values[quantityunitpairkey] = [
                QuantityUnitPair(quantity=quantities, unit=units)
            ]
            return values

        if isinstance(quantities, list) and isinstance(units, list):
            if len(quantities) != len(units):
                raise ValueError(
                    "Number of quantities should be equal to number of units"
                )

            values[quantityunitpairkey] = [
                QuantityUnitPair(quantity=quantity, unit=unit)
                for quantity, unit in zip(quantities, units)
            ]
            return values

        raise ValueError("Number of quantities should be equal to number of units")

    @validator("function", pre=True)
    def _set_function(cls, value):
        return get_from_subclass_defaults(ForcingBase, "function", value)

    @classmethod
    def validate(cls, v):
        """Try to initialize subclass based on the `function` field.
        This field is compared to each `function` field of the derived models of `ForcingBase`.
        The derived model with an equal function type will be initialized.

        Raises:
            ValueError: When the given type is not a known structure type.
        """

        # should be replaced by discriminated unions once merged
        # https://github.com/samuelcolvin/pydantic/pull/2336
        if isinstance(v, dict):
            for c in cls.__subclasses__():
                if (
                    c.__fields__.get("function").default.lower()
                    == v.get("function", "").lower()
                ):
                    v = c(**v)
                    break
            else:
                raise ValueError(
                    f"Function of {cls.__name__} with name={v.get('name', '')} and function={v.get('function', '')} is not recognized."
                )
        return v

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("name")

    def _to_section(self) -> Section:
        section = super()._to_section()

        for quantity in self.quantityunitpair:
            for prop in quantity._to_properties():
                section.content.append(prop)

        return section

    class Config:
        extra = Extra.ignore


class TimeSeries(ForcingBase):
    """Subclass for a .bc file [Forcing] block with timeseries data."""

    function: Literal["timeseries"] = "timeseries"

    timeinterpolation: TimeInterpolation = Field(alias="timeInterpolation")
    """TimeInterpolation: The type of time interpolation."""

    offset: float = Field(0.0, alias="offset")
    """float: All values in the table are increased by the offset (after multiplication by factor). Defaults to 0.0."""

    factor: float = Field(1.0, alias="factor")
    """float: All values in the table are multiplied with the factor. Defaults to 1.0."""

    _timeinterpolation_validator = get_enum_validator(
        "timeinterpolation", enum=TimeInterpolation
    )

    _key_renaming_root_validator = get_key_renaming_root_validator(
        {
            "timeinterpolation": ["time_interpolation"],
        }
    )


class Harmonic(ForcingBase):
    """Subclass for a .bc file [Forcing] block with harmonic components data."""

    function: Literal["harmonic"] = "harmonic"

    factor: float = Field(1.0, alias="factor")
    """float: All values in the table are multiplied with the factor. Defaults to 1.0."""


class Astronomic(ForcingBase):
    """Subclass for a .bc file [Forcing] block with astronomic components data."""

    function: Literal["astronomic"] = "astronomic"

    factor: float = Field(1.0, alias="factor")
    """float: All values in the table are multiplied with the factor. Defaults to 1.0."""


class HarmonicCorrection(ForcingBase):
    """Subclass for a .bc file [Forcing] block with harmonic components correction data."""

    function: Literal["harmonic-correction"] = "harmonic-correction"


class AstronomicCorrection(ForcingBase):
    """Subclass for a .bc file [Forcing] block with astronomic components correction data."""

    function: Literal["astronomic-correction"] = "astronomic-correction"


class T3D(ForcingBase):
    """Subclass for a .bc file [Forcing] block with 3D timeseries data."""

    function: Literal["t3d"] = "t3d"

    offset: float = Field(0.0, alias="offset")
    """float: All values in the table are increased by the offset (after multiplication by factor). Defaults to 0.0."""

    factor: float = Field(1.0, alias="factor")
    """float: All values in the table are multiplied with the factor. Defaults to 1.0."""

    vertpositions: List[float] = Field(alias="vertPositions")
    """List[float]: The specification of the vertical positions."""

    vertinterpolation: VerticalInterpolation = Field(
        VerticalInterpolation.linear.value, alias="vertInterpolation"
    )
    """VerticalInterpolation: The type of vertical interpolation. Defaults to linear."""

    vertpositiontype: VerticalPositionType = Field(alias="vertPositionType")
    """VerticalPositionType: The vertical position type of the verticalpositions values."""

    timeinterpolation: TimeInterpolation = Field(
        TimeInterpolation.linear.value, alias="timeInterpolation"
    )
    """TimeInterpolation: The type of time interpolation. Defaults to linear."""

    _key_renaming_root_validator = get_key_renaming_root_validator(
        {
            "timeinterpolation": ["time_interpolation"],
            "vertpositions": ["vertical_position_specification"],
            "vertinterpolation": ["vertical_interpolation"],
            "vertpositiontype": ["vertical_position_type"],
            "vertpositionindex": ["vertical_position"],
        }
    )

    _split_to_list = get_split_string_on_delimiter_validator(
        "vertpositions",
    )

    _verticalinterpolation_validator = get_enum_validator(
        "vertinterpolation", enum=VerticalInterpolation
    )
    _verticalpositiontype_validator = get_enum_validator(
        "vertpositiontype", enum=VerticalPositionType
    )
    _timeinterpolation_validator = get_enum_validator(
        "timeinterpolation", enum=TimeInterpolation
    )

    @root_validator(pre=True)
    def _validate_quantityunitpairs(cls, values: Dict) -> Dict:
        super()._validate_quantityunitpair(values)

        quantityunitpairs = values["quantityunitpair"]

        T3D._validate_that_first_unit_is_time_and_has_no_verticalposition(
            quantityunitpairs
        )

        verticalpositions = values.get("vertpositions")
        if verticalpositions is None:
            raise ValueError("vertpositions is not provided")
        verticalpositionindexes = values.get("vertpositionindex")

        number_of_verticalpositions = (
            len(verticalpositions)
            if isinstance(verticalpositions, List)
            else len(verticalpositions.split())
        )

        if verticalpositionindexes is None:
            T3D._validate_that_all_non_time_quantityunitpairs_have_valid_verticalpositionindex(
                quantityunitpairs, number_of_verticalpositions
            )
            return values

        T3D._validate_verticalpositionindexes_and_update_quantityunitpairs(
            verticalpositionindexes,
            number_of_verticalpositions,
            quantityunitpairs,
        )

        return values

    @staticmethod
    def _validate_that_first_unit_is_time_and_has_no_verticalposition(
        quantityunitpairs: List[QuantityUnitPair],
    ) -> None:
        if quantityunitpairs[0].quantity.lower() != "time":
            raise ValueError("First quantity should be `time`")
        if quantityunitpairs[0].vertpositionindex is not None:
            raise ValueError("`time` quantity cannot have vertical position index")

    @staticmethod
    def _validate_that_all_non_time_quantityunitpairs_have_valid_verticalpositionindex(
        quantityunitpairs: List[QuantityUnitPair], maximum_verticalpositionindex: int
    ) -> None:
        for quantityunitpair in quantityunitpairs:
            quantity = quantityunitpair.quantity.lower()
            verticalpositionindex = quantityunitpair.vertpositionindex

            if quantity == "time":
                continue
            if not T3D._is_valid_verticalpositionindex(
                verticalpositionindex, maximum_verticalpositionindex
            ):
                raise ValueError(
                    f"Vertical position index should be between 1 and {maximum_verticalpositionindex}, but {verticalpositionindex} was given"
                )

    @staticmethod
    def _validate_verticalpositionindexes_and_update_quantityunitpairs(
        verticalpositionindexes: List[int],
        number_of_verticalpositions: int,
        quantityunitpairs: List[QuantityUnitPair],
    ) -> None:
        if verticalpositionindexes is None:
            raise ValueError("vertPositionIndex is not provided")

        if len(verticalpositionindexes) != len(quantityunitpairs) - 1:
            raise ValueError(
                "Number of vertical position indexes should be equal to the number of quantities/units - 1"
            )

        T3D._validate_that_verticalpositionindexes_are_valid(
            verticalpositionindexes, number_of_verticalpositions
        )

        T3D._add_verticalpositionindex_to_quantityunitpairs(
            quantityunitpairs[1:], verticalpositionindexes
        )

    @staticmethod
    def _validate_that_verticalpositionindexes_are_valid(
        verticalpositionindexes: List[int], number_of_vertical_positions: int
    ) -> None:
        for verticalpositionindexstring in verticalpositionindexes:
            verticalpositionindex = (
                int(verticalpositionindexstring)
                if verticalpositionindexstring
                else None
            )
            if not T3D._is_valid_verticalpositionindex(
                verticalpositionindex, number_of_vertical_positions
            ):
                raise ValueError(
                    f"Vertical position index should be between 1 and {number_of_vertical_positions}"
                )

    @staticmethod
    def _is_valid_verticalpositionindex(
        verticalpositionindex: int, number_of_vertical_positions: int
    ) -> bool:
        one_based_index_offset = 1

        return (
            verticalpositionindex is not None
            and verticalpositionindex >= one_based_index_offset
            and verticalpositionindex <= number_of_vertical_positions
        )

    @staticmethod
    def _add_verticalpositionindex_to_quantityunitpairs(
        quantityunitpairs: List[QuantityUnitPair], verticalpositionindexes: List[int]
    ) -> None:
        if len(quantityunitpairs) != len(verticalpositionindexes):
            raise ValueError(
                "Number of quantityunitpairs and verticalpositionindexes should be equal"
            )

        for (quantityunitpair, verticalpositionindex) in zip(
            quantityunitpairs, verticalpositionindexes
        ):
            quantityunitpair.vertpositionindex = verticalpositionindex


class QHTable(ForcingBase):
    """Subclass for a .bc file [Forcing] block with Q-h table data."""

    function: Literal["qhtable"] = "qhtable"


class Constant(ForcingBase):
    """Subclass for a .bc file [Forcing] block with constant value data."""

    function: Literal["constant"] = "constant"

    offset: float = Field(0.0, alias="offset")
    """float: All values in the table are increased by the offset (after multiplication by factor). Defaults to 0.0."""

    factor: float = Field(1.0, alias="factor")
    """float: All values in the table are multiplied with the factor. Defaults to 1.0."""


class ForcingGeneral(INIGeneral):
    """`[General]` section with .bc file metadata."""

    fileversion: str = Field("1.01", alias="fileVersion")
    """str: The file version."""

    filetype: Literal["boundConds"] = Field("boundConds", alias="fileType")


class ForcingModel(INIModel):
    """
    The overall model that contains the contents of one .bc forcings file.

    This model is for example referenced under a
    [ExtModel][hydrolib.core.io.ext.models.ExtModel]`.boundary[..].forcingfile[..]`.
    """

    general: ForcingGeneral = ForcingGeneral()
    """ForcingGeneral: `[General]` block with file metadata."""

    forcing: List[ForcingBase] = []
    """List[ForcingBase]: List of `[Forcing]` blocks for all forcing
    definitions in a single .bc file. Actual data is stored in
    forcing[..].datablock from [hydrolib.core.io.ini.models.DataBlockINIBasedModel.datablock]."""

    _split_to_list = make_list_validator("forcing")

    @classmethod
    def _ext(cls) -> str:
        return ".bc"

    @classmethod
    def _filename(cls) -> str:
        return "boundaryconditions"

    @classmethod
    def _get_parser(cls) -> Callable:
        return cls.parse

    @classmethod
    def parse(cls, filepath: Path):
        # It's odd to have to disable parsing something as comments
        # but also need to pass it to the *flattener*.
        # This method now only supports per model settings, not per section.
        parser = Parser(ParserConfig(parse_datablocks=True, parse_comments=False))

        with filepath.open() as f:
            for line in f:
                parser.feed_line(line)

        return parser.finalize().flatten(True, False)

    def _serialize(self, _: dict) -> None:
        # We skip the passed dict for a better one.
        config = SerializerConfig(
            section_indent=0, property_indent=0, datablock_indent=0
        )
        write_ini(self._resolved_filepath, self._to_document(), config=config)


class RealTime(str, Enum):
    """
    Enum class containing the valid value for the "realtime" reserved
    keyword for real-time controlled forcing data, e.g., for hydraulic
    structures.

    This class is used inside the ForcingData Union, to force detection
    of the realtime keyword, prior to considering it a filename.
    """

    realtime = "realtime"
    """str: Realtime data source, externally provided"""


ForcingData = Union[float, RealTime, ForcingModel]
"""Data type that selects from three different types of forcing data:
*   a scalar float constant
*   "realtime" keyword, indicating externally controlled.
*   A ForcingModel coming from a .bc file.
"""
