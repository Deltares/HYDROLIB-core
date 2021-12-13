"""util.py provides additional utility methods related to handling ini files.
"""
from enum import Enum
from typing import Any, Type

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
    """Get a case-insensitive enum validator that will returns the corresponding enum value.

    Args:
        enum (Type[Enum]): The enum type for which to validate.
    """

    def get_enum(v):
        for entry in enum:
            if entry.lower() == v.lower():
                return entry
        return v

    return validator(*field_name, allow_reuse=True, pre=True)(get_enum)


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
    """

    def validate_correct_length(cls, values: dict):
        length = values.get(length_name)
        if length is None:
            # length attribute not present, possibly defer validation to a subclass.
            return values

        length = length + length_incr
        incrstring = f" + {length_incr}" if length_incr != 0 else ""

        for field_name in field_names:
            field = values.get(field_name)
            if field is not None:
                if len(field) != length:
                    raise ValueError(
                        f"Number of values for {field_name} should be equal to the {length_name} value{incrstring}."
                    )
            elif list_required_with_length and length > 0:
                raise ValueError(
                    f"List {field_name} cannot be missing if {length_name} is given."
                )

        return values

    return root_validator(allow_reuse=True)(validate_correct_length)


# TODO also use this for the storage nodes once in the main
def get_required_fields_validator(
    *field_names, dependent_field_name: str, dependent_value: Any
):
    """Gets a validator that checks whether the fields are provided.

    Args:
        *field_names (str): names of the instance variables that need to be validated.
        dependent_field_name (str): name of the instance variable on which the fields are dependent.
        dependent_value (Any): the value that the dependent field should contain to perform this validation.
    """

    def validate_required_fields(cls, values: dict):
        if values.get(dependent_field_name) != dependent_value:
            return values

        for field in field_names:
            if values.get(field) == None:
                raise ValueError(
                    f"{field} should be provided when {dependent_field_name} is {dependent_value}"
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
