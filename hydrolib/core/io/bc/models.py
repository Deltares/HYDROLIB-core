import logging
from abc import ABC
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Literal

from pydantic import Extra
from pydantic.class_validators import validator
from pydantic.fields import Field

from hydrolib.core.io.ini.models import DataBlockINIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.parser import Parser, ParserConfig
from hydrolib.core.io.ini.serializer import SerializerConfig, write_ini
from hydrolib.core.io.ini.util import (
    get_default,
    get_enum_validator,
    make_list_validator,
)

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


class ForcingBase(DataBlockINIBasedModel):

    _header: Literal["Forcing"] = "Forcing"
    name: str = Field(alias="name")
    function: str = Field(alias="function")
    quantity: List[str] = Field(alias="quantity")
    unit: List[str] = Field(alias="unit")

    _make_lists = make_list_validator("quantity", "unit")

    @classmethod
    def _supports_comments(cls):
        return False

    @classmethod
    def _duplicate_keys_as_list(cls):
        return True

    @validator("function")
    def _set_function(cls, value):
        return get_default(cls, "function", value)

    @classmethod
    def validate(cls, v):
        """Try to iniatialize subclass based on function field."""
        # should be replaced by discriminated unions once merged
        # https://github.com/samuelcolvin/pydantic/pull/2336
        if isinstance(v, dict):
            for c in cls.__subclasses__():
                if (
                    c.__fields__.get("function").default
                    == v.get("function", "").lower()
                ):
                    v = c(**v)
                    break
            else:
                logger.warning(
                    f"Function of {cls.__name__} with name={v.get('name', '')} and function={v.get('function', '')} is not recognized."
                )
        return v

    def _get_identifier(self, data: dict) -> str:
        return data["name"] if "name" in data else None

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
    function: Literal["harmoniccorrection"] = "harmoniccorrection"


class AstronomicCorrection(ForcingBase):
    function: Literal["astronomiccorrection"] = "astronomiccorrection"


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
        write_ini(self.filepath, self._to_document(), config=config)
