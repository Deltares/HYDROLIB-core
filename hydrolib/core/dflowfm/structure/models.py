"""
structure namespace for storing the contents of an [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]'s structure file.
"""
# TODO Implement the following structures
# - Gate

import logging
from enum import Enum
from operator import gt, ne
from typing import Dict, List, Literal, Optional, Set, Union

from pydantic import Field
from pydantic.class_validators import root_validator, validator

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.friction.models import FrictionType
from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.util import (
    get_enum_validator,
    get_from_subclass_defaults,
    get_split_string_on_delimiter_validator,
    make_list_validator,
    validate_conditionally,
    validate_correct_length,
    validate_forbidden_fields,
    validate_required_fields,
)
from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.core.utils import str_is_empty_or_none

logger = logging.getLogger(__name__)

ForcingData = Union[float, TimModel, ForcingModel]

# TODO: handle comment blocks
# TODO: handle duplicate keys
class Structure(INIBasedModel):
    # TODO: would we want to load this from something externally and generate these automatically
    class Comments(INIBasedModel.Comments):
        id: Optional[str] = "Unique structure id (max. 256 characters)."
        name: Optional[str] = "Given name in the user interface."
        polylinefile: Optional[str] = Field(
            "*.pli; Polyline geometry definition for 2D structure.",
            alias="polylinefile",
        )
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

    polylinefile: Optional[DiskOnlyFileModel] = Field(None, alias="polylinefile")

    branchid: Optional[str] = Field(None, alias="branchId")
    chainage: Optional[float] = Field(None, alias="chainage")

    numcoordinates: Optional[int] = Field(None, alias="numCoordinates")
    xcoordinates: Optional[List[float]] = Field(None, alias="xCoordinates")
    ycoordinates: Optional[List[float]] = Field(None, alias="yCoordinates")

    _loc_coord_fields = {"numcoordinates", "xcoordinates", "ycoordinates"}
    _loc_branch_fields = {"branchid", "chainage"}
    _loc_all_fields = _loc_coord_fields | _loc_branch_fields

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

        if structype == "compound" or issubclass(cls, (Compound)):
            # Compound structure does not require a location specification.
            return values

        # Backwards compatibility for old-style polylinefile input field (instead of num/x/yCoordinates):
        polyline_compatible_structures = dict(
            pump="Pump",
            dambreak="Dambreak",
            gate="Gate",
            weir="Weir",
            generalstructure="GeneralStructure",
        )
        polylinefile_in_model = (
            structype in polyline_compatible_structures.keys()
            and filtered_values.get("polylinefile") is not None
        )

        # No branchId+chainage for some structures:
        only_coordinates_structures = dict(
            longculvert="LongCulvert", dambreak="Dambreak"
        )
        coordinates_in_model = Structure.validate_coordinates_in_model(filtered_values)

        # Error: do not allow both x/y and polyline file:
        assert not (
            polylinefile_in_model and coordinates_in_model
        ), f"`Specify location either by `num/x/yCoordinates` or `polylinefile`, but not both."

        # Error: require x/y or polyline file:
        if (
            structype in polyline_compatible_structures.keys()
            and structype in only_coordinates_structures.keys()
        ):
            assert (
                coordinates_in_model or polylinefile_in_model
            ), f"Specify location either by setting `num/x/yCoordinates` or `polylinefile` fields for a {polyline_compatible_structures[structype]} structure."

        # Error: Some structures require coordinates_in_model, but not branchId and chainage.
        if (
            not polylinefile_in_model
            and structype in only_coordinates_structures.keys()
        ):
            assert (
                coordinates_in_model
            ), f"Specify location by setting `num/x/yCoordinates` for a {only_coordinates_structures[structype]} structure."

        # Error: final check: at least one of x/y, branchId+chainage or polyline file must be given
        branch_and_chainage_in_model = Structure.validate_branch_and_chainage_in_model(
            filtered_values
        )
        assert (
            branch_and_chainage_in_model
            or coordinates_in_model
            or polylinefile_in_model
        ), "Specify location either by setting `branchId` and `chainage` or `num/x/yCoordinates` or `polylinefile` fields."

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
        """Try to initialize subclass based on the `type` field.
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
        # exclude the non-applicable, or unset props like coordinates or branches
        if self.type == "compound":
            exclude_set = self._loc_all_fields
        elif self.branchid is not None:
            exclude_set = self._loc_coord_fields
        else:
            exclude_set = self._loc_branch_fields
        exclude_set = super()._exclude_fields().union(exclude_set)
        return exclude_set

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("id") or data.get("name")


class FlowDirection(str, Enum):
    """
    Enum class containing the valid values for the allowedFlowDirection
    attribute in several subclasses of Structure.
    """

    none = "none"
    positive = "positive"
    negative = "negative"
    both = "both"
    allowedvaluestext = "Possible values: both, positive, negative, none."


class Orientation(str, Enum):
    """
    Enum class containing the valid values for the orientation
    attribute in several subclasses of Structure.
    """

    positive = "positive"
    negative = "negative"
    allowedvaluestext = "Possible values: positive, negative."


class Weir(Structure):
    """
    Hydraulic structure with `type=weir`, to be included in a structure file.
    Typically inside the structure list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.structurefile[0].structure[..]`

    All lowercased attributes match with the weir input as described in
    [UM Sec.C.12.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.12.1).
    """

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
        FlowDirection.both.value, alias="allowedFlowDir"
    )

    crestlevel: ForcingData = Field(alias="crestLevel")
    crestwidth: Optional[float] = Field(None, alias="crestWidth")
    corrcoeff: float = Field(1.0, alias="corrCoeff")
    usevelocityheight: bool = Field(True, alias="useVelocityHeight")

    _flowdirection_validator = get_enum_validator("allowedflowdir", enum=FlowDirection)


class UniversalWeir(Structure):
    """
    Hydraulic structure with `type=universalWeir`, to be included in a structure file.
    Typically inside the structure list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.structurefile[0].structure[..]`

    All lowercased attributes match with the universal weir input as described in
    [UM Sec.C.12.2](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.12.2).
    """

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
    """Enum class to store a [Culvert][hydrolib.core.dflowfm.structure.models.Culvert]'s subType."""

    culvert = "culvert"
    invertedSiphon = "invertedSiphon"


