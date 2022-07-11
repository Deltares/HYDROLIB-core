from typing import List, Literal, Optional
from pydantic.fields import Field

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.util import (
    get_location_specification_rootvalidator
)


class ObservationPointCrossSectionGeneral(INIGeneral):
    """The observation point cross section file's `[General]` section with file meta data."""

    class Comments(INIBasedModel.Comments):
        fileversion: Optional[str] = Field(
            "File version. Do not edit this.", alias="fileVersion"
        )
        filetype: Optional[str] = Field(
            "File type. Should be 'obsCross'. Do not edit this.",
            alias="fileType"
        )

    comments: Comments = Comments()
    fileversion: str = Field("2.00", alias="fileVersion")
    filetype: Literal["obsCross"] = Field("obsCross", alias="fileType")


class ObservationPointCrossSection(INIBasedModel):
    """
    The cross section of an observation point that is included in the
    observation cross section file.

    All lowercased attributes match with the observation point cross
    section output as described in [UM Sec.F2.4.1]
    (https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsubsection.F.2.4.1)
    """

    class Comments(INIBasedModel.Comments):
        name: Optional[str] = "Name of the cross section (max. 255 characters)."
        branchid: Optional[str] = Field(
            "(optional) Branch on which the cross section is located.",
            alias="branchId"
        )
        chainage: Optional[str] = "(optional) Location on the branch (m)."
        numcoordinates: Optional[str] = Field(
            ("(optional) Number of values in xCoordinates and yCoordinates. "
             "This value should be greater than or equal to 2."),
            alias="numCoordinates"
        )
        xcoordinates: Optional[str] = Field(
            ("(optional) x-coordinates of the cross section line."
             "(number of values = numCoordinates)"),
            alias="xCoordinates"
        )
        ycoordinates: Optional[str] = Field(
            ("(optional) y-coordinates of the cross section line."
             "(number of values = numCoordinates)"),
            alias="yCoordinates"
        )

    comments: Comments = Comments()
    _header: Literal["ObservationCrossSection"] = "ObservationCrossSection"
    name: str = Field(max_length=255)
    branchid: Optional[str] = Field(alias="branchId")
    chainage: Optional[float] = Field()
    numcoordinates: Optional[List[float]] = Field(alias="numCoordinates")
    xcoordinates: Optional[List[float]] = Field(alias="xCoordinates")
    ycoordinates: Optional[List[float]] = Field(alias="yCoordinates")

    _location_validator = get_location_specification_rootvalidator(
        allow_nodeid=False
    )


class ObservationPointCrossSectionModel(INIModel):
    """
    The overall observation point crosssection model that contains the contents
    of one observation point crosssection file.
    """

    general: ObservationPointCrossSectionGeneral = ObservationPointCrossSectionGeneral()
    crosssections: List[ObservationPointCrossSection] = []
