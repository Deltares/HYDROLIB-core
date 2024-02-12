from strenum import StrEnum


class LocationType(StrEnum):
    """
    Enum class containing the valid values for the locationType
    attribute in several classes such as Lateral and ObservationPoint.
    """

    oned = "1d"
    """str: Denotes 1D locations (typically 1D pressure points) in a model."""

    twod = "2d"
    """str: Denotes 2D locations (typically 2D grid cells) in a model."""

    all = "all"
    """str: Denotes that both 1D and 2D locations may be selected."""


class Operand(StrEnum):
    """
    Enum class containing the valid values for the operand
    attribute in several subclasses of AbstractIniField and ExtOldForcing.
    """

    override = "O"
    """Existing values are overwritten with the provided values."""
    append = "A"
    """Provided values are used where existing values are missing."""
    add = "+"
    """Existing values are summed with the provided values."""
    mult = "*"
    """Existing values are multiplied with the provided values."""
    max = "X"
    """The maximum values of the existing values and provided values are used."""
    min = "N"
    """The minimum values of the existing values and provided values are used."""
