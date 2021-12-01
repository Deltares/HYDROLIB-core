import logging
from abc import ABC
from functools import reduce
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
)

from pydantic import Extra, Field, root_validator
from pydantic.class_validators import validator

from hydrolib.core import __version__ as version
from hydrolib.core.basemodel import BaseModel, FileModel
from hydrolib.core.io.base import DummySerializer
from hydrolib.core.io.ini.util import (
    get_from_subclass_defaults,
    get_split_string_on_delimiter_validator,
)

from .io_models import (
    CommentBlock,
    ContentElement,
    Datablock,
    DatablockRow,
    Document,
    Property,
    Section,
)
from .parser import Parser
from .serializer import Serializer, SerializerConfig, write_ini
from .util import make_list_validator

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


class INIBasedModel(BaseModel, ABC):
    """INIBasedModel defines the base model for ini models

    INIBasedModel instances can be created from Section instances
    obtained through parsing ini documents. It further supports
    adding arbitrary fields to it, which will be written to file.
    Lastly, no arbitrary types are allowed for the defined fields.

    Attributes:
        comments (Optional[Comments]):
            Optional Comments if defined by the user.
    """

    _header: str

    class Config:
        extra = Extra.allow
        arbitrary_types_allowed = False

    @classmethod
    def _supports_comments(cls):
        return True

    @classmethod
    def _duplicate_keys_as_list(cls):
        return False

    @classmethod
    def list_delimiter(cls) -> str:
        return ";"

    class Comments(BaseModel, ABC):
        """Comments defines the comments of an INIBasedModel"""

        class Config:
            extra = Extra.allow
            arbitrary_types_allowed = False

    comments: Optional[Comments] = Comments()

    @root_validator(pre=True)
    def _skip_nones_and_set_header(cls, values):
        """Drop None fields for known fields."""
        dropkeys = []
        for k, v in values.items():
            if v is None and k in cls.__fields__.keys():
                dropkeys.append(k)

        logger.info(f"Dropped unset keys: {dropkeys}")
        for k in dropkeys:
            values.pop(k)

        if "_header" in values:
            values["_header"] = cls._header

        return values

    @validator("comments", always=True, allow_reuse=True)
    def comments_matches_has_comments(cls, v):
        if not cls._supports_comments() and v is not None:
            logging.warning(f"Dropped unsupported comments from {cls.__name__} init.")
            v = None
        return v

    @classmethod
    def validate(cls: Type["INIBasedModel"], value: Any) -> "INIBasedModel":
        if isinstance(value, Section):
            value = value.flatten(
                cls._duplicate_keys_as_list(), cls._supports_comments()
            )

        return super().validate(value)

    @classmethod
    def _exclude_fields(cls) -> Set:
        return {"comments", "datablock", "_header"}

    @staticmethod
    def _convert_value(v: Any) -> str:
        if isinstance(v, bool):
            return str(int(v))
        elif isinstance(v, list):
            return ";".join([str(x) for x in v])
        elif v is None:
            return ""
        else:
            return str(v)

    def _to_section(self) -> Section:
        props = []
        for key, value in self:
            if key in self._exclude_fields():
                continue

            if key in self.__fields__:
                key = self.__fields__[key].alias

            prop = Property(
                key=key,
                value=INIBasedModel._convert_value(value),
                comment=getattr(self.comments, key, None),
            )
            props.append(prop)
        return Section(header=self._header, content=props)


class DataBlockINIBasedModel(INIBasedModel):
    """DataBlockINIBasedModel defines the base model for ini models with datablocks."""

    datablock: List[List[float]] = []

    _make_lists = make_list_validator("datablock")

    def _to_section(self) -> Section:
        section = super()._to_section()
        section.datablock = self.datablock
        return section


class INIGeneral(INIBasedModel):
    _header: Literal["General"] = "General"
    fileversion: str = Field("3.00", alias="fileVersion")
    filetype: str = Field(alias="fileType")

    @classmethod
    def _supports_comments(cls):
        return True


class FrictGeneral(INIGeneral):
    fileversion: str = Field("3.00", alias="fileVersion")
    filetype: Literal["roughness"] = Field("roughness", alias="fileType")


