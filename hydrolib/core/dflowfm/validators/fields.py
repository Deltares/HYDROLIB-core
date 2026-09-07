"""Shared field validator mixins for D-Flow FM block models.

Home for validator mixins reused across the D-Flow FM subpackages; add new dflowfm validator mixins here.
Mixins that depend only on generic base functionality (no file-format coupling) live in
`hydrolib.core.base.validators` instead.
"""

from abc import ABC

from pydantic import ValidationInfo, field_validator

from hydrolib.core.base.validators import ListFieldDelimiter
from hydrolib.core.dflowfm.common.models import (
    DataFileType,
    InterpolationMethod,
    LocationType,
    Operand,
)
from hydrolib.core.dflowfm.ini.util import enum_value_parser


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


class OperandInterpolationValidators(ABC):
    """Field validators common to every spatial-field block.

    A plain validator mixin (not an `INIBasedModel` itself); the concrete block
    bases `SpatialForcingBase` and `AbstractSpatialField` bring in `INIBasedModel`.

    Holds the `operand` and `interpolationMethod` validators shared by all four
    spatial-field blocks: `Meteo` / `Spatial` (external forcings) and
    `InitialField` / `ParameterField` (inifield). It is inherited directly by the
    two concrete block bases `SpatialForcingBase` (for `Meteo` / `Spatial`) and
    `AbstractSpatialField` (for `InitialField` / `ParameterField`). The validators
    use ``check_fields=False`` so each applies only to the subclasses that declare
    the corresponding field.

    `averagingType` is intentionally not shared: `Meteo` reaches this base too and
    stores `averagingType` as a raw integer, so an enum validator on it must stay
    off `Meteo`.
    """

    @field_validator("operand", mode="before", check_fields=False)
    @classmethod
    def _validate_operand(cls, v):
        return enum_value_parser(v, Operand, Operand.legacy_alternatives())

    @field_validator("interpolationmethod", mode="before", check_fields=False)
    @classmethod
    def _validate_interpolationmethod(cls, v):
        return enum_value_parser(v, InterpolationMethod)


class LocationTypeDataFileTypeValidators(ABC):
    """Field validators shared by the data-file spatial blocks.

    An independent plain validator mixin holding the `locationType` and
    `dataFileType` validators shared by `Spatial` (external forcings) and
    `InitialField` / `ParameterField` (inifield). `Meteo` does not use it — it has
    a `forcingFileType` and no `locationType` field. It does not inherit
    `OperandInterpolationValidators`; classes that need both validator groups
    (`Spatial`, `AbstractSpatialField`) inherit both mixins directly.
    """

    @field_validator("locationtype", mode="before", check_fields=False)
    @classmethod
    def _validate_locationtype(cls, v):
        return enum_value_parser(v, LocationType)

    @field_validator("datafiletype", mode="before", check_fields=False)
    @classmethod
    def _validate_datafiletype(cls, v):
        result = v
        if v is not None:
            result = enum_value_parser(v, DataFileType)
        return result
