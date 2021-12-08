import logging
from enum import Enum
from pathlib import Path
from typing import Callable, List, Literal, NamedTuple, Optional, Set

from pydantic import Extra
from pydantic.class_validators import root_validator, validator
from pydantic.fields import Field

from hydrolib.core.io.ini.io_models import Property, Section
from hydrolib.core.io.ini.models import DataBlockINIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.parser import Parser, ParserConfig
from hydrolib.core.io.ini.serializer import SerializerConfig, write_ini
from hydrolib.core.io.ini.util import get_enum_validator, get_from_subclass_defaults

logger = logging.getLogger(__name__)


class VerticalInterpolation(str, Enum):
    linear = "linear"
    log = "log"
    block = "block"


class VerticalPositionType(str, Enum):
    percentage_bed = "percBed"
    z_bed = "ZBed"


class TimeInterpolation(str, Enum):
    linear = "linear"
    block_from = "blockFrom"
    block_to = "blockTo"


class QuantityUnitPair(NamedTuple):
    quantity: str
    unit: str

    def _to_properties(self):
        yield Property(key="quantity", value=self.quantity)
        yield Property(key="unit", value=self.unit)


class ForcingBase(DataBlockINIBasedModel):

    _header: Literal["Forcing"] = "Forcing"
    name: str = Field(alias="name")
    function: str = Field(alias="function")
    quantityunitpair: List[QuantityUnitPair]

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
            values[quantityunitpairkey] = [(quantities, units)]
            return values

        if isinstance(quantities, list) and isinstance(units, list):
            if not len(quantities) == len(units):
                raise ValueError(
                    "Number of quantities should be equal to number of units"
                )

            values[quantityunitpairkey] = [
                (quantity, unit) for quantity, unit in zip(quantities, units)
            ]
            return values

        raise ValueError("Number of quantities should be equal to number of units")

    @validator("function", pre=True)
    def _set_function(cls, value):
        return get_from_subclass_defaults(ForcingBase, "function", value)

    @classmethod
    def validate(cls, v):
        """Try to iniatialize subclass based on the `function` field.
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
    function: Literal["timeseries"] = "timeseries"
    timeinterpolation: TimeInterpolation = Field(alias="timeInterpolation")
    offset: float = Field(0.0, alias="offset")
    factor: float = Field(1.0, alias="factor")

    _timeinterpolation_validator = get_enum_validator(
        "timeinterpolation", enum=TimeInterpolation
    )


class Harmonic(ForcingBase):
    function: Literal["harmonic"] = "harmonic"
    factor: float = Field(1.0, alias="factor")


class Astronomic(ForcingBase):
    function: Literal["astronomic"] = "astronomic"
    factor: float = Field(1.0, alias="factor")


class HarmonicCorrection(ForcingBase):
    function: Literal["harmonic-correction"] = "harmonic-correction"


class AstronomicCorrection(ForcingBase):
    function: Literal["astronomic-correction"] = "astronomic-correction"


class T3D(ForcingBase):
    function: Literal["t3d"] = "t3d"

    offset: float = Field(0.0, alias="offset")
    factor: float = Field(1.0, alias="factor")

    verticalpositions: List[float] = Field(alias="verticalPositions")
    verticalinterpolation: VerticalInterpolation = Field(alias="verticalInterpolation")
    verticalpositiontype: VerticalPositionType = Field(alias="verticalPositionType")

    _verticalinterpolation_validator = get_enum_validator(
        "verticalinterpolation", enum=VerticalInterpolation
    )
    _verticalpositiontype_validator = get_enum_validator(
        "verticalpositiontype", enum=VerticalPositionType
    )


class QHTable(ForcingBase):
    function: Literal["qhtable"] = "qhtable"


class Constant(ForcingBase):
    function: Literal["constant"] = "constant"

    offset: float = Field(0.0, alias="offset")
    factor: float = Field(1.0, alias="factor")


class ForcingGeneral(INIGeneral):
    fileversion: str = Field("1.01", alias="fileVersion")
    filetype: Literal["boundConds"] = Field("boundConds", alias="fileType")


class ForcingModel(INIModel):
    general: ForcingGeneral = ForcingGeneral()
    forcing: List[ForcingBase] = []

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
        config = SerializerConfig(section_indent=0, property_indent=4)
        write_ini(self._resolved_filepath, self._to_document(), config=config)
