"""util.py provides additional utility methods related to handling ini files.
"""
from enum import Enum
from typing import Any, List, Optional, Type

from pydantic.class_validators import root_validator, validator
from pydantic.main import BaseModel


def get_split_string_on_delimiter_validator(*field_name: str, delimiter: str = None):
    """Get a validator to split strings passed to the specified field_name.

    Strings are split based on the provided delimeter. The validator splits
    strings into a list of substrings before any other validation takes
    place.

    Args:
        delimiter (str, optional):
            The delimiter to split the string with. Defaults to None.

    Returns:
        the validator which splits strings on the provided delimiter.
    """

    def split(v: Any):
        if isinstance(v, str):
            v = v.split(delimiter)
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


def get_required_fields_validator(
    *field_names, conditional_field_name: str, conditional_value: Any
):
    """Gets a validator that checks whether the fields are provided, if `conditional_field_name` is equal to `conditional_value`.

    Args:
        *field_names (str): Names of the instance variables that need to be validated.
        conditional_field_name (str): Name of the instance variable on which the fields are dependent.
        conditional_value (Any): Value that the conditional field should contain to perform this validation.
    """

    def validate_required_fields(cls, values: dict):
        if values.get(conditional_field_name) != conditional_value:
            return values

        for field in field_names:
            if values.get(field) == None:
                raise ValueError(
                    f"{field} should be provided when {conditional_field_name} is {conditional_value}"
                )

        return values

    return root_validator(allow_reuse=True)(validate_required_fields)


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
