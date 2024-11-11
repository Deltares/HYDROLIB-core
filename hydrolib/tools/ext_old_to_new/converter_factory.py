from hydrolib.core.dflowfm.extold.models import ExtOldMeteoQuantity

from .base_converter import BaseConverter
from .meteo_converter import MeteoConverter


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
        else:
            raise ValueError(f"No converter available for QUANTITY={quantity}.")