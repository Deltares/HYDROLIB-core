import logging
from enum import Enum
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import Field, NonNegativeInt, PositiveInt
from pydantic.class_validators import validator

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.util import (
    get_enum_validator,
    get_split_string_on_delimiter_validator,
    make_list_validator,
)

logger = logging.getLogger(__name__)


class FrictionType(str, Enum):
    """
    Enum class containing the valid values for the frictionType
    attribute in several subclasses of Structure/CrossSection/friction.models.
    """

    chezy = "Chezy"
    """str: Chézy C [m 1/2 /s]"""

    manning = "Manning"
    """str: Manning n [s/m 1/3 ]"""

    walllawnikuradse = "wallLawNikuradse"
    """str: Nikuradse k_n [m]"""

    whitecolebrook = "WhiteColebrook"
    """str: Nikuradse k_n [m]"""

    stricklernikuradse = "StricklerNikuradse"
    """str: Nikuradse k_n [m]"""

    strickler = "Strickler"
    """str: Strickler k_s [m 1/3 /s]"""

    debosbijkerk = "deBosBijkerk"
    """str: De Bos-Bijkerk γ [1/s]"""


class FrictGeneral(INIGeneral):
    """The friction file's `[General]` section with file meta data."""

    class Comments(INIBasedModel.Comments):
        fileversion: Optional[str] = Field(
            "File version. Do not edit this.", alias="fileVersion"
        )
        filetype: Optional[str] = Field(
            "File type. Should be 'roughness'. Do not edit this.",
            alias="fileType",
        )
        frictionvaluesfile: Optional[str] = Field(
            "Name of <*.bc> file containing the timeseries with friction values. "
            + "Only needed for functionType = timeSeries.",
            alias="frictionValuesFile",
        )

    comments: Comments = Comments()
    _header: Literal["General"] = "General"
    fileversion: str = Field("3.01", alias="fileVersion")
    filetype: Literal["roughness"] = Field("roughness", alias="fileType")
    frictionvaluesfile: Optional[Path] = Field(alias="frictionValuesFile")


class FrictGlobal(INIBasedModel):
    """A `[Global]` block for use inside a friction file.

    Multiple of such blocks may be present to define multiple frictionId classes.
    """

    class Comments(INIBasedModel.Comments):
        frictionid: Optional[str] = Field(
            "Name of the roughness variable.", alias="frictionId"
        )
        frictiontype: Optional[str] = Field(
            "The global roughness type for this variable, which is used "
            + "if no branch specific roughness definition is given.",
            alias="frictionType",
        )
        frictionvalue: Optional[str] = Field(
            "The global default value for this roughness variable.",
            alias="frictionValue",
        )

    comments: Comments = Comments()
    _header: Literal["Global"] = "Global"
    frictionid: str = Field(alias="frictionId")
    frictiontype: FrictionType = Field(alias="frictionType")
    frictionvalue: float = Field(alias="frictionValue")

    _frictiontype_validator = get_enum_validator("frictiontype", enum=FrictionType)

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("frictionid")


