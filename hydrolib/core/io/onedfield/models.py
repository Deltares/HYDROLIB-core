import logging
from typing import List, Literal, Optional

from pydantic import Field
from pydantic.class_validators import validator
from pydantic.types import NonNegativeInt

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.util import (
    get_split_string_on_delimiter_validator,
    make_list_length_root_validator,
    make_list_validator,
)

logger = logging.getLogger(__name__)


class OneDFieldGeneral(INIGeneral):
    """The 1D field file's `[General]` section with file meta data."""

    class Comments(INIBasedModel.Comments):
        fileversion: Optional[str] = Field(
            "File version. Do not edit this.", alias="fileVersion"
        )
        filetype: Optional[str] = Field(
            "File type. Should be '1dField'. Do not edit this.",
            alias="fileType",
        )

    comments: Comments = Comments()
    _header: Literal["General"] = "General"

    fileversion: str = Field("2.00", alias="fileVersion")
    filetype: Literal["1dField"] = Field("1dField", alias="fileType")


class OneDFieldGlobal(INIBasedModel):
    """The `[Global]` block with a uniform value for use inside a 1D field file."""

    class Comments(INIBasedModel.Comments):
        quantity: Optional[str] = Field("The name of the quantity", alias="quantity")
        unit: Optional[str] = Field("The unit of the quantity", alias="unit")
        value: Optional[str] = Field(
            "The global default value for this quantity", alias="value"
        )

    comments: Comments = Comments()
    _header: Literal["Global"] = "Global"

    quantity: str = Field(alias="quantity")
    unit: str = Field(alias="unit")
    value: float = Field(alias="value")


class OneDFieldBranch(INIBasedModel):
    """
    A `[Branch]` block for use inside a 1D field file.

    Each block can define value(s) on a particular branch.
    """

    class Comments(INIBasedModel.Comments):
        branchid: Optional[str] = Field("The name of the branch", alias="branchId")
        numlocations: Optional[str] = Field(
            "Number of locations on branch. The default 0 value implies branch uniform values.",
            alias="numLocations",
        )
        chainage: Optional[str] = Field(
            "Space separated list of locations on the branch (m). Locations sorted by increasing chainage. The keyword must be specified if numLocations >0.",
            alias="chainage",
        )
        values: Optional[str] = Field(
            "Space separated list of numLocations values; one for each chainage specified. One value required if numLocations =0",
            alias="values",
        )

    comments: Comments = Comments()
    _header: Literal["Branch"] = "Branch"

    branchid: str = Field(alias="branchId")
    numlocations: Optional[NonNegativeInt] = Field(0, alias="numLocations")
    chainage: Optional[List[float]] = Field(alias="chainage")
    values: List[float] = Field(alias="values")

    _split_to_list = get_split_string_on_delimiter_validator(
        "chainage",
        "values",
        delimiter=" ",
    )

    _check_list_length_values = make_list_length_root_validator(
        "chainage",
        length_name="numlocations",
        list_required_with_length=True,
    )

    _check_list_length_chainage = make_list_length_root_validator(
        "values",
        length_name="numlocations",
        list_required_with_length=True,
        min_length=1,
    )

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("branchid")


class OneDFieldModel(INIModel):
    """
    The overall 1D field model that contains the contents of a 1D field file.

    This model is typically used when a [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry.inifieldfile[..].initial[..].datafiletype==DataFileType.onedfield`.

    Attributes:
        general (OneDFieldGeneral): `[General]` block with file metadata.
        global_ (Optional[OneDFieldGlobal]): Optional `[Global]` block with uniform value.
        branch (List[OneDFieldBranch]): Definitions of `[Branch]` field values.
    """

    general: OneDFieldGeneral = OneDFieldGeneral()
    global_: Optional[OneDFieldGlobal] = Field(
        alias="global"
    )  # to circumvent built-in kw
    branch: List[OneDFieldBranch] = []

    _split_to_list = make_list_validator(
        "branch",
    )

    @classmethod
    def _ext(cls) -> str:
        return ".ini"

    @classmethod
    def _filename(cls) -> str:
        return "1dfield"
