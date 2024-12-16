from abc import ABC, abstractmethod
from typing import Any

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.ext.models import Boundary, Meteo
from hydrolib.core.dflowfm.extold.models import (
    ExtOldBoundaryQuantity,
    ExtOldForcing,
    ExtOldInitialConditionQuantity,
    ExtOldMeteoQuantity,
    ExtOldParametersQuantity,
)
from hydrolib.core.dflowfm.inifield.models import InitialField, ParameterField
from hydrolib.tools.ext_old_to_new.utils import (
    convert_initial_cond_param_dict,
    convert_interpolation_data,
    oldfiletype_to_forcing_file_type,
)


class BaseConverter(ABC):
    """Abstract base class for converting old external forcings blocks
    to new blocks.

    Subclasses must implement the `convert` method, specific for the
    type of model data in the various old external forcing blocks.

    Class ConverterFactory uses these subclasses to create the correct
    converter, depending on the quantity of the forcing block.
    """

    def __init__(self):
        """Initializes the BaseConverter object."""
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


class MeteoConverter(BaseConverter):
    def __init__(self):
        super().__init__()

    def convert(self, forcing: ExtOldForcing) -> Meteo:
        """Convert an old external forcing block with meteo data to a Meteo
        forcing block suitable for inclusion in a new external forcings file.

        This function takes a forcing block from an old external forcings
        file, represented by an instance of ExtOldForcing, and converts it
        into a Meteo object. The Meteo object is suitable for use in new
        external forcings files, adhering to the updated format and
        specifications.

        Args:
            forcing (ExtOldForcing): The contents of a single forcing block
            in an old external forcings file. This object contains all the
            necessary information, such as quantity, values, and timestamps,
            required for the conversion process.

        Returns:
            Meteo: A Meteo object that represents the converted forcing
            block, ready to be included in a new external forcings file. The
            Meteo object conforms to the new format specifications, ensuring
            compatibility with updated systems and models.

        Raises:
            ValueError: If the forcing block contains a quantity that is not
            supported by the converter, a ValueError is raised. This ensures
            that only compatible forcing blocks are processed, maintaining
            data integrity and preventing errors in the conversion process.
        """
        meteo_data = {
            "quantity": forcing.quantity,
            "forcingfile": forcing.filename,
            "forcingfiletype": oldfiletype_to_forcing_file_type(forcing.filetype),
            "forcingVariableName": forcing.varname,
        }
        if forcing.sourcemask != DiskOnlyFileModel(None):
            raise ValueError(
                f"Attribute 'SOURCEMASK' is no longer supported, cannot "
                f"convert this input. Encountered for QUANTITY="
                f"{forcing.quantity} and FILENAME={forcing.filename}."
            )
        meteo_data = convert_interpolation_data(forcing, meteo_data)
        meteo_data["extrapolationAllowed"] = bool(forcing.extrapolation_method)
        meteo_data["extrapolationSearchRadius"] = forcing.maxsearchradius
        meteo_data["operand"] = forcing.operand

        meteo_block = Meteo(**meteo_data)

        return meteo_block


class BoundaryConditionConverter(BaseConverter):

    def __init__(self):
        super().__init__()

    def convert(self, forcing: ExtOldForcing) -> Boundary:
        """Convert an old external forcing block with meteo data to a boundary
        forcing block suitable for inclusion in a new external forcings file.

        This function takes a forcing block from an old external forcings
        file, represented by an instance of ExtOldForcing, and converts it
        into a Meteo object. The Boundary object is suitable for use in new
        external forcings files, adhering to the updated format and
        specifications.

        Args:
            forcing (ExtOldForcing): The contents of a single forcing block
            in an old external forcings file. This object contains all the
            necessary information, such as quantity, values, and timestamps,
            required for the conversion process.

        Returns:
            Boundary: A Boindary object that represents the converted forcing
            block, ready to be included in a new external forcings file. The
            Boundary object conforms to the new format specifications, ensuring
            compatibility with updated systems and models.

        Raises:
            ValueError: If the forcing block contains a quantity that is not
            supported by the converter, a ValueError is raised. This ensures
            that only compatible forcing blocks are processed, maintaining
            data integrity and preventing errors in the conversion process.
        """
        data = {
            "quantity": forcing.quantity,
            "locationfile": forcing.filename.filepath,
            "forcingfile": ForcingModel(),
        }

        new_block = Boundary(**data)

        return new_block


class InitialConditionConverter(BaseConverter):

    def __init__(self):
        super().__init__()

    def convert(self, forcing: ExtOldForcing) -> InitialField:
        """Convert an old external forcing block with Initial condition data to a IinitialField
        forcing block suitable for inclusion in a new inifieldfile file.


        This function takes a forcing block from an old external forcings
        file, represented by an instance of ExtOldForcing, and converts it
        into a InitialField object. The InitialField object is suitable for use in new
        iniFieldFile, adhering to the updated format and specifications.

        Args:
            forcing (ExtOldForcing): The contents of a single forcing block
            in an old external forcings file. This object contains all the
            necessary information, such as quantity, values, and timestamps,
            required for the conversion process.

        Returns:
            Initial condition field definition, represents an `[Initial]` block in an inifield file.

        Raises:
            ValueError: If the forcing block contains a quantity that is not
            supported by the converter, a ValueError is raised. This ensures
            that only compatible forcing blocks are processed, maintaining
            data integrity and preventing errors in the conversion process.

        References:
            [Sec.D](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.D)
        """
        data = convert_initial_cond_param_dict(forcing)
        new_block = InitialField(**data)

        return new_block


class ParametersConverter(BaseConverter):

    def __init__(self):
        super().__init__()

    def convert(self, forcing: ExtOldForcing) -> ParameterField:
        """Convert an old external forcing block with meteo data to a boundary
        forcing block suitable for inclusion in a new external forcings file.

        This function takes a forcing block from an old external forcings
        file, represented by an instance of ExtOldForcing, and converts it
        into a Meteo object. The Boundary object is suitable for use in new
        external forcings files, adhering to the updated format and
        specifications.

        Args:
            forcing (ExtOldForcing): The contents of a single forcing block
            in an old external forcings file. This object contains all the
            necessary information, such as quantity, values, and timestamps,
            required for the conversion process.

        Returns:
            Boundary: A Boindary object that represents the converted forcing
            block, ready to be included in a new external forcings file. The
            Boundary object conforms to the new format specifications, ensuring
            compatibility with updated systems and models.

        Raises:
            ValueError: If the forcing block contains a quantity that is not
            supported by the converter, a ValueError is raised. This ensures
            that only compatible forcing blocks are processed, maintaining
            data integrity and preventing errors in the conversion process.
        """
        data = convert_initial_cond_param_dict(forcing)
        new_block = ParameterField(**data)

        return new_block


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
        if ConverterFactory.contains(ExtOldMeteoQuantity, quantity):
            return MeteoConverter()
        elif ConverterFactory.contains(ExtOldInitialConditionQuantity, quantity):
            return InitialConditionConverter()
        elif ConverterFactory.contains(ExtOldBoundaryQuantity, quantity):
            return BoundaryConditionConverter()
        elif ConverterFactory.contains(ExtOldParametersQuantity, quantity):
            return ParametersConverter()
        else:
            raise ValueError(f"No converter available for QUANTITY={quantity}.")

    @staticmethod
    def contains(quantity_class, quantity) -> bool:
        try:
            quantity_class(quantity)
        except ValueError:
            return False

        return True