class FrictBranch(INIBasedModel):
    """A `[Branch]` block for use inside a friction file.

    Each block can define the roughness value(s) on a particular branch.
    """

    class Comments(INIBasedModel.Comments):
        branchid: Optional[str] = Field("The name of the branch.", alias="branchId")
        frictiontype: Optional[str] = Field(
            "The roughness type to be used on this branch.", alias="frictionType"
        )
        functiontype: Optional[str] = Field(
            "Function type for the calculation of the value. "
            + "Possible values: constant, timeSeries, absDischarge, waterlevel.",
            alias="functionType",
        )
        timeseriesid: Optional[str] = Field(
            "Refers to a data block in the <*.bc> frictionValuesFile. "
            + "Only if functionType = timeSeries.",
            alias="timeSeriesId",
        )
        numlevels: Optional[str] = Field(
            "Number of levels in table. Only if functionType is not constant.",
            alias="numLevels",
        )
        levels: Optional[str] = Field(
            "Space separated list of discharge [m3/s] or water level [m AD] values. "
            + "Only if functionType is absDischarge or waterLevel."
        )
        numlocations: Optional[str] = Field(
            "Number of locations on branch. The default 0 implies branch uniform values.",
            alias="numLocations",
        )
        chainage: Optional[str] = Field(
            "Space separated list of locations on the branch [m]. Locations sorted by "
            + "increasing chainage. The keyword must be specified if numLocations>0."
        )
        frictionvalues: Optional[str] = Field(
            "numLevels lines containing space separated lists of roughness values: "
            + "numLocations values per line. If the functionType is constant, then a "
            + "single line is required. For a uniform roughness per branch "
            + "(numLocations = 0) a single entry per line is required. The meaning "
            + "of the values depends on the roughness type selected (see frictionType).",
            alias="frictionValues",
        )

    comments: Comments = Comments()
    _header: Literal["Branch"] = "Branch"
    branchid: str = Field(alias="branchId")
    frictiontype: FrictionType = Field(alias="frictionType")
    functiontype: Optional[str] = Field("constant", alias="functionType")
    timeseriesid: Optional[str] = Field(alias="timeSeriesId")
    numlevels: Optional[PositiveInt] = Field(alias="numLevels")
    levels: Optional[List[float]]
    numlocations: Optional[NonNegativeInt] = Field(0, alias="numLocations")
    chainage: Optional[List[float]]
    frictionvalues: Optional[List[float]] = Field(
        alias="frictionValues"
    )  # TODO: turn this into List[List[float]], see issue #143.

    _split_to_list = get_split_string_on_delimiter_validator(
        "levels",
        "chainage",
        "frictionvalues",
        delimiter=" ",
    )

    _frictiontype_validator = get_enum_validator("frictiontype", enum=FrictionType)

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("branchid")

    @validator("levels", always=True)
    @classmethod
    def _validate_levels(cls, v, values):
        if v is not None and (
            values["numlevels"] is None or len(v) != values["numlevels"]
        ):
            raise ValueError(
                f"Number of values for levels should be equal to the numLevels value (branchId={values.get('branchid', '')})."
            )

        return v

    @validator("chainage", always=True)
    @classmethod
    def _validate_chainage(cls, v, values):
        if v is not None and len(v) != values["numlocations"]:
            raise ValueError(
                f"Number of values for chainage should be equal to the numLocations value (branchId={values.get('branchid', '')})."
            )

        return v

    @validator("frictionvalues", always=True)
    @classmethod
    def _validate_frictionvalues(cls, v, values):
        # number of values should be equal to numlocations*numlevels
        numlevels = (
            1
            if (
                "numlevels" not in values
                or values["numlevels"] is None
                or values["numlevels"] == 0
            )
            else values["numlevels"]
        )
        numvals = max(1, values["numlocations"]) * numlevels
        if v is not None and len(v) != numvals:
            raise ValueError(
                f"Number of values for frictionValues should be equal to the numLocations*numLevels value (branchId={values.get('branchid', '')})."
            )

        return v


class FrictionModel(INIModel):
    """
    The overall friction model that contains the contents of one friction file.

    This model is typically referenced under a [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry.frictfile[..]`.

    Attributes:
        general (FrictGeneral): `[General]` block with file metadata.
        global_ (List[FrictGlobal]): Definitions of `[Global]` friction classes.
        branch (List[FrictBranch]): Definitions of `[Branch]` friction values.
    """

    general: FrictGeneral = FrictGeneral()
    global_: List[FrictGlobal] = Field([], alias="global")  # to circumvent built-in kw
    branch: List[FrictBranch] = []

    _split_to_list = make_list_validator(
        "global_",
        "branch",
    )

    @classmethod
    def _ext(cls) -> str:
        return ".ini"

    @classmethod
    def _filename(cls) -> str:
        return "roughness"
