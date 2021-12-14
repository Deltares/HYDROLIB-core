import logging
from typing import List, Literal, Optional

from pydantic import Field, root_validator
from pydantic.class_validators import validator

from hydrolib.core.io.friction.models import FrictionType
from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.util import (
    get_enum_validator,
    get_from_subclass_defaults,
    get_split_string_on_delimiter_validator,
    make_list_length_root_validator,
    make_list_validator,
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
    """
    A `[Definition]` block for use inside a crosssection definition file,
    i.e., a [CrossDefModel][hydrolib.core.io.crosssection.models.CrossDefModel].

    This class is intended as an abstract class: various subclasses should
    define they actual types of crosssection definitions.
    """

    # TODO: would we want to load this from something externally and generate these automatically
    class Comments(INIBasedModel.Comments):
        id: Optional[str] = "Unique cross-section definition id."
        thalweg: Optional[str] = Field(
            "Transverse Y coordinate at which the cross section aligns with the branch "
            + "(Keyword used by GUI only)."
        )

    comments: Comments = Comments()

    _header: Literal["Definition"] = "Definition"

    id: str = Field(alias="id")
    type: str = Field(alias="type")
    thalweg: Optional[float]

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("id")

    @classmethod
    def _duplicate_keys_as_list(cls):
        return True

    @validator("type", pre=True)
    def _validate_type(cls, value):
        return get_from_subclass_defaults(CrossSectionDefinition, "type", value)

    @classmethod
    def validate(cls, v):
        """Try to iniatialize subclass based on the `type` field.
        This field is compared to each `type` field of the derived models of `CrossSectionDefinition`.
        The derived model with an equal crosssection definition type will be initialized.

        Raises:
            ValueError: When the given type is not a known crosssection definition type.
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

    @staticmethod
    def _get_friction_root_validator(
        frictionid_attr: str,
        frictiontype_attr: str,
        frictionvalue_attr: str,
    ):
        """
        Make a root_validator that verifies whether the crosssection definition (subclass)
        has a valid friction specification.
        Supposed to be embedded in subclasses for their friction fields.

        Args:
            frictionid_attr: name of the frictionid attribute in the subclass.
            frictiontype_attr: name of the frictiontype attribute in the subclass.
            frictionvalue_attr: name of the frictionvalue attribute in the subclass.

        Returns:
            root_validator: to be embedded in the subclass that needs it.
        """

        def validate_friction_specification(cls, values):
            """
            The actual validator function.

            Args:
            cls: The subclass for which the root_validator is called.
            values (dict): Dictionary of values to create a CrossSectionDefinition subclass.
            """
            frictionid = values.get(frictionid_attr) or ""
            frictiontype = values.get(frictiontype_attr) or ""
            frictionvalue = values.get(frictionvalue_attr) or ""

            if frictionid == "":
                if frictiontype == "" or frictionvalue == "":
                    raise ValueError(
                        f"Cross section is missing any friction specification."
                    )
            else:
                if frictiontype != "" or frictionvalue != "":
                    raise ValueError(
                        f"Cross section has duplicate friction specification (both {frictionid_attr} and {frictiontype_attr}/{frictionvalue_attr})."
                    )

            return values

        return root_validator(allow_reuse=True)(validate_friction_specification)


class CrossDefModel(INIModel):
    """
    The overall crosssection definition model that contains the contents of one crossdef file.

    This model is typically referenced under a [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry.crossdeffile`.

    Attributes:
        general (CrossdefGeneral): `[General]` block with file metadata.
        definition (List[CrossSectionDefinition]): List of `[Definition]` blocks for all cross sections.
    """

    general: CrossDefGeneral = CrossDefGeneral()
    definition: List[CrossSectionDefinition] = []

    _make_list = make_list_validator("definition")

    @classmethod
    def _filename(cls) -> str:
        return "crsdef"


class CircleCrsDef(CrossSectionDefinition):
    """
    Crosssection definition with `type=circle`, to be included in a crossdef file.
    Typically inside the definition list of a [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry.crossdeffile.definition[..]`

    All lowercased attributes match with the circle input as described in
    [UM Sec.C.16.1.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.1.1).
    """

    class Comments(CrossSectionDefinition.Comments):
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
    frictionid: Optional[str] = Field(alias="frictionId")
    frictiontype: Optional[FrictionType] = Field(alias="frictionType")
    frictionvalue: Optional[float] = Field(alias="frictionValue")

    _friction_validator = CrossSectionDefinition._get_friction_root_validator(
        "frictionid", "frictiontype", "frictionvalue"
    )
    _frictiontype_validator = get_enum_validator("frictiontype", enum=FrictionType)


class RectangleCrsDef(CrossSectionDefinition):
    """
    Crosssection definition with `type=rectangle`, to be included in a crossdef file.
    Typically inside the definition list of a [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry.crossdeffile.definition[..]`

    All lowercased attributes match with the rectangle input as described in
    [UM Sec.C.16.1.2](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.1.2).
    """

    class Comments(CrossSectionDefinition.Comments):
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
    frictionid: Optional[str] = Field(alias="frictionId")
    frictiontype: Optional[FrictionType] = Field(alias="frictionType")
    frictionvalue: Optional[float] = Field(alias="frictionValue")

    _friction_validator = CrossSectionDefinition._get_friction_root_validator(
        "frictionid", "frictiontype", "frictionvalue"
    )
    _frictiontype_validator = get_enum_validator("frictiontype", enum=FrictionType)


class ZWRiverCrsDef(CrossSectionDefinition):
    """
    Crosssection definition with `type=zwRiver`, to be included in a crossdef file.
    Typically inside the definition list of a [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry.crossdeffile.definition[..]`

    All lowercased attributes match with the zwRiver input as described in
    [UM Sec.C.16.1.3](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.1.3).
    """

    class Comments(CrossSectionDefinition.Comments):
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
            + "Equal to flowWidths if not specified. If specified, the totalWidths"
            + "should be larger than flowWidths.",
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

    type: Literal["zwRiver"] = Field("zwRiver")
    numlevels: int = Field(alias="numLevels")
    levels: List[float]
    flowwidths: List[float] = Field(alias="flowWidths")
    totalwidths: Optional[List[float]] = Field(alias="totalWidths")
    leveecrestLevel: Optional[float] = Field(alias="leveeCrestlevel")
    leveebaselevel: Optional[float] = Field(alias="leveeBaseLevel")
    leveeflowarea: Optional[float] = Field(alias="leveeFlowArea")
    leveetotalrea: Optional[float] = Field(alias="leveeTotalArea")
    mainwidth: Optional[float] = Field(alias="mainWidth")
    fp1width: Optional[float] = Field(alias="fp1Width")
    fp2width: Optional[float] = Field(alias="fp2Width")
    frictionids: Optional[List[str]] = Field(alias="frictionIds")
    frictiontypes: Optional[List[FrictionType]] = Field(alias="frictionTypes")
    frictionvalues: Optional[List[float]] = Field(alias="frictionValues")

    _split_to_list = get_split_string_on_delimiter_validator(
        "levels",
        "flowwidths",
        "totalwidths",
        "frictionvalues",
        delimiter=" ",
    )
    _split_to_list2 = get_split_string_on_delimiter_validator(
        "frictionids",
        "frictiontypes",
        delimiter=";",
    )

    _friction_validator = CrossSectionDefinition._get_friction_root_validator(
        "frictionids", "frictiontypes", "frictionvalues"
    )
    _frictiontype_validator = get_enum_validator("frictiontypes", enum=FrictionType)

    _check_list_length = make_list_length_root_validator(
        "levels",
        "flowwidths",
        "totalwidths",
        length_name="numlevels",
    )


class ZWCrsDef(CrossSectionDefinition):
    """
    Crosssection definition with `type=zw`, to be included in a crossdef file.
    Typically inside the definition list of a [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry.crossdeffile.definition[..]`

    All lowercased attributes match with the zw input as described in
    [UM Sec.C.16.1.4](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.1.4).
    """

    class Comments(CrossSectionDefinition.Comments):
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
            + "Equal to flowWidths if not specified. If specified, the totalWidths"
            + "should be larger than flowWidths.",
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
    totalwidths: Optional[List[float]] = Field(alias="totalWidths")
    frictionid: Optional[str] = Field(alias="frictionId")
    frictiontype: Optional[FrictionType] = Field(alias="frictionType")
    frictionvalue: Optional[float] = Field(alias="frictionValue")

    _split_to_list = get_split_string_on_delimiter_validator(
        "levels",
        "flowwidths",
        "totalwidths",
        delimiter=" ",
    )

    _check_list_length = make_list_length_root_validator(
        "levels",
        "flowwidths",
        "totalwidths",
        length_name="numlevels",
    )

    _friction_validator = CrossSectionDefinition._get_friction_root_validator(
        "frictionid", "frictiontype", "frictionvalue"
    )
    _frictiontype_validator = get_enum_validator("frictiontype", enum=FrictionType)


class YZCrsDef(CrossSectionDefinition):
    """
    Crosssection definition with `type=yz`, to be included in a crossdef file.
    Typically inside the definition list of a [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry.crossdeffile.definition[..]`

    All lowercased attributes match with the yz input as described in
    [UM Sec.C.16.1.6](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.1.6).
    """

    class Comments(CrossSectionDefinition.Comments):
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
    singlevaluedz: Optional[bool] = Field(alias="singleValuedZ")
    yzcount: int = Field(alias="yzCount")
    ycoordinates: List[float] = Field(alias="yCoordinates")
    zcoordinates: List[float] = Field(alias="zCoordinates")
    conveyance: Optional[str] = Field("segmented")
    sectioncount: Optional[int] = Field(1, alias="sectionCount")
    frictionpositions: Optional[List[float]] = Field(alias="frictionPositions")
    frictionids: Optional[List[str]] = Field(alias="frictionIds")
    frictiontypes: Optional[List[FrictionType]] = Field(alias="frictionTypes")
    frictionvalues: Optional[List[float]] = Field(alias="frictionValues")

    _split_to_list = get_split_string_on_delimiter_validator(
        "ycoordinates",
        "zcoordinates",
        "frictionpositions",
        "frictionvalues",
        delimiter=" ",
    )
    _split_to_list2 = get_split_string_on_delimiter_validator(
        "frictionids",
        "frictiontypes",
        delimiter=";",
    )

    _check_yzlist_length = make_list_length_root_validator(
        "ycoordinates",
        "zcoordinates",
        length_name="yzcount",
    )

    _check_frictlist_length = make_list_length_root_validator(
        "frictionids",
        "frictiontypes",
        "frictionvalues",
        length_name="sectioncount",
    )
    _check_frictlist_length1 = make_list_length_root_validator(
        "frictionpositions",
        length_name="sectioncount",
        length_incr=1,  # 1 extra for frictionpositions
    )

    _friction_validator = CrossSectionDefinition._get_friction_root_validator(
        "frictionids", "frictiontypes", "frictionvalues"
    )
    _frictiontype_validator = get_enum_validator("frictiontypes", enum=FrictionType)


class XYZCrsDef(YZCrsDef, CrossSectionDefinition):
    """
    Crosssection definition with `type=xyz`, to be included in a crossdef file.
    Typically inside the definition list of a [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry.crossdeffile.definition[..]`

    All lowercased attributes match with the xyz input as described in
    [UM Sec.C.16.1.5](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.16.1.5).

    This class extends the YZCrsDef class with x-coordinates and an optional
    branchId field. Most other attributes are inherited, but the coordcount
    is overridden under the Pydantic alias "xyzCount".

    Attributes:
        yzcount (Optional[int]): dummy attribute that should not be set nor used.
            Only present to mask the inherited attribute from parent class YZCrsDef.
        xyzcount (int): Number of XYZ-coordinates. Always use this instead of yzcount.
    """

    class Comments(YZCrsDef.Comments):
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
    branchid: Optional[str] = Field(alias="branchId")
    yzcount: Optional[int] = Field(
        alias="yzCount"
    )  # Trick to not inherit parent's yzcount required field.
    xyzcount: int = Field(alias="xyzCount")
    xcoordinates: List[float] = Field(alias="yCoordinates")

    _split_to_list0 = get_split_string_on_delimiter_validator(
        "xcoordinates",
        delimiter=" ",
    )

    @validator("xyzcount")
    @classmethod
    def validate_xyzcount_without_yzcount(cls, field_value: int, values: dict) -> int:
        """
        Validates whether this XYZCrsDef does have attribute xyzcount,
        but not the parent class's yzcount.

        Args:
            field_value (Optional[Path]): Value given for xyzcount.
            values (dict): Dictionary of values already validated.

        Raises:
            ValueError: When yzcount is present.

        Returns:
            int: The value given for xyzcount.
        """
        # Retrieve the algorithm value (if not found use 0).
        yzcount_value = values.get("yzcount")
        if field_value is not None and yzcount_value is not None:
            # yzcount should not be set, when xyzcount is set.
            raise ValueError(
                f"xyz cross section definition should not contain field yzCount (rather: xyzCount), current value: {yzcount_value}."
            )
        return field_value

    _check_yzlist_length = make_list_length_root_validator(
        "ycoordinates",
        "zcoordinates",
        length_name="xyzcount",
    )

    _check_xlist_length = make_list_length_root_validator(
        "xcoordinates",
        length_name="xyzcount",
    )


class CrossSection(INIBasedModel):
    """
    A `[CrossSection]` block for use inside a crosssection location file,
    i.e., a [CrossLocModel][hydrolib.core.io.crosssection.models.CrossLocModel].

    Attributes:
        id (str): Unique cross-section location id.
        branchid (str): (optional) Branch on which the cross section is located.
    """

    # TODO: complete support for all crosssection fields: #172.

    _header: Literal["CrossSection"] = "CrossSection"
    id: str = Field(alias="id")
    branchid: str = Field(alias="branchId")


class CrossLocModel(INIModel):
    """
    The overall crosssection location model that contains the contents of one crossloc file.

    This model is typically referenced under a [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry.crosslocfile`.

    Attributes:
        general (CrossLocGeneral): `[General]` block with file metadata.
        crosssection (List[CrossSection]): List of `[CrossSection]` blocks for all cross section locations.
    """

    general: CrossLocGeneral = CrossLocGeneral()
    crosssection: List[CrossSection] = []

    @classmethod
    def _filename(cls) -> str:
        return "crsloc"
