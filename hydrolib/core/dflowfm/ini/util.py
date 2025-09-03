"""util.py provides additional utility methods related to handling ini files.
"""

from datetime import datetime
from enum import Enum
from operator import eq
from typing import Any, Callable, Dict, List, Optional, Set, Type

from pydantic import BaseModel, ValidationInfo
from pydantic.fields import FieldInfo

from hydrolib.core.base.utils import operator_str, str_is_empty_or_none, to_list
from hydrolib.core.dflowfm.common.models import LocationType


def split_string_on_delimiter(cls, v: Any, field: ValidationInfo):
    """Split a string on the list field delimiter, and return a list of strings.

    If the input is a string, it is split on the delimiter defined in the class.
    If the input is anything else, it is returned as is.

    Args:
        cls (Type[BaseModel]): The class that contains the field.
        v (Any): The value to split.
        field (ValidationInfo): The field information.

    Returns:
        List[str] or Any: A list of strings if the input was a string, otherwise
            the input value as is.
    """
    if isinstance(v, str):
        v = v.split(cls.get_list_field_delimiter(field.field_name))
        v = [item.strip() for item in v if item != ""]
    return v


def enum_value_parser(
    v,
    enum: Type[Enum],
    alternative_enum_values: Optional[Dict[str, List[str]]] = None,
):
    """Return a function that converts strings (and string lists) to Enum values.

    Args:
        enum (Type[Enum]): The Enum type to parse values into.
        alternative_enum_values (Optional[Dict[str, List[str]]]): A dictionary mapping enum values
            to alternative string representations. If provided, the parser will also accept these
            alternative strings as valid inputs for the corresponding enum values.

    Returns:
        Callable: A function that takes a value (or list of values) and returns the corresponding
            Enum value or raises a ValueError if the value is invalid.

    Raises:
        ValueError: If the input value is not a valid Enum value or does not match any
            alternative string representations.
    """
    if isinstance(v, list):
        result = [parse_enum(item, enum, alternative_enum_values) for item in v]
    else:
        result = parse_enum(v, enum, alternative_enum_values)
    return result


def parse_enum(
    v, enum: Type[Enum], alternative_enum_values: Optional[Dict[str, List[str]]] = None
):
    result = None

    if isinstance(v, enum):
        result = v
    elif isinstance(v, str):
        v_lower = v.lower()
        for entry in enum:
            if entry.value.lower() == v_lower:
                result = entry
                break
            if (
                alternative_enum_values
                and (alts := alternative_enum_values.get(entry.value))
                and any(v_lower == alt.lower() for alt in alts)
            ):
                result = entry
                break
    if result is None:
        valid_values = [e.value for e in enum]
        raise ValueError(f"Invalid enum value: {v!r}. Expected one of: {valid_values}")
    return result


def ensure_list(v: Any):
    """Ensure that the input is a list.

    Args:
        v (Any): The value to ensure is a list.

    Returns:
        List[Any]: A list containing the input value if it was a dictionary,
            or the input value itself if it was already a list.

    Raises:
        TypeError: If the input is not a list or a dictionary.
    """
    if isinstance(v, dict):
        v = [v]
    if not isinstance(v, list):
        raise TypeError("Expected a list or a single dictionary")
    return v


def make_list(v: Any):
    if not isinstance(v, list):
        v = [v]
    return v


