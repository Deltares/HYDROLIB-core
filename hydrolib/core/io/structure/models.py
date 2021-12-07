"""
TODO Implement the following structures
- Bridge
- Generalstructure
- Long culvert
- Gate

Add comments for these structures. Maybe link them to descriptions of `Field`s?
"""

import logging
from enum import Enum
from pathlib import Path
from typing import List, Literal, Optional, Set, Union

from pydantic import Field
from pydantic.class_validators import root_validator, validator

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.util import (
    get_enum_validator,
    get_from_subclass_defaults,
    get_split_string_on_delimiter_validator,
)
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

        numcoordinates: Optional[str] = Field(
            "Number of values in xCoordinates and yCoordinates", alias="numCoordinates"
        )
        xcoordinates: Optional[str] = Field(
            "x-coordinates of the location of the structure. (number of values = numCoordinates)",
            alias="xCoordinates",
        )
        ycoordinates: Optional[str] = Field(
            "y-coordinates of the location of the structure. (number of values = numCoordinates)",
            alias="yCoordinates",
        )

    comments: Comments = Comments()

    _header: Literal["Structure"] = "Structure"

    id: str = Field("id", max_length=256, alias="id")
    name: str = Field("id", alias="name")
    type: str = Field(alias="type")

    branchid: Optional[str] = Field(None, alias="branchId")
    chainage: Optional[float] = Field(None, alias="chainage")

    numcoordinates: Optional[int] = Field(None, alias="numCoordinates")
    xcoordinates: Optional[List[float]] = Field(None, alias="xCoordinates")
    ycoordinates: Optional[List[float]] = Field(None, alias="yCoordinates")

    _split_to_list = get_split_string_on_delimiter_validator(
        "xcoordinates", "ycoordinates"
    )

    @validator("type", pre=True)
    def _validate_type(cls, value):
        return get_from_subclass_defaults(Structure, "type", value)

    @root_validator
    @classmethod
    def check_location(cls, values: dict) -> dict:
        """
        Validates the location of the structure based on the given parameters.
        For instance, if a branchid is given, then it is expected also the chainage,
        otherwise numcoordinates xcoordinates and ycoordinates shall be expected.

        Args:
            values (dict): Dictionary of values validated for the new structure.

        Raises:
            ValueError: When branchid or chainage values are not valid (empty strings).
            ValueError: When the number of xcoordinates and ycoordinates do not match numcoordinates.

        Returns:
            dict: Dictionary of values validated for the new structure.
        """
        filtered_values = {k: v for k, v in values.items() if v is not None}
        structype = filtered_values.get("type", "").lower()

        # TODO This seems to be a bit of a hack.
        if not (structype == "compound" or issubclass(cls, (Compound, Dambreak))):
            # Compound structure does not require a location specification.
            only_coordinates_structures = dict(
                longculvert="LongCulvert", dambreak="Dambreak"
            )
            coordinates_in_model = Structure.validate_coordinates_in_model(
                filtered_values
            )

            # Exception -> LongCulvert requires coordinates_in_model, but not branchId and chainage.
            if structype in only_coordinates_structures.keys():
                assert (
                    coordinates_in_model
                ), f"`num/x/yCoordinates` are mandatory for a {only_coordinates_structures[structype]} structure."

            branch_and_chainage_in_model = (
                Structure.validate_branch_and_chainage_in_model(filtered_values)
            )
            assert (
                branch_and_chainage_in_model or coordinates_in_model
            ), "Specify location either by setting `branchId` and `chainage` or `num/x/yCoordinates` fields."

        return values

    @staticmethod
    def validate_branch_and_chainage_in_model(values: dict) -> bool:
        """
        Static method to validate whether the given branchid and chainage values
        match the expectation of a new structure.

        Args:
            values (dict): Dictionary of values to be used to generate a structure.

        Raises:
            ValueError: When the value for branchid or chainage are not valid.

        Returns:
            bool: Result of valid branchid / chainage in dictionary.
        """
        branchid = values.get("branchid", None)
        if branchid is None:
            return False

        chainage = values.get("chainage", None)
        if str_is_empty_or_none(branchid) or chainage is None:
            raise ValueError(
                "A valid value for branchId and chainage is required when branchId key is specified."
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
            ValueError: When the given coordinates is less than 2.
            ValueError: When the given coordinates do not match in expected size.

        Returns:
            bool: Result of valid coordinates in dictionary.
        """
        searched_keys = ["numcoordinates", "xcoordinates", "ycoordinates"]
        if any(values.get(k, None) is None for k in searched_keys):
            return False

        n_coords = values["numcoordinates"]
        if n_coords < 2:
            raise ValueError(
                f"Expected at least 2 coordinates, but only {n_coords} declared."
            )

        def get_coord_len(coord: str) -> int:
            if values[coord] is None:
                return 0
            return len(values[coord])

        len_x_coords = get_coord_len("xcoordinates")
        len_y_coords = get_coord_len("ycoordinates")
        if n_coords == len_x_coords == len_y_coords:
            return True
        raise ValueError(
            f"Expected {n_coords} coordinates, given {len_x_coords} for xCoordinates and {len_y_coords} for yCoordinates."
        )

    @classmethod
    def validate(cls, v):
        """Try to iniatialize subclass based on the `type` field.
        This field is compared to each `type` field of the derived models of `Structure`.
        The derived model with an equal structure type will be initialized.

        Raises:
            ValueError: When the given type is not a known structure type.
        """

        # should be replaced by discriminated unions once merged
        # https://github.com/samuelcolvin/pydantic/pull/2336
        if isinstance(v, dict):
            for c in cls.__subclasses__():
                if (
                    c.__fields__.get("type").default.lower()
                    == v.get("type", "").lower()
                ):
                    v = c(**v)
                    break
            else:
                raise ValueError(
                    f"Type of {cls.__name__} with id={v.get('id', '')} and type={v.get('type', '')} is not recognized."
                )
        return super().validate(v)

    def _exclude_fields(self) -> Set:
        # exclude the unset props like coordinates or branches
        if self.branchid is not None:
            exclude_set = {"numcoordinates", "xcoordinates", "ycoordinates"}
        else:
            exclude_set = {"branchid", "chainage"}
        exclude_set = super()._exclude_fields().union(exclude_set)
        return exclude_set

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("id")


class FlowDirection(str, Enum):
    none = "none"
    positive = "positive"
    negative = "negative"
    both = "both"
    allowedvaluestext = "Possible values: both, positive, negative, none."


class Weir(Structure):
    class Comments(Structure.Comments):
        type: Optional[str] = Field("Structure type; must read weir", alias="type")
        allowedflowdir: Optional[str] = Field(
            FlowDirection.allowedvaluestext, alias="allowedFlowdir"
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

    type: Literal["weir"] = Field("weir", alias="type")
    allowedflowdir: Optional[FlowDirection] = Field(
        FlowDirection.both, alias="allowedFlowDir"
    )

    crestlevel: Union[float, Path] = Field(alias="crestLevel")
    crestwidth: Optional[float] = Field(None, alias="crestWidth")
    corrcoeff: float = Field(1.0, alias="corrCoeff")
    usevelocityheight: bool = Field(True, alias="useVelocityHeight")

    _flowdirection_validator = get_enum_validator("allowedflowdir", enum=FlowDirection)


class UniversalWeir(Structure):
    class Comments(Structure.Comments):
        type: Optional[str] = Field(
            "Structure type; must read universalWeir", alias="type"
        )
        allowedflowdir: Optional[str] = Field(
            FlowDirection.allowedvaluestext, alias="allowedFlowdir"
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

    type: Literal["universalWeir"] = Field("universalWeir", alias="type")
    allowedflowdir: FlowDirection = Field(alias="allowedFlowDir")

    numlevels: int = Field(alias="numLevels")
    yvalues: List[float] = Field(alias="yValues")
    zvalues: List[float] = Field(alias="zValues")
    crestlevel: float = Field(alias="crestLevel")
    dischargecoeff: float = Field(alias="dischargeCoeff")

    _split_to_list = get_split_string_on_delimiter_validator("yvalues", "zvalues")
    _flowdirection_validator = get_enum_validator("allowedflowdir", enum=FlowDirection)


class CulvertSubType(str, Enum):
    culvert = "culvert"
    invertedSiphon = "invertedSiphon"


class Culvert(Structure):

    type: Literal["culvert"] = Field("culvert", alias="type")
    allowedflowdir: FlowDirection = Field(alias="allowedFlowDir")

    leftlevel: float = Field(alias="leftLevel")
    rightlevel: float = Field(alias="rightLevel")
    csdefid: str = Field(alias="csDefId")
    length: float = Field(alias="length")
    inletlosscoeff: float = Field(alias="inletLossCoeff")
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
    _flowdirection_validator = get_enum_validator("allowedflowdir", enum=FlowDirection)
    _subtype_validator = get_enum_validator("subtype", enum=CulvertSubType)


class Pump(Structure):

    type: Literal["pump"] = Field("pump", alias="type")

    orientation: str = Field(alias="orientation")
    controlside: str = Field(alias="controlSide")  # TODO Enum
    numstages: int = Field(0, alias="numStages")
    capacity: Union[float, Path] = Field(alias="capacity")

    startlevelsuctionside: List[float] = Field(alias="startLevelSuctionSide")
    stoplevelsuctionside: List[float] = Field(alias="stopLevelSuctionSide")
    startleveldeliveryside: List[float] = Field(alias="startLevelDeliverySide")
    stopleveldeliveryside: List[float] = Field(alias="stopLevelDeliverySide")
    numreductionlevels: int = Field(0, alias="numReductionLevels")
    head: List[float] = Field(alias="head")
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

    type: Literal["compound"] = Field("compound", alias="type")
    numstructures: int = Field(alias="numStructures")
    structureids: List[str] = Field(alias="structureIds")

    _split_to_list = get_split_string_on_delimiter_validator(
        "structureids", delimiter=";"
    )


class Orifice(Structure):

    type: Literal["orifice"] = Field("orifice", alias="type")
    allowedflowdir: Optional[FlowDirection] = Field(
        FlowDirection.both, alias="allowedFlowDir"
    )

    crestlevel: Union[float, Path] = Field(alias="crestLevel")
    crestwidth: Optional[float] = Field(None, alias="crestWidth")
    gateloweredgelevel: Union[float, Path] = Field(alias="gateLowerEdgeLevel")
    corrcoeff: float = Field(1.0, alias="corrCoeff")
    usevelocityheight: bool = Field(True, alias="useVelocityHeight")

    # TODO Use a validator here to check the optionals related to the bool field
    uselimitflowpos: Optional[bool] = Field(False, alias="useLimitFlowPos")
    limitflowpos: Optional[float] = Field(alias="limitFlowPos")

    uselimitflowneg: Optional[bool] = Field(False, alias="useLimitFlowNeg")
    limitflowneg: Optional[float] = Field(alias="limitFlowNeg")

    _flowdirection_validator = get_enum_validator("allowedflowdir", enum=FlowDirection)

    @validator("limitflowpos", always=True)
    @classmethod
    def _validate_limitflowpos(cls, v, values):
        return cls._validate_limitflow(v, values, "limitFlowPos", "useLimitFlowPos")

    @validator("limitflowneg", always=True)
    @classmethod
    def _validate_limitflowneg(cls, v, values):
        return cls._validate_limitflow(v, values, "limitFlowNeg", "useLimitFlowNeg")

    @classmethod
    def _validate_limitflow(cls, v, values, limitflow: str, uselimitflow: str):
        if v is None and values[uselimitflow.lower()] == True:
            raise ValueError(
                f"{limitflow} should be defined when {uselimitflow} is true"
            )

        return v


class DambreakAlgorithm(int, Enum):
    van_der_knaap = 1  # "van der Knaap, 2000"
    verheij_van_der_knaap = 2  # "Verheij-van der Knaap, 2002"
    timeseries = 3  # "Predefined time series, dambreakLevelsAndWidths."

    @property
    def description(self) -> str:
        """
        Property to return the description of the enums defined above.
        Useful for comments in output files.

        Returns:
            str: Description for the current enum.
        """
        description_dict = dict(
            van_der_knaap="van der Knaap, 2000",
            verheij_van_der_knaap="Verheij-van der Knaap, 2002",
            timeseries="Predefined time series, dambreakLevelsAndWidths",
        )
        return description_dict[self.name]


class Dambreak(Structure):
    class Comments(Structure.Comments):
        type: Optional[str] = Field("Structure type; must read dambreak", alias="type")
        startlocationx: Optional[str] = Field(
            "x-coordinate of breach starting point.", alias="startLocationX"
        )
        startlocationy: Optional[str] = Field(
            "y-coordinate of breach starting point.", alias="startLocationY"
        )
        algorithm: Optional[str] = Field(
            "Breach growth algorithm. Possible values are: 1 (van der Knaap (2000)), 2 (Verheij–van der Knaap (2002)), 3: Predefined time series, see dambreakLevelsAndWidths",
            alias="algorithm",
        )
        crestlevelini: Optional[str] = Field(
            "Initial breach level zcrest level [m AD].", alias="crestLevelIni"
        )
        breachwidthini: Optional[str] = Field(
            "Initial breach width B0 [m].", alias="breachWidthIni"
        )
        crestlevelmin: Optional[str] = Field(
            "Minimal breach level zmin [m AD].", alias="crestLevelMin"
        )
        t0: Optional[str] = Field("Breach start time Tstart [s].", alias="t0")
        timetobreachtomaximumdepth: Optional[str] = Field(
            "tPhase 1 [s].", alias="timeToBreachToMaximumDepth"
        )
        f1: Optional[str] = Field("Factor f1 [-]", alias="f1")
        f2: Optional[str] = Field("Factor f2 [-]", alias="f2")
        ucrit: Optional[str] = Field(
            "Critical flow velocity uc for erosion [m/s].", alias="uCrit"
        )
        waterlevelupstreamlocationx: Optional[str] = Field(
            "(optional) x-coordinate of custom upstream water level point.",
            alias="waterLevelUpstreamLocationX",
        )
        waterlevelupstreamlocationy: Optional[str] = Field(
            "(optional) y-coordinate of custom upstream water level point.",
            alias="waterLevelUpstreamLocationY",
        )
        waterleveldownstreamlocationx: Optional[str] = Field(
            "(optional) x-coordinate of custom downstream water level point.",
            alias="waterLevelDownstreamLocationX",
        )
        waterleveldownstreamlocationy: Optional[str] = Field(
            "(optional) y-coordinate of custom downstream water level point.",
            alias="waterLevelDownstreamLocationY",
        )
        waterlevelupstreamnodeid: Optional[str] = Field(
            "(optional) Node Id of custom upstream water level point.",
            alias="waterLevelUpstreamNodeId",
        )
        waterleveldownstreamnodeid: Optional[str] = Field(
            "(optional) Node Id of custom downstream water level point.",
            alias="waterLevelDownstreamNodeId",
        )
        dambreaklevelsandwidths: Optional[str] = Field(
            "(only when algorithm=3) Filename of <*.tim> file (Section C.4) containing the breach levels and widths.",
            alias="dambreakLevelsAndWidths",
        )

    comments: Comments = Comments()
    type: Literal["dambreak"] = Field("dambreak", alias="type")
    startlocationx: float = Field(alias="startLocationX")
    startlocationy: float = Field(alias="startLocationY")
    algorithm: DambreakAlgorithm = Field(alias="algorithm")

    crestlevelini: float = Field(alias="crestLevelIni")
    breachwidthini: float = Field(alias="breachWidthIni")
    crestlevelmin: float = Field(alias="crestLevelMin")
    t0: float = Field(alias="t0")
    timetobreachtomaximumdepth: float = Field(alias="timeToBreachToMaximumDepth")
    f1: float = Field(alias="f1")
    f2: float = Field(alias="f2")
    ucrit: float = Field(alias="uCrit")
    waterlevelupstreamlocationx: Optional[float] = Field(
        alias="waterLevelUpstreamLocationX"
    )
    waterlevelupstreamlocationy: Optional[float] = Field(
        alias="waterLevelUpstreamLocationY"
    )
    waterleveldownstreamlocationx: Optional[float] = Field(
        alias="waterLevelDownstreamLocationX"
    )
    waterleveldownstreamlocationy: Optional[float] = Field(
        alias="waterLevelDownstreamLocationY"
    )
    waterlevelupstreamnodeid: Optional[str] = Field(alias="waterLevelUpstreamNodeId")
    waterleveldownstreamnodeid: Optional[str] = Field(
        alias="waterLevelDownstreamNodeId"
    )
    dambreaklevelsandwidths: Optional[Path] = Field(alias="dambreakLevelsAndWidths")

    @validator("algorithm", pre=True)
    @classmethod
    def validate_algorithm(cls, value: str) -> DambreakAlgorithm:
        """
        Validates the algorithm parameter for the dambreak structure.

        Args:
            value (int): algorithm value read from the user's input.

        Raises:
            ValueError: When the value given is not of type int.
            ValueError: When the value given is not in the range [1,3]

        Returns:
            int: Validated value.
        """
        int_value = -1
        try:
            int_value = int(value)
        except Exception:
            raise ValueError("Dambreak algorithm value should be of type int.")
        if 0 < int_value <= 3:
            return DambreakAlgorithm(int_value)
        raise ValueError("Dambreak algorithm value should be 1, 2 or 3.")

    @validator("dambreaklevelsandwidths")
    @classmethod
    def validate_dambreak_levels_and_widths(
        cls, field_value: Optional[Path], values: dict
    ) -> Optional[Path]:
        """
        Validates whether a dambreak can be created with the given dambreakLevelsAndWidths
        property. This property should be given when the algorithm value is 3.

        Args:
            field_value (Optional[Path]): Value given for dambreakLevelsAndWidths.
            values (dict): Dictionary of values already validated (assuming algorithm is in it).

        Raises:
            ValueError: When algorithm value is not 3 and field_value has a value.

        Returns:
            Optional[Path]: The value given for dambreakLevelsAndwidths.
        """
        # Retrieve the algorithm value (if not found use 0).
        algorithm_value = values.get("algorithm", 0)
        if field_value is not None and algorithm_value != 3:
            # dambreakLevelsAndWidths can only be set when algorithm = 3
            raise ValueError(
                f"Dambreak field dambreakLevelsAndWidths can only be set when algorithm = 3, current value: {algorithm_value}."
            )
        return field_value

    @root_validator
    @classmethod
    def check_location(cls, values: dict) -> dict:
        """
        Verifies whether the location for this structure contains valid values for
        numCoordinates, xCoordinates and yCoordinates or instead is using a polyline file.

        Args:
            values (dict): Dictionary of validated values to create a Dambreak.

        Raises:
            ValueError: When the values dictionary does not contain valid coordinates or polyline file..

        Returns:
            dict: Dictionary of validated values.
        """
        if (
            Structure.validate_coordinates_in_model(values)
            or values.get("polylinefile", None) is not None
        ):
            return values

        raise ValueError(
            "`num/x/yCoordinates` or `polylineFile` are mandatory for a Dambreak structure."
        )


class Bridge(Structure):
    class Comments(Structure.Comments):
        type: Optional[str] = Field("Structure type; must read bridge", alias="type")
        allowedflowdir: Optional[str] = Field(
            FlowDirection.allowedvaluestext, alias="allowedFlowdir"
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

    type: Literal["bridge"] = Field("bridge", alias="type")
    allowedflowdir: FlowDirection = Field(alias="allowedFlowdir")

    csdefid: str = Field(alias="csDefId")
    shift: float
    inletlosscoeff: float = Field(alias="inletLossCoeff")
    outletlosscoeff: float = Field(alias="outletLossCoeff")
    frictiontype: str = Field(alias="frictionType")
    friction: float
    length: float


class StructureGeneral(INIGeneral):
    _header: Literal["General"] = "General"
    fileversion: str = Field("3.00", alias="fileVersion")
    filetype: Literal["structure"] = Field("structure", alias="fileType")


class StructureModel(INIModel):
    general: StructureGeneral = StructureGeneral()
    structure: List[Structure] = []

    @classmethod
    def _ext(cls) -> str:
        return ".ini"

    @classmethod
    def _filename(cls) -> str:
        return "structures"
