"""util.py provides additional utility methods related to handling ini files.
"""
from pydantic.class_validators import validator
from typing import Any


def get_split_string_on_delimeter_validator(*field_name: str, delimiter: str = None):
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
        return v

    return validator(*field_name, allow_reuse=True, pre=True)(split)
