"""
TODO Implement the following structures
- Bridge
- Generalstructure
- Long culvert
- Gate
- Dambreak

Add comments for these structures. Maybe link them to descriptions of `Field`s?
"""

import logging
from enum import Enum
from pathlib import Path
from typing import List, Literal, Optional, Set, Union

from pydantic import Field
from pydantic.class_validators import root_validator

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.util import get_split_string_on_delimiter_validator

logger = logging.getLogger(__name__)

# TODO: handle comment blocks
# TODO: handle duplicate keys
class Structure(INIBasedModel):
    # TODO: would we want to load this from something externally and generate these automatically
    class Comments(INIBasedModel.Comments):
        id: Optional[str] = "Unique structure id (max. 256 characters)."
        name: Optional[str] = "Given name in the user interface."
        branchid: Optional[str] = Field(
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

    _header: Literal["Structure"] = "Structure"

    id: str = Field("id", max_length=256)
    name: str = Field("id")
    structure_type: str = Field(alias="type")

    branchid: Optional[str] = Field(None, alias="branchId")
    chainage: Optional[float] = None

    n_coordinates: Optional[int] = Field(None, alias="numCoordinates")
    x_coordinates: Optional[List[float]] = Field(None, alias="xCoordinates")
    y_coordinates: Optional[List[float]] = Field(None, alias="yCoordinates")

    @root_validator
    def check_location(cls, values):
        assert (
            "n_coordinates" in values
            and "x_coordinates" in values
            and "y_coordinates" in values
        ) or (
            "branchid" in values and "chainage" in values
        ), "Specify location either by setting `branchid` and `chainage` or `*_coordinates` fields."
        return values

    @classmethod
    def validate(cls, v):
        """Try to iniatialize subclass based on function field."""
        # should be replaced by discriminated unions once merged
        # https://github.com/samuelcolvin/pydantic/pull/2336
        if isinstance(v, dict):
            for c in cls.__subclasses__():
                if (
                    c.__fields__.get("structure_type").default
                    == v.get("type", "").lower()
                ):
                    v = c(**v)
                    break
            else:
                logger.warning(f"Couldn't derive specific type of {cls.__name__}")
        return super().validate(v)

    def _exclude_fields(self) -> Set:
        # exclude the unset props like coordinates or branches
        if self.branchid is not None:
            exclude_set = {"n_coordinates", "x_coordinates", "y_coordinates"}
        else:
            exclude_set = {"branchid", "chainage"}
        exclude_set = super()._exclude_fields().union(exclude_set)
        return exclude_set

    def _get_identifier(self, data: dict) -> str:
        return data["id"]


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
        allowedflowdir: Optional[str] = Field(
            "Possible values: both, positive, negative, none.", alias="allowedFlowdir"
        )

        crestlevel: Optional[str] = Field(
            "Crest level of weir (m AD).", alias="crestLevel"
        )
        crestwidth: Optional[str] = Field("Width of the weir (m).", alias="crestWidth")
        corrcoeff: Optional[str] = Field(
            "Correction coefficient (-).", alias="corrCoeff"
        )
        usevelocityheight: Optional[str] = Field(
            "Flag indicating whether the velocity height is to be calculated or not.",
            alias="useVelocityHeight",
        )

    comments: Comments = Comments()

    structure_type: Literal["weir"] = Field("weir", alias="type")
    allowedflowdir: FlowDirection = Field(alias="allowedFlowdir")

    crestlevel: Union[float, Path] = Field(alias="crestLevel")
    crestwidth: Optional[float] = Field(None, alias="crestWidth")
    corrcoeff: float = Field(1.0, alias="corrCoeff")
    usevelocityheight: bool = Field(True, alias="useVelocityHeight")


class UniversalWeir(Structure):
    class Comments(Structure.Comments):
        structure_type: Optional[str] = Field(
            "Structure type; must read universalWeir", alias="type"
        )
        allowedflowdir: Optional[str] = Field(
            "Possible values: both, positive, negative, none.", alias="allowedFlowdir"
        )

        numlevels: Optional[str] = Field("Number of yz-Values.", alias="numLevels")
        yvalues: Optional[str] = Field(
            "y-values of the cross section (m). (number of values = numLevels)",
            alias="yValues",
        )
        zvalues: Optional[str] = Field(
            "z-values of the cross section (m). (number of values = numLevels)",
            alias="zValues",
        )
        crestlevel: Optional[str] = Field(
            "Crest level of weir (m AD).", alias="crestLevel"
        )
        dischargecoeff: Optional[str] = Field(
            "Discharge coefficient c_e (-).", alias="dischargeCoeff"
        )

    comments: Comments = Comments()

    structure_type: Literal["universalWeir"] = Field("universalWeir", alias="type")
    allowedflowdir: FlowDirection = Field(alias="allowedFlowdir")

    numlevels: int = Field(alias="numLevels")
    yvalues: List[float] = Field(alias="yValues")
    zvalues: List[float] = Field(alias="zValues")
    crestlevel: float = Field(alias="crestLevel")
    dischargecoeff: float = Field(alias="dischargeCoeff")

    _split_to_list = get_split_string_on_delimiter_validator("yvalues", "zvalues")


class CulvertSubType(str, Enum):
    culvert = "culvert"
    invertedSiphon = "invertedSiphon"


class Culvert(Structure):

    structure_type: Literal["culvert"] = Field("culvert", alias="type")
    allowedflowdir: FlowDirection = Field(alias="allowedFlowdir")

    leftlevel: float = Field(alias="leftLevel")
    rightlevel: float = Field(alias="rightLevel")
    csdefid: str = Field(alias="csDefId")
    length: float = Field(alias="length")
    inletlosscoeff: float = Field(alias="inletlossCoeff")
    outletlosscoeff: float = Field(alias="outletLossCoeff")
    valveonoff: bool = Field(alias="valveOnOff")
    valveopeningheight: Union[float, Path] = Field(alias="valveOpeningHeight")
    numlosscoeff: int = Field(alias="numLossCoeff")
    relopening: List[float] = Field(alias="relOpening")
    losscoeff: List[float] = Field(alias="lossCoeff")
    bedfrictiontype: str = Field(alias="bedFrictionType")
    bedfriction: float = Field(alias="bedFriction")
    subtype: CulvertSubType = Field(alias="subType")
    bendlosscoeff: float = Field(alias="bendLossCoeff")

    _split_to_list = get_split_string_on_delimiter_validator("relopening", "losscoeff")


class Pump(Structure):

    structure_type: Literal["pump"] = Field("pump", alias="type")

    orientation: str
    controlside: str = Field(alias="controlSide")  # TODO Enum
    numstages: int = Field(0, alias="numStages")
    capacity: Union[float, Path]

    startlevelsuctionside: List[float] = Field(alias="startLevelSuctionSide")
    stoplevelsuctionside: List[float] = Field(alias="stopLevelSuctionSide")
    startleveldeliveryside: List[float] = Field(alias="startLevelDeliverySide")
    stopleveldeliveryside: List[float] = Field(alias="stopLevelDeliverySide")
    numreductionlevels: int = Field(0, alias="numReductionLevels")
    head: List[float]
    reductionfactor: List[float] = Field(alias="reductionFactor")

    _split_to_list = get_split_string_on_delimiter_validator(
        "startlevelsuctionside",
        "stoplevelsuctionside",
        "startleveldeliveryside",
        "stopleveldeliveryside",
        "head",
        "reductionfactor",
    )


class Compound(Structure):

    structure_type: Literal["compound"] = Field("compound", alias="type")
    numstructures: int = Field(alias="numStructures")
    structureids: List[str] = Field(alias="structureIds")

    _split_to_list = get_split_string_on_delimiter_validator(
        "structureids", delimiter=";"
    )


class Orifice(Structure):

    structure_type: Literal["orifice"] = Field("orifice", alias="type")
    allowedflowdir: FlowDirection = Field(alias="allowedFlowdir")

    crestlevel: Union[float, Path] = Field(alias="crestLevel")
    crestwidth: Optional[float] = Field(None, alias="crestWidth")
    gateloweredgelevel: Union[float, Path] = Field(alias="gateLowerEdgeLevel")
    corrcoeff: float = Field(1.0, alias="corrCoeff")
    usevelocityheight: bool = Field(True, alias="useVelocityHeight")

    # TODO Use a validator here to check the optionals related to the bool field
    uselimitflowpos: bool = Field(False, alias="useLimitFlowPos")
    limitflowpos: Optional[float] = Field(alias="limitFlowPos")

    uselimitflowneg: bool = Field(False, alias="useLimitflowNeg")
    limitflowneg: Optional[float] = Field(alias="limitFlowneg")


class StructureGeneral(INIGeneral):
    _header: Literal["General"] = "General"
    fileVersion: str = "3.00"
    fileType: Literal["structure"] = "structure"


class StructureModel(INIModel):
    general: StructureGeneral = StructureGeneral()
    structure: List[Structure] = []

    @classmethod
    def _ext(cls) -> str:
        return ".ini"

    @classmethod
    def _filename(cls) -> str:
        return "structures"
