"""Shared field validator mixins for D-Flow FM block models.

Home for validator mixins reused across the D-Flow FM subpackages; add new dflowfm validator mixins here.
Mixins that depend only on generic base functionality (no file-format coupling) live in
`hydrolib.core.base.validators` instead.
"""

from pydantic import ValidationInfo, field_validator

from hydrolib.core.base.validators import ListFieldDelimiter


class CoordinateValidator(ListFieldDelimiter):
    """Validator mixin for blocks that carry polygon coordinates.

    Holds the shared before-validator that splits space-delimited ``xCoordinates`` /
    ``yCoordinates`` strings into lists of floats. The coordinate fields themselves
    stay declared on each concrete block, so every block keeps control of its own
    keyword order. The validator uses ``check_fields=False`` so it applies only to
    subclasses that actually declare the coordinate fields, and it resolves the
    delimiter via the inherited `ListFieldDelimiter`.

    Intended to be combined with a concrete block model, e.g.
    ``class MassBalanceArea(CoordinateValidator, INIBasedModel): ...``.
    """

    @field_validator("xcoordinates", "ycoordinates", mode="before", check_fields=False)
    @classmethod
    def _split_coordinates_to_list(cls, v, info: ValidationInfo):
        return cls.split_string_on_delimiter(v, info)
