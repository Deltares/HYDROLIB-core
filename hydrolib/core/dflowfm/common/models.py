"""Common model types for D-Flow FM files, including LocationType and Operand enums."""

from strenum import StrEnum


class LocationType(StrEnum):
    """Enum class containing the valid values for the locationType attribute.

    Used in several classes such as Lateral and ObservationPoint.

    Attributes:
        oned: Denotes 1D locations (typically 1D pressure points) in a model.
        twod: Denotes 2D locations (typically 2D grid cells) in a model.
        all: Denotes that both 1D and 2D locations may be selected.
    """

    oned = "1d"
    twod = "2d"
    all = "all"


class Operand(StrEnum):
    """Enum class containing the valid values for the operand attribute.

    Used in several subclasses of AbstractIniField and ExtOldForcing.

    Attributes:
        override: Existing values are overwritten with the provided values. (legacy: "O")
        override_if_missing: Provided values are used where existing values are missing. (legacy: "A", was named 'append')
        add: Existing values are summed with the provided values. (legacy: "+")
        multiply: Existing values are multiplied with the provided values. (legacy: "*", was named 'mult')
        maximum: The maximum values of the existing values and provided values are used. (legacy: "X")
        minimum: The minimum values of the existing values and provided values are used. (legacy: "N")
    """

    override = "override"
    override_if_missing = "overrideIfMissing"
    add = "add"
    multiply = "multiply"
    maximum = "maximum"
    minimum = "minimum"

    @classmethod
    def legacy_alternatives(cls) -> dict[str, list[str]]:
        """Return the Operand member corresponding to a legacy single-character value.

        Args:
            legacy_value: A legacy operand character (e.g. "O", "A", "+", "*", "X", "N").

        Returns:
            The matching Operand member.

        Raises:
            ValueError: If the legacy value is not recognised.
        """
        return {
            cls.override.value: ["O"],
            cls.override_if_missing.value: ["A"],
            cls.add.value: ["+"],
            cls.multiply.value: ["*"],
            cls.maximum.value: ["X"],
            cls.minimum.value: ["N"],
        }