class Culvert(Structure):
    """
    Hydraulic structure with `type=culvert`, to be included in a structure file.
    Typically inside the structure list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.structurefile[0].structure[..]`

    All lowercased attributes match with the culvert input as described in
    [UM Sec.C.12.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.12.3).
    """

    type: Literal["culvert"] = Field("culvert", alias="type")
    allowedflowdir: FlowDirection = Field(alias="allowedFlowDir")

    leftlevel: float = Field(alias="leftLevel")
    rightlevel: float = Field(alias="rightLevel")
    csdefid: str = Field(alias="csDefId")
    length: float = Field(alias="length")
    inletlosscoeff: float = Field(alias="inletLossCoeff")
    outletlosscoeff: float = Field(alias="outletLossCoeff")
    valveonoff: bool = Field(alias="valveOnOff")
    valveopeningheight: Optional[ForcingData] = Field(alias="valveOpeningHeight")
    numlosscoeff: Optional[int] = Field(alias="numLossCoeff")
    relopening: Optional[List[float]] = Field(alias="relOpening")
    losscoeff: Optional[List[float]] = Field(alias="lossCoeff")
    bedfrictiontype: Optional[FrictionType] = Field(alias="bedFrictionType")
    bedfriction: Optional[float] = Field(alias="bedFriction")
    subtype: Optional[CulvertSubType] = Field(
        CulvertSubType.culvert.value, alias="subType"
    )
    bendlosscoeff: Optional[float] = Field(alias="bendLossCoeff")

    _split_to_list = get_split_string_on_delimiter_validator("relopening", "losscoeff")
    _flowdirection_validator = get_enum_validator("allowedflowdir", enum=FlowDirection)
    _subtype_validator = get_enum_validator("subtype", enum=CulvertSubType)
    _frictiontype_validator = get_enum_validator("bedfrictiontype", enum=FrictionType)

    @root_validator(allow_reuse=True)
    def validate_that_valve_related_fields_are_present_for_culverts_with_valves(
        cls, values: Dict
    ) -> Dict:
        """Validates that valve-related fields are present when there is a valve present."""
        return validate_required_fields(
            values,
            "valveopeningheight",
            "numlosscoeff",
            "relopening",
            "losscoeff",
            conditional_field_name="valveonoff",
            conditional_value=True,
        )

    @root_validator(allow_reuse=True)
    def validate_that_bendlosscoeff_field_is_present_for_invertedsyphons(
        cls, values: Dict
    ) -> Dict:
        """Validates that the bendlosscoeff value is present when dealing with inverted syphons."""
        return validate_required_fields(
            values,
            "bendlosscoeff",
            conditional_field_name="subtype",
            conditional_value=CulvertSubType.invertedSiphon,
        )

    @root_validator(allow_reuse=True)
    def check_list_lengths(cls, values):
        """Validates that the length of the relopening and losscoeff fields are as expected."""
        return validate_correct_length(
            values,
            "relopening",
            "losscoeff",
            length_name="numlosscoeff",
            list_required_with_length=True,
        )

    @root_validator(allow_reuse=True)
    def validate_that_bendlosscoeff_is_not_provided_for_culverts(
        cls, values: Dict
    ) -> Dict:
        """Validates that the bendlosscoeff field is not provided when the subtype is a culvert."""
        return validate_forbidden_fields(
            values,
            "bendlosscoeff",
            conditional_field_name="subtype",
            conditional_value=CulvertSubType.culvert,
        )


