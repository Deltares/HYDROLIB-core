"""util.py provides additional utility methods related to handling ini files.
"""
from enum import Enum
from operator import eq
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic.class_validators import root_validator, validator
from pydantic.fields import ModelField
from pydantic.main import BaseModel

from hydrolib.core.utils import operator_str, str_is_empty_or_none


def get_split_string_on_delimiter_validator(*field_name: str):
    """Get a validator to split strings passed to the specified field_name.

    Strings are split based on an automatically selected provided delimiter.
    The delimiter is the field's own delimiter, if that was defined using
    Field(.., delimiter=".."). Otherwise, the delimiter is the field's parent
    class's delimiter (which should be (subclass of) INIBasedModel.)
    The validator splits a string value into a list of substrings before any
    other validation takes place.

    Returns:
        the validator which splits strings on the provided delimiter.
    """

    def split(cls, v: Any, field: ModelField):
        if isinstance(v, str):
            v = v.split(cls.get_list_field_delimiter(field.name))
            v = [item.strip() for item in v if item != ""]
        return v

    return validator(*field_name, allow_reuse=True, pre=True)(split)


def get_enum_validator(*field_name: str, enum: Type[Enum]):
    """
    Get a case-insensitive enum validator that will returns the corresponding enum value.
    If the input is a list, then each list value is checked individually.

    Args:
        enum (Type[Enum]): The enum type for which to validate.
    """

    def get_enum(v):
        for entry in enum:
            if entry.lower() == v.lower():
                return entry
        return v

    return validator(*field_name, allow_reuse=True, pre=True, each_item=True)(get_enum)


def make_list_validator(*field_name: str):
    """Get a validator make a list of object if a single object is passed."""

    def split(v: Any):
        if not isinstance(v, list):
            v = [v]
        return v

    return validator(*field_name, allow_reuse=True, pre=True)(split)


def make_list_length_root_validator(
    *field_names,
    length_name: str,
    length_incr: int = 0,
    list_required_with_length: bool = False,
    min_length: int = 0,
):
    """
    Get a root_validator that checks the correct length (and presence) of several list fields in an object.

    Args:
        *field_names (str): names of the instance variables that are a list and need checking.
        length_name (str): name of the instance variable that stores the expected length.
        length_incr (int): Optional extra increment of length value (e.g., to have +1 extra value in lists).
        list_required_with_length (obj:`bool`, optional): Whether each list *must* be present if the length
            attribute is present (and > 0) in the input values. Default: False. If False, list length is only
            checked for the lists that are not None.
        min_length (int): minimum for list length value, overrides length_name value if that is smaller.
            For example, to require list length 1 when length value is given as 0.
    """

    def _get_incorrect_length_validation_message() -> str:
        """Make a string with a validation message, ready to be format()ed with
        field name and length name."""
        incrstring = f" + {length_incr}" if length_incr != 0 else ""
        minstring = f" (and at least {min_length})" if min_length > 0 else ""

        return (
            "Number of values for {} should be equal to the {} value"
            + incrstring
            + minstring
            + "."
        )

    def _validate_listfield_length(
        field_name: str, field: Optional[List[Any]], requiredlength: int
    ):
        """Validate the length of a single field, which should be a list."""

        if field is not None and len(field) != requiredlength:
            raise ValueError(
                _get_incorrect_length_validation_message().format(
                    field_name, length_name
                )
            )
        if field is None and list_required_with_length and requiredlength > 0:
            raise ValueError(
                f"List {field_name} cannot be missing if {length_name} is given."
            )

        return field

    def validate_correct_length(cls, values: dict):
        """The actual validator, will loop across all specified field names in outer function."""
        length = values.get(length_name)
        if length is None:
            # length attribute not present, possibly defer validation to a subclass.
            return values

        requiredlength = max(length + length_incr, min_length)

        for field_name in field_names:
            field = values.get(field_name)
            values[field_name] = _validate_listfield_length(
                field_name, field, requiredlength
            )

        return values

    return root_validator(allow_reuse=True)(validate_correct_length)


def get_forbidden_fields_validator(
    *field_names,
    conditional_field_name: str,
    conditional_value: Any,
    comparison_func: Callable[[Any, Any], bool] = eq,
):
    """
    Gets a validator that checks whether certain fields are *not* provided, if `conditional_field_name` is equal to `conditional_value`.
    The equality check can be overridden with another comparison operator function.

    Args:
        *field_names (str): Names of the instance variables that need to be validated.
        conditional_field_name (str): Name of the instance variable on which the fields are dependent.
        conditional_value (Any): Value that the conditional field should contain to perform this validation.
        comparison_func (Callable): binary operator function, used to override the default "eq" check for the conditional field value.
    """

    def validate_forbidden_fields(cls, values: dict):
        if (val := values.get(conditional_field_name)) is None or not comparison_func(
            val, conditional_value
        ):
            return values

        for field in field_names:
            if values.get(field) != None:
                raise ValueError(
                    f"{field} is forbidden when {conditional_field_name} {operator_str(comparison_func)} {conditional_value}"
                )

        return values

    return root_validator(allow_reuse=True)(validate_forbidden_fields)


