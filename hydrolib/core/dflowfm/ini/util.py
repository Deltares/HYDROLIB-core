"""util.py provides additional utility methods related to handling ini files.
"""

from datetime import datetime
from enum import Enum
from operator import eq
from typing import Any, Callable, Dict, List, Optional, Set, Type

from pydantic.v1.class_validators import validator
from pydantic.v1.fields import ModelField
from pydantic.v1.main import BaseModel

from hydrolib.core.base.utils import operator_str, str_is_empty_or_none, to_list
from hydrolib.core.dflowfm.common.models import LocationType


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


def get_enum_validator(
    *field_name: str,
    enum: Type[Enum],
    alternative_enum_values: Optional[Dict[str, List[str]]] = None,
):
    """
    Get a case-insensitive enum validator that will returns the corresponding enum value.
    If the input is a list, then each list value is checked individually.

    Args:
        enum (Type[Enum]): The enum type for which to validate.
        alternative_enum_values (Dict[str, List[str]], optional): Dictionary with alternative
            allowed values for one or more of the enum keys. Dict key must be a valid current
            key of enum (case sensitive). Use this to backwards support and convert old enum
            values in user input. For example: {SomeEnum.current_value: ["old value"]}.
    """

    def get_enum(v):
        for entry in enum:
            if entry.lower() == v.lower():
                return entry
            if (
                alternative_enum_values is not None
                and (alt_values := alternative_enum_values.get(entry.value)) is not None
                and v.lower() in (altval.lower() for altval in alt_values)
            ):
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


def validate_correct_length(
    values: Dict,
    *field_names,
    length_name: str,
    length_incr: int = 0,
    list_required_with_length: bool = False,
    min_length: int = 0,
) -> Dict:
    """
    Validate the correct length (and presence) of several list fields in an object.

    Args:
        values (Dict): dictionary of values to validate.
        *field_names (str): names of the instance variables that are a list and need checking.
        length_name (str): name of the instance variable that stores the expected length.
        length_incr (int): Optional extra increment of length value (e.g., to have +1 extra value in lists).
        list_required_with_length (obj:`bool`, optional): Whether each list *must* be present if the length
            attribute is present (and > 0) in the input values. Default: False. If False, list length is only
            checked for the lists that are not None.
        min_length (int): minimum for list length value, overrides length_name value if that is smaller.
            For example, to require list length 1 when length value is given as 0.

    Raises:
        ValueError: When the number of values for any of the given field_names is not as expected.

    Returns:
        Dict: Dictionary of validated values.
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

    length = values.get(length_name)
    if length is None:
        # length attribute not present, possibly defer validation to a subclass.
        return values

    requiredlength = max(length + length_incr, min_length)

    for field_name in field_names:
        field = values.get(field_name)
        values[field_name] = _validate_listfield_length(
            field_name,
            field,
            requiredlength,
        )

    return values


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
) -> Dict:
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

    return values


def validate_conditionally(
    cls,
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
        cls: Reference to a class.
        values (Dict): Dictionary of input class fields.
        root_vldt (classmethod): A root validator that is to be called *if* the condition is satisfied.
        conditional_field_name (str): Name of the instance variable that determines whether the root validator must be called or not.
        conditional_value (Any): Value that the conditional field should be compared with to perform this validation.
        comparison_func (Callable): Binary operator function, used to override the default "eq" check for the conditional field value.

    Returns:
        Dict: Validated dictionary of input class fields.
    """
    if (val := values.get(conditional_field_name)) is not None and comparison_func(
        val, conditional_value
    ):
        # Condition is met: call the actual root validator, passing on the attribute values.
        root_vldt.__func__(cls, values)

    return values


def validate_datetime_string(
    field_value: Optional[str], field: ModelField
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
                f"Invalid datetime string for {field.alias}: '{field_value}', expecting 'YYYYmmddHHMMSS'."
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
    if (field := c.__fields__.get(fieldname)) is None:
        return None

    default = field.default

    if default is not None and default.lower() == value.lower():
        # If this class's default matches, directly return it to end the recursion.
        return default

    for sc in c.__subclasses__():
        default = _try_get_default_value(sc, fieldname, value)
        if default is not None:
            return default

    # Nothing found under c, return None to caller (e.g., to continue recursion).
    return None


def get_type_based_on_subclass_default_value(
    cls: Type, fieldname: str, value: str
) -> Optional[Type]:
    """
    Gets the type of the first subclass where the default value of the fieldname is equal
    to the provided value. If there is no match in the subclass, it will recursively search
    in the subclasses of the subclass.

    Args:
        cls (Type): The base type.
        fieldname (str): The field name for which retrieve the default for.
        value (str): The value to compare with.

    Returns:
        [type]: The type of the first subclass that has a default value for the provided fieldname
        equal to the provided value. Returns None if the fieldname is not found in the subclasses
        or if no match was found.
    """
    for c in cls.__subclasses__():
        subclass_type = _get_type_based_on_default_value(c, fieldname, value)
        if subclass_type is not None:
            return subclass_type
    return None


def _get_type_based_on_default_value(cls, fieldname, value) -> Optional[Type]:
    if (field := cls.__fields__.get(fieldname)) is None:
        return None

    default = field.default
    if default is not None and default.lower() == value.lower():
        return cls

    for sc in cls.__subclasses__():
        subclass_type = _get_type_based_on_default_value(sc, fieldname, value)
        if subclass_type is not None:
            return subclass_type

    return None


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
        values (Dict): Dictionary of object's validated fields.
        config (LocationValidationConfiguration, optional): Configuration for the location validation. Default is None.
        field (LocationValidationFieldNames, optional): Fields names that should be used for the location validation. Default is None.

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
        fields: Dict[str, ModelField],
        excluded_fields: Set[str],
    ) -> None:
        """
        Notify the user of unknown keywords.

        Args:
            data (Dict[str, Any])           : Input data containing all properties which are checked on unknown keywords.
            section_header (str)            : Header of the section in which unknown keys might be detected.
            fields (Dict[str, ModelField])  : Known fields of the section.
            excluded_fields (Set[str])      : Fields which should be excluded from the check for unknown keywords.
        """
        unknown_keywords = self._get_all_unknown_keywords(data, fields, excluded_fields)

        if len(unknown_keywords) > 0:
            raise ValueError(
                f"Unknown keywords are detected in section: '{section_header}', '{unknown_keywords}'"
            )

    def _get_all_unknown_keywords(
        self, data: Dict[str, Any], fields: Dict[str, ModelField], excluded_fields: Set
    ) -> List[str]:
        """
        Get all unknown keywords in the data.

        Args:
            data: Dict[str, Any]: Input data containing all properties which are checked on unknown keywords.
            fields: Dict[str, ModelField]: Known fields of the Model.
            excluded_fields: Set[str]: Fields which should be excluded from the check for unknown keywords.

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
        keyword: str, fields: Dict[str, ModelField], excluded_fields: Set
    ):
        """
        Check if the given field name equals to any of the model field names or aliases, if not, the function checks if
        the field is not in the excluded_fields parameter.

        Args:
            keyword: str: Name of the field.
            fields: Dict[str, ModelField]: Known fields of the Model.
            excluded_fields: Set[str]: Fields which should be excluded from the check for unknown keywords.

        Returns:
            bool: True if the field is unknown (not a field name or alias and and not in the exclude list),
            False otherwise
        """
        exists = any(
            keyword == model_field.name or keyword == model_field.alias
            for model_field in fields.values()
        )
        # the field is not in the known fields, check if it should be excluded
        unknown = not exists and keyword not in excluded_fields

        return unknown
