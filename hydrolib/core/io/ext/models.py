from pathlib import Path
from typing import Dict, List, Literal, Optional

from pydantic import Field, root_validator, validator

from hydrolib.core.io.bc.models import ForcingBase, ForcingModel
from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.serializer import SerializerConfig, write_ini
from hydrolib.core.io.ini.util import (
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

    _header: Literal["Boundary"] = "Boundary"
    quantity: str = Field(alias="quantity")
    nodeid: Optional[str] = Field(alias="nodeId")
    locationfile: Optional[Path] = Field(alias="locationFile")
    forcingfile: ForcingModel = Field(alias="forcingFile")
    bndwidth1d: Optional[float] = Field(alias="bndWidth1D")
    bndbldepth: Optional[float] = Field(alias="bndBlDepth")

    def is_intermediate_link(self) -> bool:
        return True

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
        if str_is_empty_or_none(node_id) and not isinstance(location_file, Path):
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
    discharge: str = Field(alias="discharge")

    _split_to_list = get_split_string_on_delimiter_validator(
        "xcoordinates", "ycoordinates"
    )

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("id") or data.get("name")

    @validator("xcoordinates", "ycoordinates")
    @classmethod
    def validate_coordinates(cls, field_value: List[int], values: Dict) -> List[int]:
        """
        Method to validate whether the given coordinates match in number
        to the expected value given for numcoordinates.

        Args:
            field_value (List[int]): Coordinates list (x or y)
            values (Dict): Properties already 'validated' for Lateral class.

        Raises:
            ValueError: When the number of coordinates does not match expectations.

        Returns:
            List[int]: Validated list of coordinates.
        """
        num_coords = values.get("numcoordinates", None)
        if num_coords is None:
            raise ValueError(
                "numCoordinates should be given when providing xCoordinates or yCoordinates."
            )
        assert num_coords == len(
            field_value
        ), "Number of coordinates given ({}) not matching the numCoordinates value {}.".format(
            len(field_value), num_coords
        )
        return field_value

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

    @root_validator
    @classmethod
    def validate_location_dependencies(cls, values: Dict) -> Dict:
        """
        Once all the fields have been evaluated, we verify whether the location
        given for this Lateral matches the expectations.

        Args:
            values (Dict): Dictionary of Laterals validated fields.

        Raises:
            ValueError: When neither nodeid, branchid or coordinates have been given.
            ValueError: When either x or y coordinates were expected but not given.
            ValueError: When locationtype should be 1d but other was specified.

        Returns:
            Dict: Validated dictionary of Lateral fields.
        """

        def validate_coordinates(coord_name: str) -> None:
            if values.get(coord_name.lower(), None) is None:
                raise ValueError("{} should be given.".format(coord_name))

        # If nodeid or branchid and Chainage are present
        node_id: str = values.get("nodeid", None)
        branch_id: str = values.get("branchid", None)
        n_coords: int = values.get("numcoordinates", 0)
        chainage: float = values.get("chainage", None)

        # First validation - at least one of the following should be specified.
        if str_is_empty_or_none(node_id) and (str_is_empty_or_none(branch_id)):
            if n_coords == 0:
                raise ValueError(
                    "Either nodeId, branchId (with chainage) or numCoordinates (with xCoordinates and yCoordinates) are required."
                )
            else:
                # Second validation, coordinates should be valid.
                validate_coordinates("xCoordinates")
                validate_coordinates("yCoordinates")
            return values
        else:
            # Third validation, chainage should be given with branchid
            if not str_is_empty_or_none(branch_id) and chainage is None:
                raise ValueError(
                    "Chainage should be provided when branchId is specified."
                )
            # Fourth validation, when nodeid, or branchid specified, expected 1d.
            location_type = values.get("locationtype", None)
            if str_is_empty_or_none(location_type):
                values["locationtype"] = "1d"
            elif location_type.lower() != "1d":
                raise ValueError(
                    "LocationType should be 1d when nodeId (or branchId and chainage) is specified."
                )

        return values


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
