from abc import ABC
from enum import Enum
from hydrolib.core.io.ini.models import Property, Section
from pathlib import Path
from hydrolib.core.basemodel import BaseModel
from pydantic import validator, Field
from pydantic.main import Extra
from typing import Any, Dict, List, Literal, Optional, Type, Union


# TODO: handle comment blocks
# TODO: handle duplicate keys
class IniBasedModel(BaseModel, ABC):
    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True
        arbitrary_types_allowed = False

    @classmethod
    def validate(cls: Type["IniBasedModel"], value: Any) -> "IniBasedModel":
        if isinstance(value, Section):
            converted_content = cls._convert_section_content(value.content)
            underlying_dict = cls._convert_section_to_dict(value)
            value = {**underlying_dict, **converted_content}

        return super().validate(value)

    @classmethod
    def _convert_section_to_dict(cls, value: Section) -> Dict:
        return value.dict(
            exclude={
                "start_line",
                "end_line",
                "datablock",
                "content",
            }
        )

    @classmethod
    def _convert_section_content(cls, content: List):
        # TODO add comment here
        return dict((v.key, v.value) for v in content if isinstance(v, Property))


class DataBlockIniBasedModel(IniBasedModel):
    @classmethod
    def _convert_section_to_dict(cls, value: Section) -> Dict:
        return value.dict(
            exclude={
                "start_line",
                "end_line",
                "content",
            }
        )


class Structure(IniBasedModel):
    header: Literal["Structure"] = "Structure"

    id: str = Field("id", max_length=256)
    name: str = Field("id")

    # TODO: Note that either branch_id and chainage needs to be defined, or the coordinates. This shoud be either validated or refactored.
    branch_id: Optional[str] = Field(None, alias="branchId")
    chainage: Optional[float] = None

    n_coordinates: Optional[int] = Field(None, alias="numCoordinates")
    x_coordinates: Optional[List[float]] = Field(None, alias="xCoordinates")
    y_coordinates: Optional[List[float]] = Field(None, alias="yCoordinates")


class FlowDirection(str, Enum):
    none = "none"
    positive = "positive"
    negative = "negative"
    both = "both"


class Weir(Structure):
    structure_type: Literal["weir"] = Field("weir", alias="type")
    allowed_flow_direction: FlowDirection = Field(alias="allowedFlowdir")

    crest_level: Union[float, Path] = Field(alias="crestLevel")
    crest_width: Optional[float] = Field(None, alias="crestWidth")
    correction_coefficient: float = Field(1.0, alias="corrCoeff")
    use_velocity_height: bool = Field(True, alias="useVelocityHeight")


class UniversalWeir(Structure):
    structure_type: Literal["universalWeir"] = Field("universalWeir", alias="type")
    allowed_flow_direction: FlowDirection = Field(alias="allowedFlowdir")

    number_of_levels: int = Field(alias="numLevels")
    y_values: List[float] = Field(alias="yValues")
    z_values: List[float] = Field(alias="zValues")
    crest_level: float = Field(alias="crestLevel")
    discharge_coefficient: float = Field(alias="dischargeCoeff")

    @validator("y_values", "z_values", pre=True)
    def split_value_lists(cls, v):
        if isinstance(v, str):
            v = v.split()
        return v