def get_required_fields_validator(
    *field_names,
    conditional_field_name: str,
    conditional_value: Any,
    comparison_func: Callable[[Any, Any], bool] = eq,
):
    """
    Gets a validator that checks whether the fields are provided, if `conditional_field_name` is equal to `conditional_value`.
    The equality check can be overridden with another comparison operator function.

    Args:
        *field_names (str): Names of the instance variables that need to be validated.
        conditional_field_name (str): Name of the instance variable on which the fields are dependent.
        conditional_value (Any): Value that the conditional field should contain to perform this validation.
        comparison_func (Callable): binary operator function, used to override the default "eq" check for the conditional field value.
    """

    def validate_required_fields(cls, values: dict):
        if (val := values.get(conditional_field_name)) is None or not comparison_func(
            val, conditional_value
        ):
            return values

        for field in field_names:
            if values.get(field) == None:
                raise ValueError(
                    f"{field} should be provided when {conditional_field_name} {operator_str(comparison_func)} {conditional_value}"
                )

        return values

    return root_validator(allow_reuse=True)(validate_required_fields)


def get_conditional_root_validator(
    root_vldt: classmethod,
    conditional_field_name: str,
    conditional_value: Any,
    comparison_func: Callable[[Any, Any], bool] = eq,
):
    """
    Gets a validator that checks whether certain fields are *not* provided, if `conditional_field_name` is equal to `conditional_value`.
    The equality check can be overridden with another comparison operator function.

    Args:
        root_vldt (classmethod): A root validator that is to be called *if* the condition is satisfied.
        conditional_field_name (str): Name of the instance variable that determines whether the root validator must be called or not.
        conditional_value (Any): Value that the conditional field should be compared with to perform this validation.
        comparison_func (Callable): binary operator function, used to override the default "eq" check for the conditional field value.
    """

    def validate_conditionally(cls, values: dict):
        if (val := values.get(conditional_field_name)) is not None and comparison_func(
            val, conditional_value
        ):
            # Condition is met: call the actual root validator, passing on the attribute values.
            root_vldt.__func__(cls, values)

        return values

    return root_validator(allow_reuse=True)(validate_conditionally)


def get_from_subclass_defaults(cls: Type[BaseModel], fieldname: str, value: str):
    """Gets a value that corresponds with the default field value of one of the subclasses.

    Args:
        cls (Type[BaseModel]): The parent model type.
        fieldname (str): The field name for which retrieve the default for.
        value (str): The value to compare with.

    Returns:
        [type]: The field default that corresponds to the value.
    """
    for c in cls.__subclasses__():
        default = c.__fields__.get(fieldname).default
        if default.lower() == value.lower():
            return default

    return value


def get_location_specification_rootvalidator(
    allow_nodeid: bool = True,
    numfield_name: str = "numCoordinates",
    xfield_name: str = "xCoordinates",
    yfield_name: str = "yCoordinates",
):
    """
    Get a root validator that checks for correct location specification in
    typical 1D2D input in an IniBasedModel class.

    It checks for presence of at least one of: nodeId (if allowed),
    branchId+chainage or num/x/yCoordinates.
    Also, completeness of the given location is checked (e.g., no chainage
    missing when branchId given), as well as the locationType.

    Args:
        allow_nodeid (bool): Allow nodeId in input. Defaults to True.
        numfield_name (str): Field name (in input file) for the coordinates
            count. Will be lowercased in values dict. Use None when this
            class has no count field at all. Defaults to "numCoordinates".
        xfield_name (str): Field name (in input file) for the x coordinates.
            Will be lowercased in values dict. Defaults to "xCoordinates".
        yfield_name (str): Field name (in input file) for the y coordinates.
            Will be lowercased in values dict. Defaults to "yCoordinates".

    """

    def validate_location_specification(cls, values: Dict) -> Dict:
        """
        Verify whether the location given for this object matches the expectations.

        Args:
            values (Dict): Dictionary of object's validated fields.

        Raises:
            ValueError: When neither nodeid, branchid or coordinates have been given.
            ValueError: When either x or y coordinates were expected but not given.
            ValueError: When locationtype should be 1d but other was specified.

        Returns:
            Dict: Validated dictionary of input class fields.
        """

        def validate_coordinates(coord_name: str) -> None:
            if values.get(coord_name.lower(), None) is None:
                raise ValueError("{} should be given.".format(coord_name))

        # If nodeid or branchid and Chainage are present
        node_id: str = values.get("nodeid", None)
        branch_id: str = values.get("branchid", None)
        n_coords: int = (
            values.get(numfield_name.lower(), 0)
            if not str_is_empty_or_none(numfield_name)
            else None
        )

        chainage: float = values.get("chainage", None)

        # First validation - at least one of the following should be specified.
        if str_is_empty_or_none(node_id) and (str_is_empty_or_none(branch_id)):
            if n_coords == 0:
                raise ValueError(
                    f"Either {'nodeId, ' if allow_nodeid else ''}branchId (with chainage) or {numfield_name + ' with ' if numfield_name else ''}{xfield_name} and {yfield_name} are required."
                )
            else:
                # Validation: when ids are absent, coordinates should be valid.
                validate_coordinates(xfield_name)
                validate_coordinates(yfield_name)
            return values
        else:
            # Validation: nodeId only when it is allowed
            if not str_is_empty_or_none(node_id) and not allow_nodeid:
                raise ValueError(f"nodeId is not allowed for {cls.__name__} objects")
            # Validation: chainage should be given with branchid
            if not str_is_empty_or_none(branch_id) and chainage is None:
                raise ValueError(
                    "Chainage should be provided when branchId is specified."
                )
            # Validation: when nodeid, or branchid specified, expected 1d.
            location_type = values.get("locationtype", None)
            if str_is_empty_or_none(location_type):
                values["locationtype"] = "1d"
            elif location_type.lower() != "1d":
                raise ValueError(
                    "locationType should be 1d when nodeId (or branchId and chainage) is specified."
                )

        return values

    return root_validator(allow_reuse=True)(validate_location_specification)


