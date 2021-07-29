from abc import ABC
from enum import Enum
from typing import Any, Dict, List, Literal, Sequence, Type, Union

from pydantic.class_validators import validator
from pydantic.fields import Field
from pydantic.typing import NoneType

from hydrolib.core.basemodel import BaseModel
from hydrolib.core.io.ini.models import DataBlockIniBasedModel, Section


# TODO: This module is unfinished and should be finished as part of the bc file issue.
def transfer_keyvalue(src: Dict, target: Dict, key: str) -> None:
    if key in src:
        target[key] = src.pop(key)


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


# Note that this currently does not support the astronomic string arrays
# these need to be handled, however for the sake of validating whether
# the ini files work this has been skipped
class FunctionData(BaseModel):
    quantity: str
    unit: str
    values: Sequence[float]


class Function:
    # note that we could produce actual fields out of the dictionary, but this might complicate the use case a bit
    # furthermore we could change the data to numpy arrays, but I'll leave that to the actual implementer
    class FunctionBase(BaseModel, ABC):

        function: str
        function_data: Dict[str, FunctionData]

        class Config:
            allow_population_by_field_name = True
            arbitrary_types_allowed = False

        @classmethod
        def validate(
            cls: Type["Function.FunctionBase"], value: Any
        ) -> "Function.FunctionBase":
            if isinstance(value, Dict) and "function_data" not in value:
                # This is a pretty huge assumption, that we might need to address?
                cls._group_function_data(value)
            return super().validate(value)

        @validator("function_data", pre=True)
        def _convert_function_data_from_list(cls, value: Any):
            if isinstance(value, List) and all(
                (isinstance(v, FunctionData) for v in value)
            ):
                value = dict((fd.quantity, fd) for fd in value)
            return value

        @classmethod
        def _group_function_data(cls, data: Dict) -> None:
            function_data: Dict[str, FunctionData] = dict(
                (q, FunctionData(quantity=q, unit=u, values=vs))
                for q, u, vs in zip(
                    data.pop("quantity"), data.pop("unit"), data.pop("datablock")
                )
            )
            data["function_data"] = function_data

    class TimeSeries(FunctionBase):
        function: Literal["timeSeries"] = "timeSeries"

        time_interpolation: TimeInterpolation = Field(alias="timeInterpolation")

        offset: float = 0.0
        factor: float = 1.0

    class Harmonic(FunctionBase):
        function: Literal["harmonic"] = "harmonic"
        factor: float = 1.0

    class Astronomic(FunctionBase):
        function: Literal["astronomic"] = "astronomic"
        factor: float = 1.0

    class HarmonicCorrection(FunctionBase):
        function: Literal["harmonicCorrection"] = "harmonicCorrection"

    class AstronomicCorrection(FunctionBase):
        function: Literal["astronomicCorrection"] = "astronomicCorrection"

    class T3D(FunctionBase):
        function: Literal["t3D"] = "t3D"

        offset: float = 0.0
        factor: float = 1.0

        vertical_positions: List[float] = Field(alias="verticalPositions")
        vertical_interpolation: VerticalInterpolation = Field(
            alias="verticalInterpolation"
        )
        vertical_position_type: VerticalPositionType = Field(
            alias="verticalPositionType"
        )

    class QHTable(FunctionBase):
        function: Literal["QHTable"] = "QHTable"

    class Constant(FunctionBase):
        function: Literal["constant"] = "constant"

        offset: float = 0.0
        factor: float = 1.0


class Forcing(DataBlockIniBasedModel):
    @classmethod
    def _supports_comments(cls):
        return False

    @classmethod
    def _duplicate_keys_as_list(cls):
        return True

    _header: Literal["Forcing"] = "Forcing"

    name: str

    function: Union[
        Function.TimeSeries,
        Function.Harmonic,
        Function.Astronomic,
        Function.HarmonicCorrection,
        Function.AstronomicCorrection,
        Function.T3D,
        Function.QHTable,
        Function.Constant,
    ]

    @classmethod
    def _convert_section_content(cls, content: List) -> Dict:
        content_dict = super()._convert_section_content(content)
        cls._group_function_data(content_dict)
        return content_dict

    @classmethod
    def _convert_section(cls, section: Section) -> Dict:
        result = section.flatten(
            cls._duplicate_keys_as_list(), cls._supports_comments()
        )
        transfer_keyvalue(result, result["function"], "datablock")
        return result

    @classmethod
    def _group_function_data(cls, data: Dict) -> None:
        function_data = {"function": data["function"]}

        keys_to_transfer = [
            "offset",
            "factor",
            "verticalPositions",
            "verticalInterpolation",
            "verticalPositionType",
            "timeInterpolation",
            "quantity",
            "unit",
            "verticalPositionIndex",
        ]

        for key in keys_to_transfer:
            transfer_keyvalue(data, function_data, key)

        data["function"] = function_data