class Pump(Structure):
    """
    Hydraulic structure with `type=pump`, to be included in a structure file.
    Typically inside the structure list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.structurefile[0].structure[..]`

    All lowercased attributes match with the pump input as described in
    [UM Sec.C.12.6](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.12.6).
    """

    type: Literal["pump"] = Field("pump", alias="type")

    orientation: Optional[Orientation] = Field(alias="orientation")
    controlside: Optional[str] = Field(alias="controlSide")  # TODO Enum
    numstages: Optional[int] = Field(alias="numStages")
    capacity: ForcingData = Field(alias="capacity")

    startlevelsuctionside: Optional[List[float]] = Field(alias="startLevelSuctionSide")
    stoplevelsuctionside: Optional[List[float]] = Field(alias="stopLevelSuctionSide")
    startleveldeliveryside: Optional[List[float]] = Field(
        alias="startLevelDeliverySide"
    )
    stopleveldeliveryside: Optional[List[float]] = Field(alias="stopLevelDeliverySide")
    numreductionlevels: Optional[int] = Field(alias="numReductionLevels")
    head: Optional[List[float]] = Field(alias="head")
    reductionfactor: Optional[List[float]] = Field(alias="reductionFactor")

    _split_to_list = get_split_string_on_delimiter_validator(
        "startlevelsuctionside",
        "stoplevelsuctionside",
        "startleveldeliveryside",
        "stopleveldeliveryside",
        "head",
        "reductionfactor",
    )

    _orientation_validator = get_enum_validator("orientation", enum=Orientation)

    @root_validator(allow_reuse=True)
    def validate_that_controlside_is_provided_when_numstages_is_provided(
        cls, values: Dict
    ) -> Dict:
        return validate_required_fields(
            values,
            "controlside",
            conditional_field_name="numstages",
            conditional_value=0,
            comparison_func=gt,
        )

    @classmethod
    def _check_list_lengths_suctionside(cls, values: Dict) -> Dict:
        """Validates that the length of the startlevelsuctionside and stoplevelsuctionside fields are as expected."""
        return validate_correct_length(
            values,
            "startlevelsuctionside",
            "stoplevelsuctionside",
            length_name="numstages",
            list_required_with_length=True,
        )

    @root_validator(allow_reuse=True)
    def conditionally_check_list_lengths_suctionside(cls, values: Dict) -> Dict:
        """
        Validates the length of the suction side fields, but only if there is a controlside value
        present in the values and the controlside is not equal to the deliverySide.
        """
        return validate_conditionally(
            cls,
            values,
            Pump._check_list_lengths_suctionside,
            "controlside",
            "deliverySide",
            ne,
        )

    @classmethod
    def _check_list_lengths_deliveryside(cls, values: Dict) -> Dict:
        """Validates that the length of the startleveldeliveryside and stopleveldeliveryside fields are as expected."""
        return validate_correct_length(
            values,
            "startleveldeliveryside",
            "stopleveldeliveryside",
            length_name="numstages",
            list_required_with_length=True,
        )

    @root_validator(allow_reuse=True)
    def conditionally_check_list_lengths_deliveryside(cls, values: Dict) -> Dict:
        """
        Validates the length of the delivery side fields, but only if there is a controlside value
        present in the values and the controlside is not equal to the suctionSide.
        """
        return validate_conditionally(
            cls,
            values,
            Pump._check_list_lengths_deliveryside,
            "controlside",
            "suctionSide",
            ne,
        )

    @root_validator(allow_reuse=True)
    def check_list_lengths_head_and_reductionfactor(cls, values):
        """Validates that the lengths of the head and reductionfactor fields are as expected."""
        return validate_correct_length(
            values,
            "head",
            "reductionfactor",
            length_name="numreductionlevels",
            list_required_with_length=True,
        )


