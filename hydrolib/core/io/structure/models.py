from enum import Enum
from hydrolib.core.io.ini.util import get_split_string_on_delimeter_validator
from hydrolib.core.io.ini.models import IniBasedModel
from pathlib import Path
from pydantic import Field
from typing import List, Literal, Optional, Union


# TODO: handle comment blocks
# TODO: handle duplicate keys
class Structure(IniBasedModel):
    # TODO: would we want to load this from something externally and generate these automatically
    class Comments(IniBasedModel.Comments):
        id: Optional[str] = "Unique structure id (max. 256 characters)."
        name: Optional[str] = "Given name in the user interface."
        branch_id: Optional[str] = Field(
            "Branch on which the structure is located.", alias="branchId"
        )
        chainage: Optional[str] = "Chainage on the branch (m)."

        n_coordinates: Optional[str] = Field(
            "Number of values in xCoordinates and yCoordinates", alias="numCoordinates"
        )
        x_coordinates: Optional[str] = Field(
            "x-coordinates of the location of the structure. (number of values = numCoordinates)",
            alias="xCoordinates",
        )
        y_coordinates: Optional[str] = Field(
            "y-coordinates of the location of the structure. (number of values = numCoordinates)",
            alias="yCoordinates",
        )

    comments: Comments = Comments()

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
    class Comments(Structure.Comments):
        structure_type: Optional[str] = Field(
            "Structure type; must read weir", alias="type"
        )
        allowed_flow_direction: Optional[str] = Field(
            "Possible values: both, positive, negative, none.", alias="allowedFlowdir"
        )

        crest_level: Optional[str] = Field(
            "Crest level of weir (m AD).", alias="crestLevel"
        )
        crest_width: Optional[str] = Field("Width of the weir (m).", alias="crestWidth")
        correction_coefficient: Optional[str] = Field(
            "Correction coefficient (-).", alias="corrCoeff"
        )
        use_velocity_height: Optional[str] = Field(
            "Flag indicating whether the velocity height is to be calculated or not.",
            alias="useVelocityHeight",
        )

    comments: Comments = Comments()

    structure_type: Literal["weir"] = Field("weir", alias="type")
    allowed_flow_direction: FlowDirection = Field(alias="allowedFlowdir")

    crest_level: Union[float, Path] = Field(alias="crestLevel")
    crest_width: Optional[float] = Field(None, alias="crestWidth")
    correction_coefficient: float = Field(1.0, alias="corrCoeff")
    use_velocity_height: bool = Field(True, alias="useVelocityHeight")


class UniversalWeir(Structure):
    class Comments(Structure.Comments):
        structure_type: Optional[str] = Field(
            "Structure type; must read universalWeir", alias="type"
        )
        allowed_flow_direction: Optional[str] = Field(
            "Possible values: both, positive, negative, none.", alias="allowedFlowdir"
        )

        number_of_levels: Optional[str] = Field(
            "Number of yz-Values.", alias="numLevels"
        )
        y_values: Optional[str] = Field(
            "y-values of the cross section (m). (number of values = numLevels)",
            alias="yValues",
        )
        z_values: Optional[str] = Field(
            "z-values of the cross section (m). (number of values = numLevels)",
            alias="zValues",
        )
        crest_level: Optional[str] = Field(
            "Crest level of weir (m AD).", alias="crestLevel"
        )
        discharge_coefficient: Optional[str] = Field(
            "Discharge coefficient c_e (-).", alias="dischargeCoeff"
        )

    comments: Comments = Comments()

    structure_type: Literal["universalWeir"] = Field("universalWeir", alias="type")
    allowed_flow_direction: FlowDirection = Field(alias="allowedFlowdir")

    number_of_levels: int = Field(alias="numLevels")
    y_values: List[float] = Field(alias="yValues")
    z_values: List[float] = Field(alias="zValues")
    crest_level: float = Field(alias="crestLevel")
    discharge_coefficient: float = Field(alias="dischargeCoeff")

    _split_to_list = get_split_string_on_delimeter_validator("y_values", "z_values")
