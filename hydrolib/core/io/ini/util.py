"""util.py provides additional utility methods related to handling ini files.
"""
from enum import Enum
from operator import eq
from typing import Any, Callable, List, Optional, Type

from pydantic.class_validators import root_validator, validator
from pydantic.fields import ModelField
from pydantic.main import BaseModel

from hydrolib.core.utils import operator_str


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
