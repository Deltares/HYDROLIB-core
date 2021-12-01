import logging
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import Field

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.util import get_split_string_on_delimiter_validator

from ..ini.util import make_list_validator

logger = logging.getLogger(__name__)


class FrictGeneral(INIGeneral):
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
    frictiontype: str = Field(alias="frictionType")
    frictionvalue: float = Field(alias="frictionValue")


class FrictBranch(INIBasedModel):
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
    frictiontype: str = Field(alias="frictionType")
    functiontype: Optional[str] = Field("constant", alias="functionType")
    timeseriesid: Optional[str] = Field(alias="timeSeriesId")
    numlevels: Optional[int] = Field(alias="numLevels")
    levels: Optional[List[float]]
    numlocations: Optional[int] = Field(0, alias="numLocations")
    chainage: Optional[List[float]]
    frictionvalues: Optional[List[float]] = Field(
        alias="frictionValues"
    )  # TODO: turn this into List[List[float]]

    _split_to_list = get_split_string_on_delimiter_validator(
        "levels",
        "chainage",
        "frictionvalues",
        delimiter=" ",
    )

    _make_lists = make_list_validator("frictionvalues")


class FrictionModel(INIModel):
    general: FrictGeneral = FrictGeneral()
    global_: FrictGlobal = Field(alias="global")  # to circumvent built-in kw
    branch: List[FrictBranch] = []

    _split_to_list = make_list_validator(
        "branch",
    )

    @classmethod
    def _ext(cls) -> str:
        return ".ini"

    @classmethod
    def _filename(cls) -> str:
        return "roughness"