class Compound(Structure):
    """
    Hydraulic structure with `type=compound`, to be included in a structure file.
    Typically inside the structure list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.structurefile[0].structure[..]`

    All lowercased attributes match with the compound input as described in
    [UM Sec.C.12.11](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.12.11).
    """

    type: Literal["compound"] = Field("compound", alias="type")
    numstructures: int = Field(alias="numStructures")
    structureids: List[str] = Field(alias="structureIds", delimiter=";")

    _split_to_list = get_split_string_on_delimiter_validator(
        "structureids",
    )


class Orifice(Structure):
    """
    Hydraulic structure with `type=orifice`, to be included in a structure file.
    Typically inside the structure list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.structurefile[0].structure[..]`

    All lowercased attributes match with the orifice input as described in
    [UM Sec.C.12.7](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.12.7).
    """

    type: Literal["orifice"] = Field("orifice", alias="type")
    allowedflowdir: Optional[FlowDirection] = Field(
        FlowDirection.both.value, alias="allowedFlowDir"
    )

    crestlevel: ForcingData = Field(alias="crestLevel")
    crestwidth: Optional[float] = Field(None, alias="crestWidth")
    gateloweredgelevel: ForcingData = Field(alias="gateLowerEdgeLevel")
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


class GateOpeningHorizontalDirection(str, Enum):
    """Horizontal opening direction of gate door[s]."""

    symmetric = "symmetric"
    from_left = "fromLeft"
    from_right = "fromRight"
    allowedvaluestext = "Possible values: symmetric, fromLeft, fromRight."