class CrossdefGeneral(INIGeneral):
    fileversion: str = Field("3.00", alias="fileVersion")
    filetype: Literal["crossDef"] = Field("crossDef", alias="fileType")


class CrosslockGeneral(INIGeneral):
    fileversion: str = Field("3.00", alias="fileVersion")
    filetype: Literal["crossLoc"] = Field("crossLoc", alias="fileType")


class INIModel(FileModel):
    """INI Model representation."""

    general: INIGeneral

    @classmethod
    def _ext(cls) -> str:
        return ".ini"

    @classmethod
    def _filename(cls) -> str:
        return "fm"

    @classmethod
    def _get_serializer(cls):
        pass  # unused in favor of direct _serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return Parser.parse

    def _to_document(self) -> Document:
        header = CommentBlock(lines=[f"written by HYDROLIB-core {version}"])
        sections = []
        for _, value in self:
            if _ == "filepath" or value is None:
                continue
            if isinstance(value, list):
                for v in value:
                    sections.append(v._to_section())
            else:
                sections.append(value._to_section())
        return Document(header_comment=[header], sections=sections)

    def _serialize(self, _: dict) -> None:
        # We skip the passed dict for a better one.
        config = SerializerConfig(section_indent=0, property_indent=4)
        write_ini(self.filepath, self._to_document(), config=config)


class CrossSectionDefinition(INIBasedModel):
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


class CrossDefModel(INIModel):
    general: CrossdefGeneral = CrossdefGeneral()
    definition: List[CrossSectionDefinition] = []

    _make_list = make_list_validator("definition")

    @classmethod
    def _filename(cls) -> str:
        return "crsdef"


class CircleCrsDef(CrossSectionDefinition):
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
    frictiontype: Optional[str] = Field(alias="frictionType")
    frictionvalue: Optional[float] = Field(alias="frictionValue")


class RectangleCrsDef(CrossSectionDefinition):
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
    frictiontype: Optional[str] = Field(alias="frictionType")
    frictionvalue: Optional[float] = Field(alias="frictionValue")


class ZWRiverCrsDef(CrossSectionDefinition):
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
    frictiontypes: Optional[List[str]] = Field(alias="frictionTypes")
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


class ZWCrsDef(CrossSectionDefinition):
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
    frictiontype: Optional[str] = Field(alias="frictionType")
    frictionvalue: Optional[float] = Field(alias="frictionValue")

    _split_to_list = get_split_string_on_delimiter_validator(
        "levels",
        "flowwidths",
        "totalwidths",
        delimiter=" ",
    )


class YZCrsDef(CrossSectionDefinition):
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
    frictionpositions: List[float] = Field(alias="frictionPositions")
    frictionids: Optional[List[str]] = Field(alias="frictionIds")
    frictiontypes: Optional[List[str]] = Field(alias="frictionTypes")
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


class XYZCrsDef(YZCrsDef, CrossSectionDefinition):
    """
    A class for XYZ Cross section definitions.

    This class extends the YZCrsDef class with x-coordinates and an optional
    branchId field. Most other attributes are inherited, but the coordcount
    is overridden under the Pydantic alias "xyzCount".
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


class CrossSection(INIBasedModel):
    _header: Literal["CrossSection"] = "CrossSection"
    id: str = Field(alias="id")
    branchid: str = Field(alias="branchId")


class CrossLocModel(INIModel):
    general: CrosslockGeneral = CrosslockGeneral()
    crosssection: List[CrossSection] = []

    @classmethod
    def _filename(cls) -> str:
        return "crsloc"


class Global(INIBasedModel):
    _header: Literal["Global"] = "Global"
    frictionid: str = Field(alias="frictionId")
    frictiontype: str = Field(alias="frictionType")
    frictionvalue: float = Field(alias="frictionValue")


class FrictionModel(INIModel):
    general: FrictGeneral = FrictGeneral()
    global_: List[Global] = Field([], alias="global")  # to circumvent built-in kw

    _split_to_list = make_list_validator(
        "global_",
    )
