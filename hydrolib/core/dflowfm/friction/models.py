import logging
from pathlib import Path
from typing import Annotated, List, Literal, Optional

from pydantic import (
    BeforeValidator,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic.types import NonNegativeInt, PositiveInt
from strenum import StrEnum

from hydrolib.core.base.models import (
    DiskOnlyFileModel,
    set_default_disk_only_file_model,
)
from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.util import (
    enum_value_parser,
    make_list,
    split_string_on_delimiter,
)

logger = logging.getLogger(__name__)


class FrictionType(StrEnum):
    """
    Enum class containing the valid values for the frictionType
    attribute in several subclasses of Structure/CrossSection/friction.models.

    Args:
        chezy: str
            Chézy C [m 1/2 /s]
        manning: str
            Manning n [s/m 1/3 ]
        walllawnikuradse: str
            Nikuradse k_n [m]
        whitecolebrook: str
            Nikuradse k_n [m]
        stricklernikuradse: str
            Nikuradse k_n [m]
        strickler: str
            Strickler k_s [m 1/3 /s]
        debosbijkerk: str
            De Bos-Bijkerk γ [1/s]
    """

    chezy = "Chezy"
    manning = "Manning"
    walllawnikuradse = "wallLawNikuradse"
    whitecolebrook = "WhiteColebrook"
    stricklernikuradse = "StricklerNikuradse"
    strickler = "Strickler"
    debosbijkerk = "deBosBijkerk"


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
    frictionvaluesfile: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="frictionValuesFile"
    )

    @field_validator("frictionvaluesfile", mode="before")
    @classmethod
    def _validate_frictionvaluesfile(cls, v: Optional[DiskOnlyFileModel]):
        """Validate the frictionValuesFile field to ensure it is a DiskOnlyFileModel."""
        if isinstance(v, (str, Path)):
            return DiskOnlyFileModel(v)
        return v


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

    @field_validator("frictiontype", mode="before")
    @classmethod
    def _validate_frictiontype(cls, v: str) -> FrictionType:
        return enum_value_parser(v, FrictionType)

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
    timeseriesid: Optional[str] = Field(None, alias="timeSeriesId")
    numlevels: Optional[PositiveInt] = Field(None, alias="numLevels")
    levels: Optional[List[float]] = Field(None)
    numlocations: Optional[NonNegativeInt] = Field(0, alias="numLocations")
    chainage: Optional[List[float]] = Field(None)
    frictionvalues: Optional[List[float]] = Field(None, alias="frictionValues")

    @field_validator("levels", "chainage", "frictionvalues", mode="before")
    @classmethod
    def split_field_values(cls, v, info: ValidationInfo) -> Optional[List[float]]:
        return split_string_on_delimiter(cls, v, info)

    @field_validator("frictiontype", mode="before")
    @classmethod
    def _validate_frictiontype(cls, v: str) -> FrictionType:
        return enum_value_parser(v, FrictionType)

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("branchid")

    @field_validator("levels", mode="after")
    @classmethod
    def _validate_levels(cls, v: Optional[List[float]], info: ValidationInfo):
        numlevels = info.data.get("numlevels")
        branchid = info.data.get("branchid", "")
        if v is not None and (numlevels is None or len(v) != numlevels):
            raise ValueError(
                f"Number of values for levels should be equal to the numLevels value (branchId={branchid})."
            )

        return v

    @field_validator("chainage", mode="after")
    @classmethod
    def _validate_chainage(cls, v: Optional[List[float]], info: ValidationInfo):
        numlocations = info.data.get("numlocations")
        branchid = info.data.get("branchid", "")
        if v is not None and len(v) != numlocations:
            raise ValueError(
                f"Number of values for chainage should be equal to the numLocations value (branchId={branchid})."
            )

        return v

    @field_validator("frictionvalues", mode="after")
    @classmethod
    def _validate_frictionvalues(cls, v: Optional[List[float]], info: ValidationInfo):
        numlevels = info.data.get("numlevels") or 1
        numlocations = info.data.get("numlocations") or 0
        branchid = info.data.get("branchid", "")
        # number of values should be equal to numlocations*numlevels
        numvals = max(1, numlocations) * numlevels

        if v is not None and len(v) != numvals:
            raise ValueError(
                f"Number of values for frictionValues should be equal to the numLocations*numLevels value (branchId={branchid})."
            )

        return v

    @model_validator(mode="after")
    @classmethod
    def validate_all(cls, values):
        v = values
        if v.levels is not None:
            if v.numlevels is None or len(v.levels) != v.numlevels:
                raise ValueError(
                    f"Number of values for levels should be equal to the numLevels value (branchId={v.branchid})."
                )

        if v.chainage is not None and len(v.chainage) != v.numlocations:
            raise ValueError(
                f"Number of values for chainage should be equal to the numLocations value (branchId={v.branchid})."
            )

        if v.frictionvalues is not None:
            numlevels = 1 if not v.numlevels else v.numlevels
            numvals = max(1, v.numlocations) * numlevels
            if len(v.frictionvalues) != numvals:
                raise ValueError(
                    f"Number of values for frictionValues should be equal to the numLocations*numLevels value (branchId={v.branchid})."
                )

        return v


class FrictionModel(INIModel):
    """
    The overall friction model that contains the contents of one friction file.

    This model is typically referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.frictfile[..]`.

    Attributes:
        general (FrictGeneral): `[General]` block with file metadata.
        global_ (List[FrictGlobal]): Definitions of `[Global]` friction classes.
        branch (List[FrictBranch]): Definitions of `[Branch]` friction values.
    """

    general: FrictGeneral = FrictGeneral()
    global_: Annotated[List[FrictGlobal], BeforeValidator(make_list)] = Field(
        default_factory=list, alias="global"
    )  # to circumvent built-in kw
    branch: Annotated[List[FrictBranch], BeforeValidator(make_list)] = []

    @classmethod
    def _ext(cls) -> str:
        return ".ini"

    @classmethod
    def _filename(cls) -> str:
        return "roughness"
