from enum import Enum
from hydrolib.core.io.ini.models import IniBasedModel
from pathlib import Path
from pydantic import validator, Field
from typing import List, Literal, Optional, Union


# TODO: handle comment blocks
# TODO: handle duplicate keys
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
