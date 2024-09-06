"""
namespace for storing the branches as branches.gui file
"""

# TODO reconsider the definition and/or filename of the branches.gui (from Prisca)

import logging
from typing import List, Literal, Optional

from pydantic.v1.class_validators import root_validator, validator
from pydantic.v1.fields import Field

from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.util import make_list_validator

logger = logging.getLogger(__name__)


# FIXME: GUI does not recongnize this section yet
class BranchGeneral(INIGeneral):
    """The branches.gui file's `[General]` section with file meta data."""

    class Comments(INIBasedModel.Comments):
        fileversion: Optional[str] = Field(
            "File version. Do not edit this.", alias="fileVersion"
        )
        filetype: Optional[str] = Field(
            "File type. Should be 'branches'. Do not edit this.",
            alias="fileType",
        )

    comments: Comments = Comments()
    _header: Literal["General"] = "General"
    fileversion: str = Field("2.00", alias="fileVersion")
    filetype: Literal["branches"] = Field("branches", alias="fileType")


class Branch(INIBasedModel):
    """
    A branch that is included in the branches.gui file.
    """

    class Comments(INIBasedModel.Comments):
        name: Optional[str] = "Unique branch id."
        branchtype: Optional[str] = Field(
            "Channel = 0, SewerConnection = 1, Pipe = 2.", alias="branchType"
        )
        islengthcustom: Optional[str] = Field(
            "branch length specified by user.", alias="isLengthCustom"
        )
        sourcecompartmentname: Optional[str] = Field(
            "Source compartment name this sewer connection is beginning.",
            alias="sourceCompartmentName",
        )
        targetcompartmentname: Optional[str] = Field(
            "Source compartment name this sewer connection is beginning.",
            alias="targetCompartmentName",
        )
        material: Optional[str] = Field(
            "0 = Unknown, 1 = Concrete, 2 = CastIron, 3 = StoneWare, 4 = Hdpe, "
            "5 = Masonry, 6 = SheetMetal, 7 = Polyester, 8 = Polyvinylchlorid, 9 = Steel"
        )

    comments: Comments = Comments()

    _header: Literal["Branch"] = "Branch"

    name: str = Field("name", max_length=255, alias="name")
    branchtype: int = Field(0, alias="branchType")
    islengthcustom: Optional[bool] = Field(True, alias="isLengthCustom")
    sourcecompartmentname: Optional[str] = Field(None, alias="sourceCompartmentName")
    targetcompartmentname: Optional[str] = Field(None, alias="targetCompartmentName")
    material: Optional[int] = Field(None, alias="material")

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("name")

    @root_validator
    @classmethod
    def _validate_branch(cls, values: dict):
        if values.get("branchtype") == 2 and (
            values.get("sourcecompartmentname") is None
            and values.get("targetcompartmentname") is None
        ):
            raise ValueError(
                "Either sourceCompartmentName or targetCompartmentName should be provided when branchType is 2."
            )

        return values

    @validator("branchtype")
    def _validate_branchtype(cls, branchtype: int):
        allowed_branchtypes = [0, 1, 2]
        if branchtype not in allowed_branchtypes:
            str_allowed_branchtypes = [str(i) for i in allowed_branchtypes]
            error_msg = f"branchType ({branchtype}) is not allowed. Allowed values: {', '.join(str_allowed_branchtypes)}"
            raise ValueError(error_msg)

        return branchtype

    @validator("material")
    def _validate_material(cls, material: int):
        allowed_materials = range(10)
        if material not in allowed_materials:
            str_allowed_materials = [str(i) for i in allowed_materials]
            error_msg = f"material ({material}) is not allowed. Allowed values: {', '.join(str_allowed_materials)}"
            raise ValueError(error_msg)

        return material


class BranchModel(INIModel):
    """
    The overall branch model that contains the contents of one branches.gui file.

    This model is not referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel].

    Attributes:
        general (BranchGeneral): `[General]` block with file metadata.
        branch(List[Branch]): List of `[Branch]` blocks for all branches.
    """

    general: BranchGeneral = BranchGeneral()
    branch: List[Branch] = []

    _make_list = make_list_validator("branch")

    @classmethod
    def _ext(cls) -> str:
        return ".gui"

    @classmethod
    def _filename(cls) -> str:
        return "branches"
