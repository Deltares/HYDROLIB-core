from abc import ABC
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Literal

from pydantic.fields import Field
from pydantic import Extra

from hydrolib.core.io.ini.models import DataBlockINIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.parser import Parser, ParserConfig
from hydrolib.core.io.ini.serializer import SerializerConfig, write_ini
from hydrolib.core.io.ini.util import make_list_validator


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

    _header: Literal["forcing"] = "forcing"
    name: str
    function: str
    quantity: List[str]
    unit: List[str]

    _make_lists = make_list_validator("quantity", "unit")

    @classmethod
    def _supports_comments(cls):
        return False

    @classmethod
    def _duplicate_keys_as_list(cls):
        return True

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

    def _get_identifier(self, data: dict) -> str:
        return data["name"] if "name" in data else None

    class Config:
        extra = Extra.ignore


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