def validate_correct_length(
    values: Dict,
    *field_names,
    length_name: str,
    length_incr: int = 0,
    list_required_with_length: bool = False,
    min_length: int = 0,
):
    """
    Validate the correct length (and presence) of several list fields in an object.

    Args:
        values (Dict):
            dictionary of values to validate.
        *field_names (str):
            names of the instance variables that are a list and need checking.
        length_name (str):
            name of the instance variable that stores the expected length.
        length_incr (int):
            Optional extra increment of length value (e.g., to have +1 extra value in lists).
        list_required_with_length (obj:`bool`, optional):
            Whether each list *must* be present if the length attribute is present (and > 0) in the input values.
            Default: False. If False, list length is only checked for the lists that are not None.
        min_length (int):
            minimum for list length value, overrides length_name value if that is smaller. For example, to require
            list length 1 when length value is given as 0.

    Raises:
        ValueError:
            When the number of values for any of the given field_names is not as expected.

    Returns:
        Dict:
            Dictionary of validated values.
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

    length = values.get(length_name)
    if length is None:
        # length attribute not present, possibly defer validation to a subclass.
        return values

    requiredlength = max(int(length) + length_incr, min_length)

    for field_name in field_names:
        field = values.get(field_name)
        _validate_listfield_length(field_name, field, requiredlength)


def validate_forbidden_fields(
    values: Dict,
    *field_names,
    conditional_field_name: str,
    conditional_value: Any,
    comparison_func: Callable[[Any, Any], bool] = eq,
) -> Dict:
    """
    Validates whether certain fields are *not* provided, if `conditional_field_name` is equal to `conditional_value`.
    The equality check can be overridden with another comparison operator function.

    Args:
        values (Dict): Dictionary of input class fields.
        *field_names (str): Names of the instance variables that need to be validated.
        conditional_field_name (str): Name of the instance variable on which the fields are dependent.
        conditional_value (Any): Value that the conditional field should contain to perform this validation.
        comparison_func (Callable): binary operator function, used to override the default "eq" check for the conditional field value.

    Raises:
        ValueError: When a forbidden field is provided.

    Returns:
        Dict: Validated dictionary of input class fields.
    """
    if (val := values.get(conditional_field_name)) is None or not comparison_func(
        val, conditional_value
    ):
        return values

    for field in field_names:
        if values.get(field) is not None:
            raise ValueError(
                f"{field} is forbidden when {conditional_field_name} {operator_str(comparison_func)} {conditional_value}"
            )

    return values


def validate_required_fields(
    values: Dict,
    *field_names,
    conditional_field_name: str,
    conditional_value: Any,
    comparison_func: Callable[[Any, Any], bool] = eq,
):
    """
    Validates whether the specified fields are provided, if `conditional_field_name` is equal to `conditional_value`.
    The equality check can be overridden with another comparison operator function.

    Args:
        values (Dict): Dictionary of input class fields.
        *field_names (str): Names of the instance variables that need to be validated.
        conditional_field_name (str): Name of the instance variable on which the fields are dependent.
        conditional_value (Any): Value that the conditional field should contain to perform this validation.
        comparison_func (Callable): binary operator function, used to override the default "eq" check for the conditional field value.

    Raises:
        ValueError: When a required field is not provided under the given conditions.

    Returns:
        Dict: Validated dictionary of input class fields.
    """

    if (val := values.get(conditional_field_name)) is None or not comparison_func(
        val, conditional_value
    ):
        return values

    for field in field_names:
        if values.get(field) is None:
            raise ValueError(
                f"{field} should be provided when {conditional_field_name} {operator_str(comparison_func)} {conditional_value}"
            )


def validate_conditionally(
    values: Dict,
    root_vldt: classmethod,
    conditional_field_name: str,
    conditional_value: Any,
    comparison_func: Callable[[Any, Any], bool] = eq,
) -> Dict:
    """
    Validate whether certain fields are *not* provided, if `conditional_field_name` is equal to `conditional_value`.
    The equality check can be overridden with another comparison operator function.

    Args:
        values (Dict):
            Dictionary of input class fields.
        root_vldt (classmethod):
            A root validator that is to be called *if* the condition is satisfied.
        conditional_field_name (str):
            Name of the instance variable that determines whether the root validator must be called or not.
        conditional_value (Any):
            Value that the conditional field should be compared with to perform this validation.
        comparison_func (Callable):
            Binary operator function, used to override the default "eq" check for the conditional field value.

    Returns:
        Dict:
            Validated dictionary of input class fields.
    """
    if (val := values.get(conditional_field_name)) is not None and comparison_func(
        val, conditional_value
    ):
        # Condition is met: call the actual root validator, passing on the attribute values.
        root_vldt(values)


def validate_datetime_string(
    field_value: Optional[str], field: ValidationInfo
) -> Optional[str]:
    """Validate that a field value matches the YYYYmmddHHMMSS datetime format.

    Args:
        field_value (Optional[str]): value of a Pydantic field, may be optional.
        field (ModelField): the underlying Pydantic ModelField, used in error
            message.

    Returns:
        Optional[str]: the original input value, if valid.

    Raises:
        ValueError: if a non-empty input string does not have valid format.
    """
    if (
        field_value is not None
        and len(field_value.strip()) > 0
        and field_value != "yyyymmddhhmmss"
    ):
        try:
            _ = datetime.strptime(field_value, r"%Y%m%d%H%M%S")
        except ValueError:
            raise ValueError(
                f"Invalid datetime string for {field.field_name}: '{field_value}', expecting 'YYYYmmddHHMMSS'."
            )

    return field_value  # this is the value written to the class field


def get_from_subclass_defaults(cls: Type[BaseModel], fieldname: str, value: str) -> str:
    """
    Gets a value that corresponds with the default field value of one of the subclasses.
    If the subclass doesn't have the specified field, it will look into its own subclasses
    recursively for the specified fieldname.

    Args:
        cls (Type[BaseModel]): The parent model type.
        fieldname (str): The field name for which retrieve the default for.
        value (str): The value to compare with.

    Returns:
        str: The field default that corresponds to the value. If nothing is found return the input value.
    """
    # Immediately check in direct subclasses, not in base cls itself:
    for c in cls.__subclasses__():
        default = _try_get_default_value(c, fieldname, value)
        if default is not None:
            return default

    # No matching default was found, return input value:
    return value


def _try_get_default_value(
    c: Type[BaseModel], fieldname: str, value: str
) -> Optional[str]:
    """Helper subroutine to get the default value for a particular field in
    the given class or any of its descendant classes, if it matches the input
    value (case insensitive).

    This method recurses depth-first topdown into the class'es subclasses.

        c (Type[BaseModel]): The base model type where the search starts.
        fieldname (str): The field name for which retrieve the default for.
        value (str): The value to compare with.

    Returns:
        Optional[str]: The field default that corresponds to the value. If nothing is found return None.
    """
    stack = [c]
    result = None
    while stack:
        current_class = stack.pop()
        if not hasattr(current_class, "model_fields"):
            continue
        field = current_class.model_fields.get(fieldname)
        if field is not None:
            # In pydantic v2, default is accessed through default_factory or directly
            if hasattr(field, "default_factory") and field.default_factory is not None:
                default = field.default_factory()
            else:
                default = field.default

            if (
                default is not None
                and hasattr(default, "lower")
                and default.lower() == value.lower()
            ):
                result = default
                break
        # Add subclasses to stack for further checking
        stack.extend(current_class.__subclasses__())
    return result


class LocationValidationConfiguration(BaseModel):
    """Class that holds the various configuration settings needed for location validation."""

    validate_node: bool = True
    """bool, optional: Whether or not node location specification should be validated. Defaults to True."""

    validate_coordinates: bool = True
    """bool, optional: Whether or not coordinate location specification should be validated. Defaults to True."""

    validate_branch: bool = True
    """bool, optional: Whether or not branch location specification should be validated. Defaults to True."""

    validate_num_coordinates: bool = True
    """bool, optional: Whether or not the number of coordinates should be validated or not. This option is only relevant when `validate_coordinates` is True. Defaults to True."""

    validate_location_type: bool = True
    """bool, optional: Whether or not the location type should be validated. Defaults to True."""

    minimum_num_coordinates: int = 0
    """int, optional: The minimum required number of coordinates. This option is only relevant when `validate_coordinates` is True. Defaults to 0."""


class LocationValidationFieldNames(BaseModel):
    """Class that holds the various field names needed for location validation."""

    node_id: str = "nodeId"
    """str, optional: The node id field name. Defaults to `nodeId`."""

    branch_id: str = "branchId"
    """str, optional: The branch id field name. Defaults to `branchId`."""

    chainage: str = "chainage"
    """str, optional: The chainage field name. Defaults to `chainage`."""

    x_coordinates: str = "xCoordinates"
    """str, optional: The x-coordinates field name. Defaults to `xCoordinates`."""

    y_coordinates: str = "yCoordinates"
    """str, optional: The y-coordinates field name. Defaults to `yCoordinates`."""

    num_coordinates: str = "numCoordinates"
    """str, optional: The number of coordinates field name. Defaults to `numCoordinates`."""

    location_type: str = "locationType"
    """str, optional: The location type field name. Defaults to `locationType`."""


def validate_location_specification(
    values: Dict,
    config: Optional[LocationValidationConfiguration] = None,
    fields: Optional[LocationValidationFieldNames] = None,
) -> Dict:
    """
    Validates whether the correct location specification is given in
    typical 1D2D input in an IniBasedModel class.

    Validates for presence of at least one of: nodeId, branchId with chainage,
    xCoordinates with yCoordinates, or xCoordinates with yCoordinates and numCoordinates.
    Validates for the locationType for nodeId and branchId.

    Args:
        values (Dict):
            Dictionary of object's validated fields.
        config (LocationValidationConfiguration, optional):
            Configuration for the location validation. Default is None.
        fields (LocationValidationFieldNames, optional):
            Fields names that should be used for the location validation. Default is None.

    Raises:
        ValueError: When exactly one of the following combinations were not given:
            - nodeId
            - branchId with chainage
            - xCoordinates with yCoordinates
            - xCoordinates with yCoordinates and numCoordinates.
        ValueError: When numCoordinates does not meet the requirement minimum amount or does not match the amount of xCoordinates or yCoordinates.
        ValueError: When locationType should be 1d but other was specified.

    Returns:
        Dict: Validated dictionary of input class fields.
    """

    if config is None:
        config = LocationValidationConfiguration()

    if fields is None:
        fields = LocationValidationFieldNames()

    has_node_id = not str_is_empty_or_none(values.get(fields.node_id.lower()))
    has_branch_id = not str_is_empty_or_none(values.get(fields.branch_id.lower()))
    has_chainage = values.get(fields.chainage.lower()) is not None
    has_x_coordinates = values.get(fields.x_coordinates.lower()) is not None
    has_y_coordinates = values.get(fields.y_coordinates.lower()) is not None
    has_num_coordinates = values.get(fields.num_coordinates.lower()) is not None

    # ----- Local validation functions
    def get_length(field: str):
        value = values[field.lower()]
        return len(to_list(value))

    def validate_location_type(expected_location_type: LocationType) -> None:
        location_type = values.get(fields.location_type.lower(), None)
        if str_is_empty_or_none(location_type):
            values[fields.location_type.lower()] = expected_location_type
        elif location_type != expected_location_type:
            raise ValueError(
                f"{fields.location_type} should be {expected_location_type} but was {location_type}"
            )

    def validate_coordinates_with_num_coordinates() -> None:
        length_x_coordinates = get_length(fields.x_coordinates)
        length_y_coordinates = get_length(fields.y_coordinates)
        num_coordinates = values[fields.num_coordinates.lower()]

        if not num_coordinates == length_x_coordinates == length_y_coordinates:
            raise ValueError(
                f"{fields.num_coordinates} should be equal to the amount of {fields.x_coordinates} and {fields.y_coordinates}"
            )

        validate_minimum_num_coordinates(num_coordinates)

    def validate_coordinates() -> None:
        len_x_coordinates = get_length(fields.x_coordinates)
        len_y_coordinates = get_length(fields.y_coordinates)

        if len_x_coordinates != len_y_coordinates:
            raise ValueError(
                f"{fields.x_coordinates} and {fields.y_coordinates} should have an equal amount of coordinates"
            )

        validate_minimum_num_coordinates(len_x_coordinates)

    def validate_minimum_num_coordinates(actual_num: int) -> None:
        if actual_num < config.minimum_num_coordinates:
            raise ValueError(
                f"{fields.x_coordinates} and {fields.y_coordinates} should have at least {config.minimum_num_coordinates} coordinate(s)"
            )

    def is_valid_node_specification() -> bool:
        has_other = (
            has_branch_id
            or has_chainage
            or has_x_coordinates
            or has_y_coordinates
            or has_num_coordinates
        )
        return has_node_id and not has_other

    def is_valid_branch_specification() -> bool:
        has_other = (
            has_node_id or has_x_coordinates or has_y_coordinates or has_num_coordinates
        )
        return has_branch_id and has_chainage and not has_other

    def is_valid_coordinates_specification() -> bool:
        has_other = has_node_id or has_branch_id or has_chainage or has_num_coordinates
        return has_x_coordinates and has_y_coordinates and not has_other

    def is_valid_coordinates_with_num_coordinates_specification() -> bool:
        has_other = has_node_id or has_branch_id or has_chainage
        return (
            has_x_coordinates
            and has_y_coordinates
            and has_num_coordinates
            and not has_other
        )

    # -----

    error_parts: List[str] = []

    if config.validate_node:
        if is_valid_node_specification():
            if config.validate_location_type:
                validate_location_type(LocationType.oned)
            return values

        error_parts.append(fields.node_id)

    if config.validate_branch:
        if is_valid_branch_specification():
            if config.validate_location_type:
                validate_location_type(LocationType.oned)
            return values

        error_parts.append(f"{fields.branch_id} and {fields.chainage}")

    if config.validate_coordinates:
        if config.validate_num_coordinates:
            if is_valid_coordinates_with_num_coordinates_specification():
                validate_coordinates_with_num_coordinates()
                return values

            error_parts.append(
                f"{fields.x_coordinates}, {fields.y_coordinates} and {fields.num_coordinates}"
            )

        else:
            if is_valid_coordinates_specification():
                validate_coordinates()
                return values

            error_parts.append(f"{fields.x_coordinates} and {fields.y_coordinates}")

    error = " or ".join(error_parts) + " should be provided"
    raise ValueError(error)


def rename_keys_for_backwards_compatibility(
    values: Dict, keys_to_rename: Dict[str, List[str]]
) -> Dict:
    """
    Renames the provided keys to support backwards compatibility.

    Args:

        values (Dict): Dictionary of input class fields.
        keys_to_rename (Dict[str, List[str]]): Dictionary of keys and a list of old keys that
        should be converted to the current key.

    Returns:
        Dict: Dictionary where the provided keys are renamed.
    """
    if not isinstance(values, dict):
        return values
    for current_keyword, old_keywords in keys_to_rename.items():
        if current_keyword in values:
            continue

        for old_keyword in old_keywords:
            if (value := values.get(old_keyword)) is not None:
                values[current_keyword] = value
                del values[old_keyword]
                break

    return values


class UnknownKeywordErrorManager:
    """
    Error manager for unknown keys.
    Detects unknown keys and manages the Error to the user.
    """

    def raise_error_for_unknown_keywords(
        self,
        data: Dict[str, Any],
        section_header: str,
        fields: Dict[str, FieldInfo],
        excluded_fields: Set[str],
    ) -> None:
        """
        Notify the user of unknown keywords.

        Args:
            data (Dict[str, Any]):
                Input data containing all properties which are checked on unknown keywords.
            section_header (str):
                Header of the section in which unknown keys might be detected.
            fields (Dict[str, FieldInfo]):
                Known fields of the section.
            excluded_fields (Set[str]):
                Fields which should be excluded from the check for unknown keywords.
        """
        unknown_keywords = self._get_all_unknown_keywords(data, fields, excluded_fields)

        if len(unknown_keywords) > 0:
            raise ValueError(
                f"Unknown keywords are detected in section: '{section_header}', '{unknown_keywords}'"
            )

    def _get_all_unknown_keywords(
        self,
        data: Dict[str, Any],
        fields: Dict[str, FieldInfo],
        excluded_fields: Set,
    ) -> List[str]:
        """
        Get all unknown keywords in the data.

        Args:
            data: Dict[str, Any]:
                Input data containing all properties which are checked on unknown keywords.
            fields: Dict[str, FieldInfo]:
                Known fields of the Model.
            excluded_fields: Set[str]:
                Fields which should be excluded from the check for unknown keywords.

        Returns:
            List[str]: List of unknown keywords.
        """
        list_of_unknown_keywords = []
        for keyword in data:
            if self._is_unknown_keyword(keyword, fields, excluded_fields):
                list_of_unknown_keywords.append(keyword)

        return list_of_unknown_keywords

    @staticmethod
    def _is_unknown_keyword(
        keyword: str, fields: Dict[str, FieldInfo], excluded_fields: Set
    ) -> bool:
        """
        Check if the given field name equals to any of the model field names or aliases, if not, the function checks if
        the field is not in the excluded_fields parameter.

        Args:
            keyword: str: Name of the field.
            fields: Dict[str, FieldInfo]: Known fields of the Model.
            excluded_fields: Set[str]: Fields which should be excluded from the check for unknown keywords.

        Returns:
            bool: True if the field is unknown (not a field name or alias and and not in the exclude list),
            False otherwise
        """
        exists = keyword in fields or any(
            hasattr(field_info, "alias") and keyword == field_info.alias
            for field_info in fields.values()
        )
        # the field is not in the known fields, check if it should be excluded
        unknown = not exists and keyword not in excluded_fields

        return unknown
