from typing import Dict, List, Literal, Optional

from pydantic.class_validators import root_validator
from pydantic.fields import Field

from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.util import (
    LocationValidationConfiguration,
    get_split_string_on_delimiter_validator,
    validate_location_specification,
)


class ObservationCrossSectionGeneral(INIGeneral):
    """The observation cross section file's `[General]` section with file meta data."""

    class Comments(INIBasedModel.Comments):
        fileversion: Optional[str] = Field(
            "File version. Do not edit this.", alias="fileVersion"
        )
        filetype: Optional[str] = Field(
            "File type. Should be 'obsCross'. Do not edit this.", alias="fileType"
        )

    comments: Comments = Comments()
    fileversion: str = Field("2.00", alias="fileVersion")
    filetype: Literal["obsCross"] = Field("obsCross", alias="fileType")


class ObservationCrossSection(INIBasedModel):
    """
    The observation cross section that is included in the
    observation cross section file.

    All lowercased attributes match with the observation cross
    section output as described in [UM Sec.F2.4.1]
    (https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsubsection.F.2.4.1)
    """

    class Comments(INIBasedModel.Comments):
        name: Optional[str] = "Name of the cross section (max. 255 characters)."
        branchid: Optional[str] = Field(
            "(optional) Branch on which the cross section is located.", alias="branchId"
        )
        chainage: Optional[str] = "(optional) Location on the branch (m)."
        numcoordinates: Optional[str] = Field(
            "(optional) Number of values in xCoordinates and yCoordinates. "
            "This value should be greater than or equal to 2.",
            alias="numCoordinates",
        )
        xcoordinates: Optional[str] = Field(
            "(optional) x-coordinates of the cross section line. "
            "(number of values = numCoordinates)",
            alias="xCoordinates",
        )
        ycoordinates: Optional[str] = Field(
            "(optional) y-coordinates of the cross section line. "
            "(number of values = numCoordinates)",
            alias="yCoordinates",
        )

    comments: Comments = Comments()
    _header: Literal["ObservationCrossSection"] = "ObservationCrossSection"
    name: str = Field(max_length=255, alias="name")
    branchid: Optional[str] = Field(alias="branchId")
    chainage: Optional[float] = Field(alias="chainage")
    numcoordinates: Optional[int] = Field(alias="numCoordinates")
    xcoordinates: Optional[List[float]] = Field(alias="xCoordinates")
    ycoordinates: Optional[List[float]] = Field(alias="yCoordinates")

    _split_to_list = get_split_string_on_delimiter_validator(
        "xcoordinates", "ycoordinates"
    )

    @root_validator(allow_reuse=True)
    def validate_that_location_specification_is_correct(cls, values: Dict) -> Dict:
        """Validates that the correct location specification is given."""
        return validate_location_specification(
            values,
            config=LocationValidationConfiguration(
                validate_node=False, minimum_num_coordinates=2
            ),
        )

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("name")


class ObservationCrossSectionModel(INIModel):
    """
    The overall observation cross section model that contains the contents
    of one observation cross section file.
    """

    general: ObservationCrossSectionGeneral = ObservationCrossSectionGeneral()
    observationcrosssection: List[ObservationCrossSection] = []
