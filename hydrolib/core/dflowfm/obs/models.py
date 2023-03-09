from typing import Dict, List, Literal, Optional

from pydantic.class_validators import root_validator
from pydantic.fields import Field

from hydrolib.core.dflowfm.common.models import LocationType
from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.util import (
    LocationValidationConfiguration,
    LocationValidationFieldNames,
    get_enum_validator,
    make_list_validator,
    validate_location_specification,
)


class ObservationPointGeneral(INIGeneral):
    """The observation point file's `[General]` section with file meta data."""

    class Comments(INIBasedModel.Comments):
        fileversion: Optional[str] = Field(
            "File version. Do not edit this.", alias="fileVersion"
        )
        filetype: Optional[str] = Field(
            "File type. Should be 'obsPoints'. Do not edit this.",
            alias="fileType",
        )

    comments: Comments = Comments()
    _header: Literal["General"] = "General"
    fileversion: str = Field("2.00", alias="fileVersion")
    filetype: Literal["obsPoints"] = Field("obsPoints", alias="fileType")


class ObservationPoint(INIBasedModel):
    """
    An observation point that is included in the observation point file.

    All lowercased attributes match with the observation point input as described in
    [UM Sec.F.2.2.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsubsection.F.2.2.1).
    """

    class Comments(INIBasedModel.Comments):
        name: Optional[str] = "Name of the observation point (max. 255 characters)."
        locationtype: Optional[
            str
        ] = "Only when x and y are also specified. 1d: snap to closest 1D grid point, 2d: snap to closest 2D grid cell centre, all: snap to closest 1D or 2D point."
        branchid: Optional[str] = Field(
            "Branch on which the observation point is located.", alias="branchId"
        )
        chainage: Optional[str] = "Chainage on the branch (m)."

        x: Optional[str] = Field(
            "x-coordinate of the location of the observation point.",
            alias="x",
        )
        y: Optional[str] = Field(
            "y-coordinate of the location of the observation point.",
            alias="y",
        )

    comments: Comments = Comments()

    _header: Literal["ObservationPoint"] = "ObservationPoint"

    name: str = Field("id", max_length=255, alias="name")
    locationtype: Optional[LocationType] = Field(None, alias="locationType")

    branchid: Optional[str] = Field(None, alias="branchId")
    chainage: Optional[float] = Field(None, alias="chainage")

    x: Optional[float] = Field(None, alias="x")
    y: Optional[float] = Field(None, alias="y")

    _type_validator = get_enum_validator("locationtype", enum=LocationType)

    @root_validator(allow_reuse=True)
    def validate_that_location_specification_is_correct(cls, values: Dict) -> Dict:
        """Validates that the correct location specification is given."""
        return validate_location_specification(
            values,
            config=LocationValidationConfiguration(
                validate_node=False, validate_num_coordinates=False
            ),
            fields=LocationValidationFieldNames(x_coordinates="x", y_coordinates="y"),
        )

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("name")


class ObservationPointModel(INIModel):
    """
    The overall observation point model that contains the contents of one observation point file.

    This model is typically referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.output.obsfile[..]`.

    Attributes:
        general (ObservationPointGeneral): `[General]` block with file metadata.
        observationpoint (List[ObservationPoint]): List of `[ObservationPoint]` blocks for all observation points.
    """

    general: ObservationPointGeneral = ObservationPointGeneral()
    observationpoint: List[ObservationPoint] = []

    _make_list = make_list_validator("observationpoint")

    @classmethod
    def _filename(cls) -> str:
        return "obsFile"
