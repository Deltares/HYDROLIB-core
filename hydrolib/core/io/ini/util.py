"""util.py provides additional utility methods related to handling ini files.
"""
from enum import Enum
from typing import Any, Type

from pydantic.class_validators import validator
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


def get_default(cls: Type[BaseModel], fieldname: str, default: Any = None):
    """Gets the default value of a model field.

    Args:
        cls (Type[BaseModel]): A model
        fieldname (str): The field name for which to get the default for.
        default (Any, optional): Return value for when the field cannot be retrieved. Defaults to None.

    Returns:
        [Any]: Returns the default field value if found, otherwise `default`.
    """
    field = cls.__fields__.get(fieldname)
    if field:
        return field.default

    return default
