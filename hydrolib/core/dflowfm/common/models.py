"""Common model types for D-Flow FM files, including LocationType and Operand enums."""

from strenum import StrEnum


class LocationType(StrEnum):
    """Enum class containing the valid values for the locationType attribute.

    Used in several classes such as Lateral and ObservationPoint.
    """

    oned = "1d"
    """str: Denotes 1D locations (typically 1D pressure points) in a model."""

    twod = "2d"
    """str: Denotes 2D locations (typically 2D grid cells) in a model."""

    all = "all"
    """str: Denotes that both 1D and 2D locations may be selected."""


class Operand(StrEnum):
    """Enum class containing the valid values for the operand attribute.

    Used in several subclasses of AbstractIniField and ExtOldForcing.
    """
    override = "override"  # legacy: "O"
    """Existing values are overwritten with the provided values."""
    override_if_missing = "overrideIfMissing"  # legacy: "A"  (was named 'append')
    """Provided values are used where existing values are missing."""
    add = "add"  # legacy: "+" (was named add)
    """Existing values are summed with the provided values."""
    multiply = "multiply"  # legacy: "*" (was named mult)
    """Existing values are multiplied with the provided values."""
    maximum = "maximum"  # legacy: "x"
    """The maximum values of the existing values and provided values are used."""
    minimum = "minimum"  # legacy: "m"
    """The minimum values of the existing values and provided values are used."""

