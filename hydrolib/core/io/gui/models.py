"""
namespace for storing the branches as branches.gui file
"""
# TODO reconsider the definition and/or filename of the branches.gui (from Prisca)

import logging

from typing import List, Literal, Optional
from pydantic.class_validators import root_validator, validator
from pydantic.fields import Field

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.util import make_list_validator
from hydrolib.core.basemodel import BaseModel, ParsableFileModel
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
        branchtype: Optional[str] = Field("Channel = 0, SewerConnection = 1, Pipe = 2.", alias="branchType")
        islengthcustom: Optional[str] = Field(
            "branch length specified by user.", alias="isLengthCustom"
        )
        sourcecompartmentname: Optional[str] = Field("Source compartment name this sewer connection is beginning.", alias="sourceCompartmentName")
        targetcompartmentname: Optional[str] = Field("Source compartment name this sewer connection is beginning.", alias="targetCompartmentName")
        material: Optional[str] = Field("0 = Unknown, 1 = Concrete, 2 = CastIron, 3 = StoneWare, 4 = Hdpe, "
                                        "5 = Masonry, 6 = SheetMetal, 7 = Polyester, 8 = Polyvinylchlorid, 9 = Steel")

    comments: Comments = Comments()

    _header: Literal["Branch"] = "Branch"

    name: str = Field("name", max_length=255, alias="name")
    branchtype: int = Field(0, alias="branchType")
    islengthcustom: Optional[bool] = Field(
        True, alias="isLengthCustom"
    )
    sourcecompartmentname: Optional[str] = Field(None, alias="sourceCompartmentName")
    targetcompartmentname: Optional[str] = Field(None, alias="targetCompartmentName")
    material: Optional[int] = Field(None, alias="material")

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("name")

    @validator("branchtype")
    def _validate_branchtype(cls, branchtype: int):
        if branchtype not in [0, 1, 2]:
            raise ValueError(f"branchtype is not allowed {branchtype}")
        return branchtype

    @validator("material")
    def _validate_material(cls, material: int):
        if material not in [range(10)]:
            raise ValueError("material is not allowed")
        return material

class BranchModel(INIModel):
    """
    The overall branch model that contains the contents of one branches.gui file.

    This model is not referenced under a [FMModel][hydrolib.core.io.mdu.models.FMModel].

    Attributes:
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

    @validator("branch", each_item=True)
    def _validate(cls, branch: Branch):
        """Validates for each pipe whether the compartment info is filled in
        """

        if (
            branch.branchtype == 2
            and (branch.sourcecompartmentname is None
            and branch.targetcompartmentname is None)
        ):
            raise ValueError(
                f"Either source or target compartment name should be provided when branchtype is 2 for branch id {branch.name}"
            )

        return branch


