from abc import ABC, abstractmethod
from typing import Any

from hydrolib.core.dflowfm.extold.models import ExtOldForcing


class BaseConverter(ABC):
    """Abstract base class for converting old external forcings blocks
    to new blocks.

    Subclasses must implement the `convert` method, specific for the
    type of model data in the various old external forcing blocks.

    Class ConverterFactory uses these subclasses to create the correct
    converter, depending on the quantity of the forcing block.
    """

    def __init__(self):
        pass

    @abstractmethod
    def convert(self, data: ExtOldForcing) -> Any:
        """Converts the data from the old external forcings format to
        the proper/new model input block.

        Args:
            data (ExtOldForcing): The data read from an old format
                external forcings file.

        Returns:
            Any: The converted data in the new format. Should be
                included into some FileModel object by the caller.
        """
        raise NotImplementedError("Subclasses must implement convert method")