class GeneralStructure(Structure):
    """
    Hydraulic structure with `type=generalStructure`, to be included in a structure file.
    Typically inside the structure list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.structurefile[0].structure[..]`

    All lowercased attributes match with the orifice input as described in
    [UM Sec.C.12.9](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.12.9).
    """

    class Comments(Structure.Comments):
        type: Optional[str] = Field(
            "Structure type; must read generalStructure", alias="type"
        )
        allowedflowdir: Optional[str] = Field(
            FlowDirection.allowedvaluestext, alias="allowedFlowDir"
        )

        upstream1width: Optional[str] = Field("w_u1 [m]", alias="upstream1Width")
        upstream1level: Optional[str] = Field("z_u1 [m AD]", alias="upstream1Level")
        upstream2width: Optional[str] = Field("w_u2 [m]", alias="upstream2Width")
        upstream2level: Optional[str] = Field("z_u2 [m D]", alias="upstream2Level")

        crestwidth: Optional[str] = Field("w_s [m]", alias="crestWidth")
        crestlevel: Optional[str] = Field("z_s [m AD]", alias="crestLevel")
        crestlength: Optional[str] = Field(
            "The crest length across the general structure [m]. When the crest length > 0, the extra resistance for this structure will be ls * g/(C2 * waterdepth)",
            alias="crestLength",
        )

        downstream1width: Optional[str] = Field("w_d1 [m]", alias="downstream1Width")
        downstream1level: Optional[str] = Field("z_d1 [m AD]", alias="downstream1Level")
        downstream2width: Optional[str] = Field("w_d2 [m]", alias="downstream2Width")
        downstream2level: Optional[str] = Field("z_d2 [m AD]", alias="downstream2Level")

        gateloweredgelevel: Optional[str] = Field(
            "Position of gate door’s lower edge [m AD]", alias="gateLowerEdgeLevel"
        )
        posfreegateflowcoeff: Optional[str] = Field(
            "Positive free gate flow corr.coeff. cgf [-]", alias="posFreeGateFlowCoeff"
        )
        posdrowngateflowcoeff: Optional[str] = Field(
            "Positive drowned gate flow corr.coeff. cgd [-]",
            alias="posDrownGateFlowCoeff",
        )
        posfreeweirflowcoeff: Optional[str] = Field(
            "Positive free weir flow corr.coeff. cwf [-]", alias="posFreeWeirFlowCoeff"
        )
        posdrownweirflowcoeff: Optional[str] = Field(
            "Positive drowned weir flow corr.coeff. cwd [-]",
            alias="posDrownWeirFlowCoeff",
        )
        poscontrcoeffreegate: Optional[str] = Field(
            "Positive gate flow contraction coefficient µgf [-]",
            alias="posContrCoefFreeGate",
        )
        negfreegateflowcoeff: Optional[str] = Field(
            "Negative free gate flow corr.coeff. cgf [-]", alias="negFreeGateFlowCoeff"
        )
        negdrowngateflowcoeff: Optional[str] = Field(
            "Negative drowned gate flow corr.coeff. cgd [-]",
            alias="negDrownGateFlowCoeff",
        )
        negfreeweirflowcoeff: Optional[str] = Field(
            "Negative free weir flow corr.coeff. cwf [-]", alias="negFreeWeirFlowCoeff"
        )
        negdrownweirflowcoeff: Optional[str] = Field(
            "Negative drowned weir flow corr.coeff. cwd [-]",
            alias="negDrownWeirFlowCoeff",
        )
        negcontrcoeffreegate: Optional[str] = Field(
            "Negative gate flow contraction coefficient mu gf [-]",
            alias="negContrCoefFreeGate",
        )
        extraresistance: Optional[str] = Field(
            "Extra resistance [-]", alias="extraResistance"
        )
        gateheight: Optional[str] = Field(None, alias="gateHeight")
        gateopeningwidth: Optional[str] = Field(
            "Opening width between gate doors [m], should be smaller than (or equal to) crestWidth",
            alias="gateOpeningWidth",
        )
        gateopeninghorizontaldirection: Optional[str] = Field(
            "Horizontal opening direction of gate door[s]. Possible values are: symmetric, fromLeft, fromRight",
            alias="gateOpeningHorizontalDirection",
        )
        usevelocityheight: Optional[str] = Field(
            "Flag indicates whether the velocity height is to be calculated or not",
            alias="useVelocityHeight",
        )

    comments: Optional[Comments] = Comments()

    type: Literal["generalStructure"] = Field("generalStructure", alias="type")
    allowedflowdir: Optional[FlowDirection] = Field(
        FlowDirection.both.value, alias="allowedFlowDir"
    )

    upstream1width: Optional[float] = Field(10.0, alias="upstream1Width")
    upstream1level: Optional[float] = Field(0.0, alias="upstream1Level")
    upstream2width: Optional[float] = Field(10.0, alias="upstream2Width")
    upstream2level: Optional[float] = Field(0.0, alias="upstream2Level")

    crestwidth: Optional[float] = Field(10.0, alias="crestWidth")
    crestlevel: Optional[ForcingData] = Field(0.0, alias="crestLevel")
    crestlength: Optional[float] = Field(0.0, alias="crestLength")

    downstream1width: Optional[float] = Field(10.0, alias="downstream1Width")
    downstream1level: Optional[float] = Field(0.0, alias="downstream1Level")
    downstream2width: Optional[float] = Field(10.0, alias="downstream2Width")
    downstream2level: Optional[float] = Field(0.0, alias="downstream2Level")

    gateloweredgelevel: Optional[ForcingData] = Field(11.0, alias="gateLowerEdgeLevel")
    posfreegateflowcoeff: Optional[float] = Field(1.0, alias="posFreeGateFlowCoeff")
    posdrowngateflowcoeff: Optional[float] = Field(1.0, alias="posDrownGateFlowCoeff")
    posfreeweirflowcoeff: Optional[float] = Field(1.0, alias="posFreeWeirFlowCoeff")
    posdrownweirflowcoeff: Optional[float] = Field(1.0, alias="posDrownWeirFlowCoeff")
    poscontrcoeffreegate: Optional[float] = Field(1.0, alias="posContrCoefFreeGate")
    negfreegateflowcoeff: Optional[float] = Field(1.0, alias="negFreeGateFlowCoeff")
    negdrowngateflowcoeff: Optional[float] = Field(1.0, alias="negDrownGateFlowCoeff")
    negfreeweirflowcoeff: Optional[float] = Field(1.0, alias="negFreeWeirFlowCoeff")
    negdrownweirflowcoeff: Optional[float] = Field(1.0, alias="negDrownWeirFlowCoeff")
    negcontrcoeffreegate: Optional[float] = Field(1.0, alias="negContrCoefFreeGate")
    extraresistance: Optional[float] = Field(0.0, alias="extraResistance")
    gateheight: Optional[float] = Field(1e10, alias="gateHeight")
    gateopeningwidth: Optional[ForcingData] = Field(0.0, alias="gateOpeningWidth")
    gateopeninghorizontaldirection: Optional[GateOpeningHorizontalDirection] = Field(
        GateOpeningHorizontalDirection.symmetric.value,
        alias="gateOpeningHorizontalDirection",
    )
    usevelocityheight: Optional[bool] = Field(True, alias="useVelocityHeight")


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
    """
    Hydraulic structure with `type=dambreak`, to be included in a structure file.
    Typically inside the structure list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.structurefile[0].structure[..]`

    All lowercased attributes match with the dambreak input as described in
    [UM Sec.C.12.10](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.12.10).
    """

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
    dambreaklevelsandwidths: Optional[Union[TimModel, ForcingModel]] = Field(
        alias="dambreakLevelsAndWidths"
    )

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
        cls, field_value: Optional[Union[TimModel, ForcingModel]], values: dict
    ) -> Optional[Union[TimModel, ForcingModel]]:
        """
        Validates whether a dambreak can be created with the given dambreakLevelsAndWidths
        property. This property should be given when the algorithm value is 3.

        Args:
            field_value (Optional[Union[TimModel, ForcingModel]]): Value given for dambreakLevelsAndWidths.
            values (dict): Dictionary of values already validated (assuming algorithm is in it).

        Raises:
            ValueError: When algorithm value is not 3 and field_value has a value.

        Returns:
            Optional[Union[TimModel, ForcingModel]]: The value given for dambreakLevelsAndwidths.
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
    def check_location_dambreak(cls, values: dict) -> dict:
        """
        Verifies whether the location for this structure contains valid values for
        numCoordinates, xCoordinates and yCoordinates or instead is using a polyline file.
        Verifies whether de water level location specifications are valid.

        Args:
            values (dict): Dictionary of validated values to create a Dambreak.

        Raises:
            ValueError: When the values dictionary does not contain valid coordinates or polyline file or when the water level location specifications are not valid.

        Returns:
            dict: Dictionary of validated values.
        """

        def _validate_waterlevel_location(x_key: str, y_key: str, node_key: str):
            x_is_given = values.get(x_key.lower()) is not None
            y_is_given = values.get(y_key.lower()) is not None
            node_is_given = values.get(node_key.lower()) is not None

            if (x_is_given and y_is_given and not node_is_given) or (
                node_is_given and not x_is_given and not y_is_given
            ):
                return

            raise ValueError(
                f"Either `{node_key}` should be specified or `{x_key}` and `{y_key}`."
            )

        _validate_waterlevel_location(
            "waterLevelUpstreamLocationX",
            "waterLevelUpstreamLocationY",
            "waterLevelUpstreamNodeId",
        )
        _validate_waterlevel_location(
            "waterLevelDownstreamLocationX",
            "waterLevelDownstreamLocationY",
            "waterLevelDownstreamNodeId",
        )

        return values


class Bridge(Structure):
    """
    Hydraulic structure with `type=bridge`, to be included in a structure file.
    Typically inside the structure list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.structurefile[0].structure[..]`

    All lowercased attributes match with the bridge input as described in
    [UM Sec.C.12.5](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.12.5).
    """

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
    frictiontype: FrictionType = Field(alias="frictionType")
    friction: float
    length: float

    _frictiontype_validator = get_enum_validator("frictiontype", enum=FrictionType)


class StructureGeneral(INIGeneral):
    """`[General]` section with structure file metadata."""

    _header: Literal["General"] = "General"
    fileversion: str = Field("3.00", alias="fileVersion")
    filetype: Literal["structure"] = Field("structure", alias="fileType")


class StructureModel(INIModel):
    """
    The overall structure model that contains the contents of one structure file.

    This model is typically referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.structurefile[..]`.

    Attributes:
        general (StructureGeneral): `[General]` block with file metadata.
        branch (List[Structure]): List of `[Structure]` blocks for all hydraulic structures.
    """

    general: StructureGeneral = StructureGeneral()
    structure: List[Structure] = []

    @classmethod
    def _ext(cls) -> str:
        return ".ini"

    @classmethod
    def _filename(cls) -> str:
        return "structures"

    _split_to_list = make_list_validator("structure")
