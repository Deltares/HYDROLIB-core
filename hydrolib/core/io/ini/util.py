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


def make_list_length_root_validator(*field_names, length_name: str, id_name: str):
    """
    Get a root_validator that checks the correct length of several list fields in an object.

    Args:
        *field_names (str): names of the instance variables that are a list and need checking.
        length_name (str): name of the instance variable that stores the expected length.
        id_name (str): name of the ``id`` instance variable that will be printed in an error message string.
    """

    def validate_correct_length(cls, values):
        length = int(values.get(length_name, "0"))

        for field_name in field_names:
            field = values.get(field_name)
            if field is not None and not (
                isinstance(field, list) and len(field) == length
            ):
                raise ValueError(
                    f"Number of values for {field_name} should be equal to the {length_name} value ({id_name}={values[id_name]})."
                )
        return values

    return root_validator(allow_reuse=True)(validate_correct_length)


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