def get_number_of_coordinates_validator(
    numfield_name: str = "numCoordinates",
    xfield_name: str = "xCoordinates",
    yfield_name: str = "yCoordinates",
    minimum_required_number_of_coordinates: int = 0,
):
    """
    Get a validator that validates whether the given coordinates match in number
    to the expected value given by numCoordinates and that numCoordinates is
    greater than or equal to the minimum required number of coordinates.

    Args:
        numfield_name (str, optional): Field name (in input file) for the coordinates
            count. Will be lowercased in values dict. Defaults to "numCoordinates".
        xfield_name (str, optional): Field name (in input file) for the x coordinates.
            Will be lowercased in values dict. Defaults to "xCoordinates".
        yfield_name (str, optional): Field name (in input file) for the y coordinates.
            Will be lowercased in values dict. Defaults to "yCoordinates".
        minimum_required_number_of_coordinates (int, optional): Minimum number of
            coordinates required in order to validate. Defaults to 0.
    """

    def validate_number_of_coordinates(cls, values: Dict) -> Dict:
        """
        Validates whether the given coordinates match in number to the
        expected value given for numCoordinates and is greater than or
        equal to the minimum required number of coordinates.

        Args:
            values (Dict): Dictionary of object's validated fields.

        Raises:
            ValueError: When the number of coordinates is not specified but the coordinates are.
            ValueError: When the number of coordinates is provided but the x-coordinates or
                y-coordinates are not.
            ValueError: When the number of x-coordinates or the number of y-coordinates
                does not match the number of coordinates.
            ValueError: When the number of x-coordinates or the number of y-coordinates
                is less than the number of required coordinates.

        Returns:
            Dict: Validated dictionary of input class fields.
        """

        def get_value(field_name: str) -> Any:
            return (
                values.get(field_name.lower(), None)
                if not str_is_empty_or_none(field_name)
                else None
            )

        def all_values_are_none() -> bool:
            return (
                number_of_coordinates is None
                and xcoordinates is None
                and ycoordinates is None
            )

        def some_values_are_none() -> bool:
            return (
                number_of_coordinates is None
                or xcoordinates is None
                or ycoordinates is None
            )

        def validate_x_and_ycoordinate_number() -> None:
            number_of_xcoordinates = len(xcoordinates)
            number_of_ycoordinates = len(ycoordinates)

            if (
                number_of_xcoordinates != number_of_coordinates
                or number_of_ycoordinates != number_of_coordinates
                or number_of_xcoordinates < minimum_required_number_of_coordinates
            ):
                raise ValueError(
                    f"Number of x-coordinates and y-coordinates should match number of"
                    "coordinates and should be atleast {minimum_required_number_of_coordinates}."
                )

        number_of_coordinates = get_value(numfield_name)
        xcoordinates = get_value(xfield_name)
        ycoordinates = get_value(yfield_name)

        if all_values_are_none():
            return values

        if some_values_are_none():
            raise ValueError(
                f"When using coordinates, the fields {numfield_name}, {xfield_name} and {yfield_name} should be given."
            )

        validate_x_and_ycoordinate_number()

        return values

    return root_validator(allow_reuse=True)(validate_number_of_coordinates)
