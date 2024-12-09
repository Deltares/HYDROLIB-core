from hydrolib.core.dflowfm.extold.models import (
    ExtOldBoundaryQuantity,
    ExtOldInitialConditionQuantity,
    ExtOldMeteoQuantity,
)
from hydrolib.tools.ext_old_to_new.converters import BaseConverter
from hydrolib.tools.ext_old_to_new.converters import (
    BoundaryConditionConverter,
    InitialConditionConverter,
    MeteoConverter,
)


def __contains__(cls, item):
    try:
        cls(item)
    except ValueError:
        return False
    return True


class ConverterFactory:
    """
    A factory class for creating converters based on the given quantity.
    """

    @staticmethod
    def create_converter(quantity) -> BaseConverter:
        """
        Create converter based on the given quantity.

        Args:
            quantity: The quantity for which the converter needs to be created.

        Returns:
            BaseConverter: An instance of a specific BaseConverter subclass
                for the given quantity.

        Raises:
            ValueError: If no converter is available for the given quantity.
        """
        if __contains__(ExtOldMeteoQuantity, quantity):
            return MeteoConverter()
        elif __contains__(ExtOldInitialConditionQuantity, quantity):
            return InitialConditionConverter()
        elif __contains__(ExtOldBoundaryQuantity, quantity):
            return BoundaryConditionConverter()
        else:
            raise ValueError(f"No converter available for QUANTITY={quantity}.")
