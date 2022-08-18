from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

from pydantic import Field, root_validator, validator

from hydrolib.core.basemodel import (
    DiskOnlyFileModel,
    validator_set_default_disk_only_file_model_when_none,
)
from hydrolib.core.io.bc.models import ForcingBase, ForcingData, ForcingModel
from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.serializer import SerializerConfig, write_ini
from hydrolib.core.io.ini.util import (
    get_location_specification_rootvalidator,
    get_number_of_coordinates_validator,
    get_split_string_on_delimiter_validator,
    make_list_validator,
)
from hydrolib.core.utils import str_is_empty_or_none


class Boundary(INIBasedModel):
    """
    A `[Boundary]` block for use inside an external forcings file,
    i.e., a [ExtModel][hydrolib.core.io.ext.models.ExtModel].

    All lowercased attributes match with the boundary input as described in
    [UM Sec.C.5.2.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.1).
    """

    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    _header: Literal["Boundary"] = "Boundary"
    quantity: str = Field(alias="quantity")
    nodeid: Optional[str] = Field(alias="nodeId")
    locationfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="locationFile"
    )
    forcingfile: ForcingModel = Field(alias="forcingFile")
    bndwidth1d: Optional[float] = Field(alias="bndWidth1D")
    bndbldepth: Optional[float] = Field(alias="bndBlDepth")

    def is_intermediate_link(self) -> bool:
        return True

    @classmethod
    def _is_valid_locationfile_data(
        cls, elem: Union[None, str, Path, DiskOnlyFileModel]
    ) -> bool:
        return isinstance(elem, Path) or (
            isinstance(elem, DiskOnlyFileModel) and elem.filepath is not None
        )

    @root_validator
    @classmethod
    def check_nodeid_or_locationfile_present(cls, values: Dict):
        """
        Verifies that either nodeid or locationfile properties have been set.

        Args:
            values (Dict): Dictionary with values already validated.

        Raises:
            ValueError: When none of the values are present.

        Returns:
            Dict: Validated dictionary of values for Boundary.
        """
        node_id = values.get("nodeid", None)
        location_file = values.get("locationfile", None)
        if str_is_empty_or_none(node_id) and not cls._is_valid_locationfile_data(
            location_file
        ):
            raise ValueError(
                "Either nodeId or locationFile fields should be specified."
            )
        return values

    def _get_identifier(self, data: dict) -> Optional[str]:
        """
        Retrieves the identifier for a boundary, which is the nodeid

        Args:
            data (dict): Dictionary of values for this boundary.

        Returns:
            str: The nodeid value or None if not found.
        """
        return data.get("nodeid")

    @property
    def forcing(self) -> ForcingBase:
        """Retrieves the corresponding forcing data for this boundary.

        Returns:
            ForcingBase: The corresponding forcing data. None when this boundary does not have a forcing file or when the data cannot be found.
        """

        if self.forcingfile is None:
            return None

        for forcing in self.forcingfile.forcing:

            if self.nodeid != forcing.name:
                continue

            for quantity in forcing.quantityunitpair:
                if quantity.quantity.startswith(self.quantity):
                    return forcing

        return None


class Lateral(INIBasedModel):
    """
    A `[Lateral]` block for use inside an external forcings file,
    i.e., a [ExtModel][hydrolib.core.io.ext.models.ExtModel].

    All lowercased attributes match with the lateral input as described in
    [UM Sec.C.5.2.2](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.2).
    """

    _header: Literal["Lateral"] = "Lateral"
    id: str = Field(alias="id")
    name: str = Field("", alias="name")
    locationtype: Optional[str] = Field(alias="locationType")
    nodeid: Optional[str] = Field(alias="nodeId")
    branchid: Optional[str] = Field(alias="branchId")
    chainage: Optional[float] = Field(alias="chainage")
    numcoordinates: Optional[int] = Field(alias="numCoordinates")
    xcoordinates: Optional[List[int]] = Field(alias="xCoordinates")
    ycoordinates: Optional[List[int]] = Field(alias="yCoordinates")
    discharge: ForcingData = Field(alias="discharge")

    def is_intermediate_link(self) -> bool:
        return True

    _split_to_list = get_split_string_on_delimiter_validator(
        "xcoordinates", "ycoordinates"
    )

    _location_validator = get_location_specification_rootvalidator(allow_nodeid=True)
    _number_of_coordinates_validator = get_number_of_coordinates_validator(
        minimum_required_number_of_coordinates=1
    )

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("id") or data.get("name")

    @validator("locationtype")
    @classmethod
    def validate_location_type(cls, v: str) -> str:
        """
        Method to validate whether the specified location type is correct.

        Args:
            v (str): Given value for the locationtype field.

        Raises:
            ValueError: When the value given for locationtype is unknown.

        Returns:
            str: Validated locationtype string.
        """
        possible_values = ["1d", "2d", "all"]
        if v.lower() not in possible_values:
            raise ValueError(
                "Value given ({}) not accepted, should be one of: {}".format(
                    v, ", ".join(possible_values)
                )
            )
        return v


class ExtGeneral(INIGeneral):
    """The external forcing file's `[General]` section with file meta data."""

    _header: Literal["General"] = "General"
    fileversion: str = Field("2.01", alias="fileVersion")
    filetype: Literal["extForce"] = Field("extForce", alias="fileType")


class ExtModel(INIModel):
    """
    The overall external forcings model that contains the contents of one external forcings file (new format).

    This model is typically referenced under a [FMModel][hydrolib.core.io.mdu.models.FMModel]`.external_forcing.extforcefilenew`.

    Attributes:
        general (ExtGeneral): `[General]` block with file metadata.
        boundary (List[Boundary]): List of `[Boundary]` blocks for all boundary conditions.
        lateral List[Lateral]): List of `[Lateral]` blocks for all lateral discharges.
    """

    general: ExtGeneral = ExtGeneral()
    boundary: List[Boundary] = []
    lateral: List[Lateral] = []

    _split_to_list = make_list_validator("boundary", "lateral")

    @classmethod
    def _ext(cls) -> str:
        return ".ext"

    @classmethod
    def _filename(cls) -> str:
        return "bnd"

    def _serialize(self, _: dict) -> None:
        # We skip the passed dict for a better one.
        config = SerializerConfig(section_indent=0, property_indent=0)
        write_ini(self._resolved_filepath, self._to_document(), config=config)
