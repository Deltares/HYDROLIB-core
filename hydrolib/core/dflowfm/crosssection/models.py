"""Cross section models for D-Flow FM."""

import logging
from typing import Annotated, List, Literal, Optional, Union

from pydantic import (
    BeforeValidator,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from hydrolib.core.dflowfm.friction.models import FrictionType
from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.util import (
    LocationValidationConfiguration,
    LocationValidationFieldNames,
    UnknownKeywordErrorManager,
    enum_value_parser,
    make_list,
    split_string_on_delimiter,
    validate_correct_length,
    validate_location_specification,
)

logger = logging.getLogger(__name__)

frictionid_description = 'Name of the roughness variable associated with \
    this cross section. Either this parameter or \
    frictionType should be specified. If neither \
    parameter is specified, the frictionId defaults \
    to "Main".'

frictiontype_description = "Roughness type associated with this cross section \
    Either this parameter or frictionId should be specified."

frictionvalue_description = "Roughness value; its meaning depends on the roughness type selected \
    (only used if frictionType specified)."


class CrossDefGeneral(INIGeneral):
    """The crosssection definition file's `[General]` section with file meta data."""

    fileversion: str = Field("3.00", alias="fileVersion")
    filetype: Literal["crossDef"] = Field("crossDef", alias="fileType")


class CrossLocGeneral(INIGeneral):
    """The crosssection location file's `[General]` section with file meta data."""

    fileversion: str = Field("3.00", alias="fileVersion")
    filetype: Literal["crossLoc"] = Field("crossLoc", alias="fileType")


class CrossSectionDefinition(INIBasedModel):
    """CrossSectionDefinition.

    A `[Definition]` block for use inside a crosssection definition file,
    i.e., a [CrossDefModel][hydrolib.core.dflowfm.crosssection.models.CrossDefModel].

    This class is intended as an abstract class: various subclasses should
    define they actual types of crosssection definitions.
    """

    class Comments(INIBasedModel.Comments):
        """Comments for the CrossSectionDefinition class."""

        id: Optional[str] = "Unique cross-section definition id."
        thalweg: Optional[str] = Field(
            "Transverse Y coordinate at which the cross section aligns with the branch (Keyword used by GUI only)."
        )

    comments: Comments = Comments()

    _header: Literal["Definition"] = "Definition"

    id: str = Field(alias="id")
    type: str = Field(alias="type")
    thalweg: Optional[float] = None

    @classmethod
    def _get_unknown_keyword_error_manager(cls) -> Optional[UnknownKeywordErrorManager]:
        """The CrossSectionDefinition does not currently support raising an error on unknown keywords."""
        return None

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("id")

    @classmethod
    def _duplicate_keys_as_list(cls):
        return True

    @staticmethod
    def _check_friction_fields(frictionid, frictiontype, frictionvalue, label=""):
        """Check the friction specification.

        Make a model_validator that verifies whether the crosssection definition (subclass)
        has a valid friction specification.
        Supposed to be embedded in subclasses for their friction fields.

        Args:
            frictionid:
                name of the frictionid attribute in the subclass.
            frictiontype:
                name of the frictiontype attribute in the subclass.
            frictionvalue:
                name of the frictionvalue attribute in the subclass.

        Raises:
            ValueError:
                If both frictionid and frictiontype/frictionvalue are specified.
        """
        if frictionid and (frictiontype or frictionvalue):
            raise ValueError(
                f"{label} has duplicate friction specification: both frictionid and frictiontype/frictionvalue."
            )


class CircleCrsDef(CrossSectionDefinition):
    """CircleCrsDef.

    Crosssection definition with `type=circle`, to be included in a crossdef file.
    Typically inside the definition list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.crossdeffile.definition[..]`

    All lowercased attributes match with the circle input as described in
    [UM Sec.C.16.1.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.1.1).
    """

    class Comments(CrossSectionDefinition.Comments):
        """Comments for the CircleCrsDef class."""

        type: Optional[str] = Field("Cross section type; must read circle")

        diameter: Optional[str] = Field("Internal diameter of the circle [m].")
        frictionid: Optional[str] = Field(
            frictionid_description,
            alias="frictionId",
        )
        frictiontype: Optional[str] = Field(
            frictiontype_description,
            alias="frictionType",
        )
        frictionvalue: Optional[str] = Field(
            frictionvalue_description,
            alias="frictionValue",
        )

    comments: Comments = Comments()

    type: Literal["circle"] = Field("circle")
    diameter: float
    frictionid: Optional[str] = Field(None, alias="frictionId")
    frictiontype: Optional[FrictionType] = Field(None, alias="frictionType")
    frictionvalue: Optional[float] = Field(None, alias="frictionValue")

    @model_validator(mode="after")
    def check_friction(self):
        self._check_friction_fields(
            self.frictionid, self.frictiontype, self.frictionvalue, label=self.id
        )
        return self

    @field_validator("frictiontype", mode="before")
    @classmethod
    def validate_enum_frictiontype(cls, v):
        return enum_value_parser(v, FrictionType)


class RectangleCrsDef(CrossSectionDefinition):
    """RectangleCrsDef.

    Crosssection definition with `type=rectangle`, to be included in a crossdef file.
    Typically inside the definition list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.crossdeffile.definition[..]`

    All lowercased attributes match with the rectangle input as described in
    [UM Sec.C.16.1.2](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.1.2).
    """

    class Comments(CrossSectionDefinition.Comments):
        """Comments for the RectangleCrsDef class."""

        type: Optional[str] = Field("Cross section type; must read rectangle")
        width: Optional[str] = Field("Width of the rectangle [m].")
        height: Optional[str] = Field("Height of the rectangle [m].")
        closed: Optional[str] = Field("no: Open channel, yes: Closed channel.")
        frictionid: Optional[str] = Field(
            frictionid_description,
            alias="frictionId",
        )
        frictiontype: Optional[str] = Field(
            frictiontype_description,
            alias="frictionType",
        )
        frictionvalue: Optional[str] = Field(
            frictionvalue_description,
            alias="frictionValue",
        )

    comments: Comments = Comments()

    type: Literal["rectangle"] = Field("rectangle")
    width: float
    height: float
    closed: bool = Field(True)
    frictionid: Optional[str] = Field(None, alias="frictionId")
    frictiontype: Optional[FrictionType] = Field(None, alias="frictionType")
    frictionvalue: Optional[float] = Field(None, alias="frictionValue")

    @model_validator(mode="after")
    def check_friction(self):
        self._check_friction_fields(
            self.frictionid, self.frictiontype, self.frictionvalue, label=self.id
        )
        return self

    @field_validator("frictiontype", mode="before")
    @classmethod
    def validate_enum_frictiontype(cls, v):
        return enum_value_parser(v, FrictionType)


class ZWRiverCrsDef(CrossSectionDefinition):
    """ZWRiverCrsDef.

    Crosssection definition with `type=zwRiver`, to be included in a crossdef file.
    Typically inside the definition list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.crossdeffile.definition[..]`

    All lowercased attributes match with the zwRiver input as described in
    [UM Sec.C.16.1.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.1.3).
    """

    class Comments(CrossSectionDefinition.Comments):
        """Comments for the ZWRiverCrsDef class."""

        type: Optional[str] = Field(
            "Cross section type; must read zwRiver", alias="type"
        )
        numlevels: Optional[str] = Field(
            "Number of levels in the table.", alias="numLevels"
        )
        levels: Optional[str] = Field(
            "Space separated list of monotonic increasing heights/levels [m AD].",
            alias="levels",
        )
        flowwidths: Optional[str] = Field(
            "Space separated list of flow widths at the selected heights [m)].",
            alias="flowWidths",
        )
        totalwidths: Optional[str] = Field(
            "Space separated list of total widths at the selected heights [m]. "
            "Equal to flowWidths if not specified. If specified, the totalWidths"
            "should be larger than flowWidths.",
            alias="totalWidths",
        )
        leveecrestLevel: Optional[str] = Field(
            "Crest level of levee [m AD].", alias="leveeCrestlevel"
        )
        leveebaselevel: Optional[str] = Field(
            "Base level of levee [m AD].", alias="leveeBaseLevel"
        )
        leveeflowarea: Optional[str] = Field(
            "Flow area behind levee [m2].", alias="leveeFlowArea"
        )
        leveetotalarea: Optional[str] = Field(
            "Total area behind levee [m2].", alias="leveeTotalArea"
        )
        mainwidth: Optional[str] = Field(
            "Width of main section [m]. Default value: max(flowWidths).",
            alias="mainWidth",
        )
        fp1width: Optional[str] = Field(
            "Width of floodplain 1 section [m]. Default value: max(flowWidths)-mainWidth",
            alias="fp1Width",
        )
        fp2width: Optional[str] = Field(
            "Width of floodplain 2 section [m]. Default value: max(flowWidths)-mainWidth-fp1Width",
            alias="fp2Width",
        )
        frictionids: Optional[str] = Field(
            "Semicolon separated list of roughness variable names associated with the roughness "
            "sections. Either this parameter or frictionTypes should be specified. If neither "
            'parameter is specified, the frictionIds default to "Main", "FloodPlain1" '
            'and "FloodPlain2".',
            alias="frictionIds",
        )
        frictiontypes: Optional[str] = Field(
            "Semicolon separated list of roughness types associated with the roughness sections. "
            "Either this parameter or frictionIds should be specified. Can be specified as a "
            "single value if all roughness sections use the same type.",
            alias="frictionTypes",
        )
        frictionvalues: Optional[str] = Field(
            "Space separated list of roughness values; their meaning depends on the roughness "
            "types selected (only used if frictionTypes specified).",
            alias="frictionValues",
        )

    comments: Comments = Comments()

    type: Literal["zwRiver"] = Field("zwRiver")
    numlevels: int = Field(alias="numLevels")
    levels: List[float]
    flowwidths: List[float] = Field(alias="flowWidths")
    totalwidths: Optional[List[float]] = Field(None, alias="totalWidths")
    leveecrestLevel: Optional[float] = Field(None, alias="leveeCrestlevel")
    leveebaselevel: Optional[float] = Field(None, alias="leveeBaseLevel")
    leveeflowarea: Optional[float] = Field(None, alias="leveeFlowArea")
    leveetotalrea: Optional[float] = Field(None, alias="leveeTotalArea")
    mainwidth: Optional[float] = Field(None, alias="mainWidth")
    fp1width: Optional[float] = Field(None, alias="fp1Width")
    fp2width: Optional[float] = Field(None, alias="fp2Width")
    frictionids: Optional[List[str]] = Field(None, alias="frictionIds", delimiter=";")
    frictiontypes: Optional[List[FrictionType]] = Field(
        None, alias="frictionTypes", delimiter=";"
    )
    frictionvalues: Optional[List[float]] = Field(None, alias="frictionValues")

    @field_validator(
        "levels",
        "flowwidths",
        "totalwidths",
        "frictionvalues",
        "frictionids",
        "frictiontypes",
        mode="before",
    )
    @classmethod
    def split_string_list(cls, v, info: ValidationInfo):
        return split_string_on_delimiter(cls, v, info)

    @model_validator(mode="after")
    def check_friction(self):
        self._check_friction_fields(
            self.frictionids, self.frictiontypes, self.frictionvalues, label=self.id
        )
        return self

    @field_validator("frictiontypes", mode="before")
    @classmethod
    def validate_enum_frictiontype(cls, v):
        return enum_value_parser(v, FrictionType)

    @model_validator(mode="after")
    def check_list_lengths(self):
        """Validate that the length of the levels, flowwidths and totalwidths fields are as expected."""
        validate_correct_length(
            self.model_dump(),
            "levels",
            "flowwidths",
            "totalwidths",
            length_name="numlevels",
        )
        return self


class ZWCrsDef(CrossSectionDefinition):
    """ZWCrsDef.

    Crosssection definition with `type=zw`, to be included in a crossdef file.
    Typically inside the definition list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.crossdeffile.definition[..]`

    All lowercased attributes match with the zw input as described in
    [UM Sec.C.16.1.4](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.1.4).
    """

    class Comments(CrossSectionDefinition.Comments):
        """Comments for the ZWCrsDef class."""

        type: Optional[str] = Field("Cross section type; must read zw", alias="type")
        # NOTE: Field "template" deliberately ignored for now.
        numlevels: Optional[str] = Field(
            "Number of levels in the table.", alias="numLevels"
        )
        levels: Optional[str] = Field(
            "Space separated list of monotonic increasing heights/levels [m AD].",
            alias="levels",
        )
        flowwidths: Optional[str] = Field(
            "Space separated list of flow widths at the selected heights [m)].",
            alias="flowWidths",
        )
        totalwidths: Optional[str] = Field(
            "Space separated list of total widths at the selected heights [m]. "
            "Equal to flowWidths if not specified. If specified, the totalWidths"
            "should be larger than flowWidths.",
            alias="totalWidths",
        )
        frictionid: Optional[str] = Field(
            frictionid_description,
            alias="frictionId",
        )
        frictiontype: Optional[str] = Field(
            frictiontype_description,
            alias="frictionType",
        )
        frictionvalue: Optional[str] = Field(
            frictionvalue_description,
            alias="frictionValue",
        )

    comments: Comments = Comments()

    type: Literal["zw"] = Field("zw")
    numlevels: int = Field(alias="numLevels")
    levels: List[float]
    flowwidths: List[float] = Field(alias="flowWidths")
    totalwidths: Optional[List[float]] = Field(None, alias="totalWidths")
    frictionid: Optional[str] = Field(None, alias="frictionId")
    frictiontype: Optional[FrictionType] = Field(None, alias="frictionType")
    frictionvalue: Optional[float] = Field(None, alias="frictionValue")

    @field_validator(
        "levels",
        "flowwidths",
        "totalwidths",
        mode="before",
    )
    @classmethod
    def split_string_list(cls, v, info: ValidationInfo):
        return split_string_on_delimiter(cls, v, info)

    @model_validator(mode="after")
    def check_list_lengths(self):
        """Validate that the length of the levels, flowwidths and totalwidths fields are as expected."""
        validate_correct_length(
            self.model_dump(),
            "levels",
            "flowwidths",
            "totalwidths",
            length_name="numlevels",
        )
        return self

    @model_validator(mode="after")
    def check_friction(self):
        self._check_friction_fields(
            self.frictionid, self.frictiontype, self.frictionvalue, label=self.id
        )
        return self

    @field_validator("frictiontype", mode="before")
    @classmethod
    def validate_enum_frictiontype(cls, v):
        return enum_value_parser(v, FrictionType)


class YZCrsDef(CrossSectionDefinition):
    """YZCrsDef.

    Crosssection definition with `type=yz`, to be included in a crossdef file.
    Typically inside the definition list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.crossdeffile.definition[..]`

    All lowercased attributes match with the yz input as described in
    [UM Sec.C.16.1.6](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.1.6).
    """

    class Comments(CrossSectionDefinition.Comments):
        """Comments for the YZCrsDef class."""

        type: Optional[str] = Field("Cross section type; must read yz", alias="type")
        conveyance: Optional[str] = Field(
            "lumped: Lumped, segmented: Vertically segmented. Only the default lumped "
            + "option is allowed if singleValuedZ = no. In the case of lumped conveyance, "
            + "only a single uniform roughness for the whole cross section is allowed, "
            + "i.e., sectionCount must equal 1.",
        )
        yzcount: Optional[str] = Field("Number of YZ-coordinates.", alias="yzCount")
        yCoordinates: Optional[str] = Field(
            "Space separated list of monotonic increasing y-coordinates [m].",
            alias="yCoordinates",
        )
        zCoordinates: Optional[str] = Field(
            "Space separated list of single-valued z-coordinates [m AD].",
            alias="zCoordinates",
        )
        sectioncount: Optional[str] = Field(
            "Number of roughness sections. If the lumped conveyance is selected then "
            + "sectionCount must equal 1.",
            alias="sectionCount",
        )
        frictionpositions: Optional[str] = Field(
            "Locations where the roughness sections start and end. Always one location more than "
            + "sectionCount. The first value should equal 0 and the last value should equal the "
            + "cross section length. Keyword may be skipped if sectionCount = 1.",
            alias="frictionPositions",
        )
        frictionids: Optional[str] = Field(
            "Semicolon separated list of roughness variable names associated with the roughness "
            + "sections. Either this parameter or frictionTypes should be specified. If neither "
            + 'parameter is specified, the frictionIds default to "Main", "FloodPlain1" '
            + 'and "FloodPlain2".',
            alias="frictionIds",
        )
        frictiontypes: Optional[str] = Field(
            "Semicolon separated list of roughness types associated with the roughness sections. "
            + "Either this parameter or frictionIds should be specified. Can be specified as a "
            + "single value if all roughness sections use the same type.",
            alias="frictionTypes",
        )
        frictionvalues: Optional[str] = Field(
            "Space separated list of roughness values; their meaning depends on the roughness "
            + "types selected (only used if frictionTypes specified).",
            alias="frictionValues",
        )

    comments: Comments = Comments()

    type: Literal["yz"] = Field("yz")
    singlevaluedz: Optional[bool] = Field(None, alias="singleValuedZ")
    yzcount: int = Field(alias="yzCount")
    ycoordinates: List[float] = Field(alias="yCoordinates")
    zcoordinates: List[float] = Field(alias="zCoordinates")
    conveyance: Optional[str] = Field("segmented")
    sectioncount: Optional[int] = Field(1, alias="sectionCount")
    frictionpositions: Optional[List[float]] = Field(None, alias="frictionPositions")
    frictionids: Optional[List[str]] = Field(None, alias="frictionIds", delimiter=";")
    frictiontypes: Optional[List[FrictionType]] = Field(
        None, alias="frictionTypes", delimiter=";"
    )
    frictionvalues: Optional[List[float]] = Field(None, alias="frictionValues")

    @field_validator(
        "ycoordinates",
        "zcoordinates",
        "frictionpositions",
        "frictionvalues",
        "frictionids",
        "frictiontypes",
        mode="before",
    )
    @classmethod
    def split_string_list(cls, v, info: ValidationInfo):
        return split_string_on_delimiter(cls, v, info)

    @model_validator(mode="after")
    def check_friction(self):
        self._check_friction_fields(
            self.frictionids, self.frictiontypes, self.frictionvalues, label=self.id
        )
        return self

    @field_validator("frictiontypes", mode="before")
    @classmethod
    def validate_enum_frictiontype(cls, v):
        return enum_value_parser(v, FrictionType)

    @model_validator(mode="after")
    def check_list_lengths_coordinates(self):
        """Validate that the length of the ycoordinates and zcoordinates fields are as expected."""
        validate_correct_length(
            self.model_dump(),
            "ycoordinates",
            "zcoordinates",
            length_name="yzcount",
        )
        return self

    @model_validator(mode="after")
    def check_list_lengths_friction(self):
        """Validate that the length of the frictionids, frictiontypes and frictionvalues field are as expected."""
        validate_correct_length(
            self.model_dump(),
            "frictionids",
            "frictiontypes",
            "frictionvalues",
            length_name="sectioncount",
        )
        return self

    @model_validator(mode="after")
    def check_list_length_frictionpositions(self):
        """Validate that the length of the frictionpositions field is as expected."""
        validate_correct_length(
            self.model_dump(),
            "frictionpositions",
            length_name="sectioncount",
            length_incr=1,  # 1 extra for frictionpositions
        )
        return self


class XYZCrsDef(YZCrsDef, CrossSectionDefinition):
    """XYZCrsDef.

    Crosssection definition with `type=xyz`, to be included in a crossdef file.
    Typically inside the definition list of a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.crossdeffile.definition[..]`

    All lowercased attributes match with the xyz input as described in
    [UM Sec.C.16.1.5](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.1.5).

    This class extends the YZCrsDef class with x-coordinates and an optional
    branchId field. Most other attributes are inherited, but the coordcount
    is overridden under the Pydantic alias "xyzCount".

    Attributes:
        yzcount (Optional[int]): dummy attribute that should not be set nor used.
            Only present to mask the inherited attribute from parent class YZCrsDef.
        xyzcount (int): Number of XYZ-coordinates. Always use this instead of yzcount.
    """

    class Comments(YZCrsDef.Comments):
        """Comments for the XYZCrsDef class."""

        type: Optional[str] = Field("Cross section type; must read xyz", alias="type")
        branchid: Optional[str] = Field(
            "Branch on which the cross section is located.", alias="branchId"
        )
        xyzcount: Optional[str] = Field("Number of XYZ-coordinates.", alias="xyzCount")
        xCoordinates: Optional[str] = Field(
            "Space separated list of x-coordinates [m or degrees East].",
            alias="xCoordinates",
        )
        yCoordinates: Optional[str] = Field(
            "Space separated list of y-coordinates [m or degrees North].",
            alias="yCoordinates",
        )
        zCoordinates: Optional[str] = Field(
            "Space separated list of z-coordinates [m AD].",
            alias="zCoordinates",
        )

    comments: Comments = Comments()

    type: Literal["xyz"] = Field("xyz")
    branchid: Optional[str] = Field(None, alias="branchId")
    yzcount: Optional[int] = Field(
        None, alias="yzCount"
    )  # Trick to not inherit parent's yzcount required field.
    xyzcount: int = Field(alias="xyzCount")
    xcoordinates: List[float] = Field(alias="xCoordinates")

    @field_validator("xcoordinates", mode="before")
    def split_string_xcoordinates(cls, v, info: ValidationInfo):
        return split_string_on_delimiter(cls, v, info)

    @field_validator("xyzcount")
    @classmethod
    def validate_xyzcount_without_yzcount(
        cls, field_value: int, values: ValidationInfo
    ) -> int:
        """Validate the xyzcount field.

        Validates whether this XYZCrsDef does have attribute xyzcount,
        but not the parent class's yzcount.

        Args:
            field_value (Optional[Path]):
                Value given for xyzcount.
            value (int):
                The validated value of xyzcount.

        Raises:
            ValueError:
                When yzcount is present.

        Returns:
            int:
                The value given for xyzcount.
        """
        # Retrieve the algorithm value (if not found use 0).
        yzcount_value = values.data.get("yzcount")
        if field_value is not None and yzcount_value is not None:
            # yzcount should not be set, when xyzcount is set.
            raise ValueError(
                f"xyz cross section definition should not contain field yzCount (rather: xyzCount), current value: {yzcount_value}."
            )
        return field_value

    @model_validator(mode="after")
    def check_list_lengths_coordinates(self):
        """Validate that the length of the xcoordinates, ycoordinates and zcoordinates field are as expected."""
        validate_correct_length(
            self.model_dump(),
            "xcoordinates",
            "ycoordinates",
            "zcoordinates",
            length_name="xyzcount",
        )
        return self


class CrossSection(INIBasedModel):
    """Crosssection.

    A `[CrossSection]` block for use inside a crosssection location file,
    i.e., a [CrossLocModel][hydrolib.core.dflowfm.crosssection.models.CrossLocModel].

    Attributes:
        id (str): Unique cross-section location id.
        branchid (str, optional): Branch on which the cross section is located.
        chainage (str, optional): Chainage on the branch (m).
        x (str, optional): x-coordinate of the location of the cross section.
        y (str, optional): y-coordinate of the location of the cross section.
        shift (float, optional): Vertical shift of the cross section definition [m]. Defined positive upwards.
        definitionid (str): Id of cross section definition.
    """

    class Comments(INIBasedModel.Comments):
        """Comments for the CrossSection class."""

        id: Optional[str] = "Unique cross-section location id."
        branchid: Optional[str] = Field(
            "Branch on which the cross section is located.", alias="branchId"
        )
        chainage: Optional[str] = "Chainage on the branch (m)."

        x: Optional[str] = Field(
            "x-coordinate of the location of the cross section.",
        )
        y: Optional[str] = Field(
            "y-coordinate of the location of the cross section.",
        )
        shift: Optional[str] = Field(
            "Vertical shift of the cross section definition [m]. Defined positive upwards.",
        )
        definitionid: Optional[str] = Field(
            "Id of cross section definition.", alias="definitionId"
        )

    comments: Comments = Comments()
    _header: Literal["CrossSection"] = "CrossSection"
    id: str = Field(alias="id")

    branchid: Optional[str] = Field(None, alias="branchId")
    chainage: Optional[float] = Field(None)

    x: Optional[float] = Field(None)
    y: Optional[float] = Field(None)

    shift: Optional[float] = Field(0.0)
    definitionid: str = Field(alias="definitionId")

    @model_validator(mode="after")
    def validate_that_location_specification_is_correct(self):
        """Validate that the correct location specification is given."""
        validate_location_specification(
            self.model_dump(),
            config=LocationValidationConfiguration(
                validate_node=False,
                validate_num_coordinates=False,
                validate_location_type=False,
            ),
            fields=LocationValidationFieldNames(x_coordinates="x", y_coordinates="y"),
        )
        return self


class CrossLocModel(INIModel):
    """The overall crosssection location model that contains the contents of one crossloc file.

    This model is typically referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.crosslocfile`.

    Attributes:
        general (CrossLocGeneral):
            `[General]` block with file metadata.
        crosssection (List[CrossSection]):
            List of `[CrossSection]` blocks for all cross-section locations, The crosssection attribute also accepts
            single cross section.

    Examples:
        - Create the read `CrossLocModel` class from file.
        ```python
        >>> from hydrolib.core.dflowfm.crosssection.models import CrossLocModel
        >>> from pathlib import Path
        >>> path = Path("examples/data/crsloc.ini")
        >>> crossloc_model = CrossLocModel(path)
        >>> print(len(crossloc_model.crosssection))
        2
        >>> print(crossloc_model.crosssection[0])
        comments=Comments(id=None, branchid=None, chainage=None, x='x-coordinate of the location of the cross section.', y='y-coordinate of the location of the cross section.', shift=None, definitionid=None) id='Channel1_50.000' branchid='Channel1' chainage=50.0 x=None y=None shift=1.0 definitionid='Prof1'

        ```

        - Create the `CrossLocModel` class by providing values for the `crosssection` attribute.
        ```python
        >>> data = {
        ...    "id": 99,
        ...    "branchId": 9,
        ...    "chainage": 403,
        ...    "shift": 0.0,
        ...    "definitionId": 99
        ... }
        >>> cross_section = CrossSection(**data)
        >>> crossloc = CrossLocModel(crosssection=cross_section)
        >>> type(crossloc.crosssection)
        <class 'list'>
        >>> len(crossloc.crosssection)
        1

        ```

        - Create the `CrossLocModel` class by providing values as a dictionary.
        ```python
        >>> data = {
        ...     "crosssection": {
        ...         "id": 99,
        ...         "branchId": 9,
        ...         "chainage": 403.089709,
        ...         "shift": 0.0,
        ...         "definitionId": 99,
        ...     }
        ... }
        >>> crossloc = CrossLocModel(**data)
        >>> print(crossloc.crosssection)
        [CrossSection(comments=Comments(id='Unique cross-section location id.', branchid='Branch on which the cross section is located.', chainage='Chainage on the branch (m).', x='x-coordinate of the location of the cross section.', y='y-coordinate of the location of the cross section.', shift='Vertical shift of the cross section definition [m]. Defined positive upwards.', definitionid='Id of cross section definition.'), id='99', branchid='9', chainage=403.089709, x=None, y=None, shift=0.0, definitionid='99')]

        ```
    """

    general: CrossLocGeneral = CrossLocGeneral()
    crosssection: List[CrossSection] = Field(default_factory=list)

    @classmethod
    def _filename(cls) -> str:
        return "crsloc"

    @field_validator("crosssection", mode="before")
    def ensure_crosssection_is_list(cls, v):
        """Converting the crosssection to a list if it is not already a list."""
        if isinstance(v, list):
            return v
        elif v is None:
            return []
        return [v]


CrossSectionDefinitionUnion = Annotated[
    Union[
        CircleCrsDef,
        RectangleCrsDef,
        ZWRiverCrsDef,
        ZWCrsDef,
        YZCrsDef,
        XYZCrsDef,
    ],
    Field(discriminator="type"),
]


class CrossDefModel(INIModel):
    """
    The overall crosssection definition model that contains the contents of one crossdef file.

    This model is typically referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.crossdeffile`.

    Attributes:
        general (CrossdefGeneral): `[General]` block with file metadata.
        definition (List[CrossSectionDefinition]): List of `[Definition]` blocks for all cross sections.
    """

    general: CrossDefGeneral = CrossDefGeneral()
    definition: Annotated[
        List[CrossSectionDefinitionUnion], BeforeValidator(make_list)
    ] = []

    @classmethod
    def _filename(cls) -> str:
        return "crsdef"
