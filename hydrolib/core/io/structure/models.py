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
from hydrolib.core.utils import str_is_empty_or_none

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
    @classmethod
    def check_location(cls, values: dict) -> dict:
        """
        Validates the location of the structure based on the given parameters.
        For instance, if a branchId is given, then it is expected also the chainage,
        otherwise numCoordinates x and yCoordinates shall be expected.

        Args:
            values (dict): Dictionary of values validated for the new structure.

        Raises:
            ValueError: When branchid or chainage values are not valid (empty strings).
            ValueError: When the number of coordinates (x,y) do not match numCoordinates.

        Returns:
            dict: Dictionary of values validated for the new structure.
        """
        filtered_values = {k: v for k, v in values.items() if v is not None}
        structure_type = filtered_values.get("structure_type", "").lower()
        if structure_type == "compound" or issubclass(cls, Compound):
            # Compound structure does not require a location specification.
            return values

        coordinates_in_model = Structure.validate_coordinates_in_model(filtered_values)

        # Exception -> LongCulvert requires coordinates_in_model, but not branchId and chainage.
        if structure_type == "longculvert":
            assert (
                coordinates_in_model
            ), "`num/x/yCoordinates` are mandatory for a LongCulvert structure."
            return values

        branch_and_chainage_in_model = Structure.validate_branch_and_chainage_in_model(
            filtered_values
        )
        assert (
            branch_and_chainage_in_model or coordinates_in_model
        ), "Specify location either by setting `branchId` and `chainage` or `num/x/yCoordinates` fields."
        return values

    @staticmethod
    def validate_branch_and_chainage_in_model(values: dict) -> bool:
        """
        Static method to validate whether the given branchId and chainage values
        match the expectation of a new structure.

        Args:
            values (dict): Dictionary of values to be used to generate a structure.

        Raises:
            ValueError: When the value for branchId or chainage are not valid.

        Returns:
            bool: Result of valid branchId / chainage in dictionary.
        """
        branchid = values.get("branchid", None)
        if branchid is None:
            return False

        chainage = values.get("chainage", None)
        if str_is_empty_or_none(branchid) or chainage is None:
            raise ValueError(
                "A valid value for branchId and chainage is required when branchid key is specified."
            )
        return True

    @staticmethod
    def validate_coordinates_in_model(values: dict) -> bool:
        """
        Static method to validate whether the given values match the expectations
        of a structure to define its coordinates.

        Args:
            values (dict): Dictionary of values to be used to generate a structure.

        Raises:
            ValueError: When the given coordinates do not match in expected size.

        Returns:
            bool: Result of valid coordinates in dictionary.
        """
        coordinates_in_model = (
            "n_coordinates" in values
            and "x_coordinates" in values
            and "y_coordinates" in values
        )
        if not coordinates_in_model:
            return False

        n_coords = values["n_coordinates"]

        def get_coord_len(coord: str) -> int:
            if values[coord] is None:
                return 0
            return len(values[coord])

        len_x_coords = get_coord_len("x_coordinates")
        len_y_coords = get_coord_len("y_coordinates")
        if n_coords == len_x_coords == len_y_coords:
            return True
        raise ValueError(
            f"Expected {n_coords} coordinates, given {len_x_coords} for x and {len_y_coords} for y coordinates."
        )

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
                logger.warning(
                    f"Type of {cls.__name__} with id={v.get('id', '')} and type={v.get('type', '')} is not recognized."
                )
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


class Bridge(Structure):
    class Comments(Structure.Comments):
        structure_type: Optional[str] = Field(
            "Structure type; must read bridge", alias="type"
        )
        allowedflowdir: Optional[str] = Field(
            "Possible values: both, positive, negative, none.", alias="allowedFlowdir"
        )

        csdefid: Optional[str] = Field(
            "Id of Cross-Section Definition.", alias="csDefId"
        )
        shift: Optional[str] = Field(
            "Vertical shift of the cross section definition [m]. Defined positive upwards."
        )
        inletlosscoeff: Optional[str] = Field(
            "Inlet loss coefficient [-], ξ_i.",
            alias="inletLossCoeff",
        )
        outletlosscoeff: Optional[str] = Field(
            "Outlet loss coefficient [-], k.",
            alias="outletLossCoeff",
        )
        frictiontype: Optional[str] = Field(
            "Friction type, possible values are: Chezy, Manning, wallLawNikuradse, WhiteColebrook, StricklerNikuradse, Strickler, deBosBijkerk.",
            alias="frictionType",
        )
        friction: Optional[str] = Field(
            "Friction value, used in friction loss.",
            alias="friction",
        )
        length: Optional[str] = Field("Length [m], L.")

    comments: Comments = Comments()

    structure_type: Literal["bridge"] = Field("bridge", alias="type")
    allowedflowdir: FlowDirection = Field(alias="allowedFlowdir")

    csdefid: str = Field(alias="csDefId")
    shift: float = Field()
    inletlosscoeff: float = Field(alias="inletLossCoeff")
    outletlosscoeff: float = Field(alias="outletLossCoeff")
    frictiontype: str = Field(alias="frictionType")
    friction: float = Field(alias="friction")
    length: float = Field()


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
