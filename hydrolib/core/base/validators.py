"""Shared, format-agnostic validator (and validator-supporting) mixins.

These mixins hold validation behaviour reused across several subpackages, so they
live in `core/base` rather than in any file-format subpackage. Keeping them here lets
a validator mixin depend only on base functionality instead of importing from a
file-format subpackage such as `dflowfm.ini`.
"""

from abc import ABC
from typing import Any

from pydantic import ValidationInfo
from pydantic.fields import FieldInfo


class ListFieldDelimiter(ABC):
    """Resolve and apply the delimiter used to (de)serialize inline list fields.

    A capability mixin for models whose list fields are written inline as a
    delimited string (e.g. ``xCoordinates = 0.0 1.0 2.0``): it resolves the
    delimiter for a field and splits such strings into lists.

    The default delimiter is a single space; a field may override it with
    ``Field(..., json_schema_extra={"delimiter": ...})``. Concrete classes are
    expected to be Pydantic models, since the lookups use ``cls.model_fields``.

    Note:
        `INIBasedModel` inherits this mixin, so delimiter behavior is centralized
        here and reused across dependent models.
    """

    @classmethod
    def get_list_delimiter(cls) -> str:
        """Return the default delimiter used for list fields of this model.

        This should be overridden by any subclass for a particular file type that
        needs a specific/different list separator.
        """
        return " "

    @classmethod
    def get_list_field_delimiter(cls, field_key: str) -> str:
        """Return the delimiter for a specific field.

        The returned delimiter is either the field's custom list delimiter (set via
        ``Field(..., json_schema_extra={"delimiter": ...})``) or the model's default
        list delimiter.

        Args:
            field_key (str): The original field key (not its alias).

        Returns:
            str: The delimiter to use for (de)serializing the given field.
        """
        delimiter = None
        field_info = cls.model_fields.get(field_key)
        if (
            (field := field_info)
            and isinstance(field, FieldInfo)
            and field.json_schema_extra
        ):
            delimiter = field.json_schema_extra.get("delimiter")
        if not delimiter:
            delimiter = cls.get_list_delimiter()

        return delimiter

    @classmethod
    def split_string_on_delimiter(cls, v: Any, info: ValidationInfo) -> Any:
        """Split a delimited string field value into a list of trimmed strings.

        Args:
            v (Any): The value to split; returned unchanged when it is not a string.
            info (ValidationInfo): Pydantic validation info; supplies the field name.

        Returns:
            Any: A list of trimmed strings when the input is a string, else the input
                value unchanged.
        """
        if isinstance(v, str):
            v = v.split(cls.get_list_field_delimiter(info.field_name))
            v = [item.strip() for item in v if item != ""]
        return v
