from typing import Dict, List, Literal, Optional

from pydantic import Field, validator
from pydantic.class_validators import root_validator

from hydrolib.core.io.bc.models import ForcingBase, ForcingModel
from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.serializer import SerializerConfig, write_ini
from hydrolib.core.io.ini.util import (
    get_split_string_on_delimiter_validator,
    make_list_validator,
)
from hydrolib.core.utils import str_is_empty_or_none


class Boundary(INIBasedModel):
    _header: Literal["Boundary"] = "Boundary"
    quantity: str
    nodeId: Optional[str]
    forcingfile: Optional[ForcingModel] = None
    bndWidth1D: Optional[float]

    def is_intermediate_link(self) -> bool:
        return True

    def _get_identifier(self, data: dict) -> str:
        return data["nodeid"] if "nodeid" in data else None

    @property
    def forcing(self) -> ForcingBase:
        """Retrieves the corresponding forcing data for this boundary.

        Returns:
            ForcingBase: The corresponding forcing data. None when this boundary does not have a forcing file or when the data cannot be found.
        """

        if self.forcingfile is None:
            return None

        for forcing in self.forcingfile.forcing:

            if self.nodeId != forcing.name:
                continue

            for quantity in forcing.quantity:
                if quantity.startswith(self.quantity):
                    return forcing

        return None


class Lateral(INIBasedModel):
    _header: Literal["Lateral"] = "Lateral"
    id: str
    name: str = ""
    locationType: Optional[str]
    nodeId: Optional[str]
    branchId: Optional[str]
    chainage: Optional[float]
    numCoordinates: Optional[int]
    xCoordinates: Optional[List[int]]
    yCoordinates: Optional[List[int]]
    discharge: str

    _split_to_list = get_split_string_on_delimiter_validator(
        "xCoordinates", "yCoordinates"
    )

    def _get_identifier(self, data: dict) -> str:
        return data["id"] if "id" in data else None

    @validator("xCoordinates", "yCoordinates")
    @classmethod
    def validate_coordinates(cls, field_value: List[int], values: Dict) -> List[int]:
        """
        Method to validate whether the given coordinates match in number
        to the expected value given for numCoordinates.

        Args:
            field_value (List[int]): Coordinates list (x or y)
            values (Dict): Properties already 'validated' for Lateral class.

        Raises:
            ValueError: When the number of coordinates does not match expectations.

        Returns:
            List[int]: Validated list of coordinates.
        """
        num_coords = values.get("numCoordinates", None)
        if num_coords is None:
            raise ValueError(
                "numCoordinates should be given when providing x or y coordinates."
            )
        assert num_coords == len(
            field_value
        ), "Number of coordinates given ({}) not matching the numCoordinates value {}.".format(
            len(field_value), num_coords
        )
        return field_value

    @validator("locationType")
    @classmethod
    def validate_location_type(cls, v: str) -> str:
        """
        Method to validate whether the specified location type is correct.

        Args:
            v (str): Given value for the locationType field.

        Raises:
            ValueError: When the value given for locationType is unknown.

        Returns:
            str: Validated locationType string.
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
            ValueError: When neither nodeId, branchId or coordinates have been given.
            ValueError: When either x or y coordinates were expected but not given.
            ValueError: When locationType should be 1d but other was specified.

        Returns:
            Dict: Validated dictionary of Lateral fields.
        """

        def validate_coordinates(coord_name: str) -> None:
            if values.get(coord_name, None) is None:
                raise ValueError("{} should be given.".format(coord_name))

        # If nodeId or branchId and Chainage are present
        node_id: str = values.get("nodeId", None)
        branch_id: str = values.get("branchId", None)
        n_coords: int = values.get("numCoordinates", 0)
        chainage: float = values.get("chainage", None)

        # First validation - at least one of the following should be specified.
        if str_is_empty_or_none(node_id) and (str_is_empty_or_none(branch_id)):
            if n_coords == 0:
                raise ValueError(
                    "Either nodeId, branchId (with chainage) or numCoordinates (with x, y coordinates) are required."
                )
            else:
                # Second validation, coordinates should be valid.
                validate_coordinates("xCoordinates")
                validate_coordinates("yCoordinates")
            return values
        else:
            # Third validation, chainage should be given with branchId
            if not str_is_empty_or_none(branch_id) and chainage is None:
                raise ValueError("Chainage should be provided when branchId specified.")
            # Fourth validation, when nodeId, or branchId specified, expected 1d.
            location_type = values.get("locationType", None)
            if str_is_empty_or_none(location_type):
                values["locationType"] = "1d"
            elif location_type.lower() != "1d":
                raise ValueError(
                    "LocationType should be 1d when nodeId (or branchId and chainage) specified."
                )

        return values


class ExtGeneral(INIGeneral):
    _header: Literal["General"] = "General"
    fileVersion: str = "2.01"
    fileType: Literal["extForce"] = "extForce"


class ExtModel(INIModel):
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
        write_ini(self.filepath, self._to_document(), config=config)
