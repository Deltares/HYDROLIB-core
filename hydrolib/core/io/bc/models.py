from abc import ABC
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Sequence, Type, Union

from pydantic.class_validators import validator
from pydantic.fields import Field
from pydantic.typing import NoneType

from hydrolib.core.basemodel import BaseModel
from hydrolib.core.io.ini.models import (
    DataBlockIniBasedModel,
    INIGeneral,
    INIModel,
    Section,
)
from hydrolib.core.io.ini.parser import Parser, ParserConfig
from hydrolib.core.io.ini.util import make_list_validator
from hydrolib.core.utils import Strict


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


class ForcingBase(DataBlockIniBasedModel):

    _header: Literal["forcing"] = "forcing"
    name: str
    function: str
    quantity: List[str]
    unit: List[str]
    datablock: List[List[float]] = []

    _make_lists = make_list_validator("quantity", "unit", "datablock")

    @classmethod
    def _supports_comments(cls):
        return False

    @classmethod
    def _duplicate_keys_as_list(cls):
        return True

    def _convert_section_to_dict(self) -> Dict:
        return self.dict(
            exclude={
                "start_line",
                "end_line",
            }
        )

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
        return v


class TimeSeries(ForcingBase):
    function: Literal["timeseries"] = "timeseries"
    timeinterpolation: TimeInterpolation = Field(alias="timeInterpolation")
    offset: float = 0.0
    factor: float = 1.0


class Harmonic(ForcingBase):
    function: Literal["harmonic"] = "harmonic"
    factor: float = 1.0


class Astronomic(ForcingBase):
    function: Literal["astronomic"] = "astronomic"
    factor: float = 1.0


class HarmonicCorrection(ForcingBase):
    function: Literal["harmoniccorrection"] = "harmoniccorrection"


class AstronomicCorrection(ForcingBase):
    function: Literal["astronomiccorrection"] = "astronomiccorrection"


class T3D(ForcingBase):
    function: Literal["t3d"] = "t3d"

    offset: float = 0.0
    factor: float = 1.0

    vertical_positions: List[float] = Field(alias="verticalPositions")
    vertical_interpolation: VerticalInterpolation = Field(alias="verticalInterpolation")
    vertical_position_type: VerticalPositionType = Field(alias="verticalPositionType")


class QHTable(ForcingBase):
    function: Literal["qhtable"] = "qhtable"


class Constant(ForcingBase):
    function: Literal["constant"] = "constant"

    offset: float = 0.0
    factor: float = 1.0


class ForcingGeneral(INIGeneral):
    fileVersion: str = "1.01"
    fileType: Literal["boundConds"] = "boundConds"


class ForcingModel(INIModel):
    general: ForcingGeneral
    forcing: List[ForcingBase]

    @classmethod
    def _ext(cls) -> str:
        return ".bc"

    @classmethod
    def _filename(cls) -> str:
        return "forcing"

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
