from abc import ABC, abstractmethod
from typing import Any, Dict

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
from hydrolib.core.dflowfm.inifield.models import (
    InitialField,
    InterpolationMethod,
    ParameterField,
)
from hydrolib.tools.ext_old_to_new.utils import (
    oldfiletype_to_forcing_file_type,
    oldmethod_to_averaging_type,
    oldmethod_to_interpolation_method,
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
        meteo_data["interpolationmethod"] = oldmethod_to_interpolation_method(
            forcing.method
        )
        if meteo_data["interpolationmethod"] == InterpolationMethod.averaging:
            meteo_data["averagingtype"] = oldmethod_to_averaging_type(forcing.method)
            meteo_data["averagingrelsize"] = forcing.relativesearchcellsize
            meteo_data["averagingnummin"] = forcing.nummin
            meteo_data["averagingpercentile"] = forcing.percentileminmax

        meteo_data["extrapolationAllowed"] = bool(forcing.extrapolation_method)
        meteo_data["extrapolationSearchRadius"] = forcing.maxsearchradius
        meteo_data["operand"] = forcing.operand

        meteo_block = Meteo(**meteo_data)

        return meteo_block


class BoundaryConditionConverter(BaseConverter):

    def __init__(self):
        super().__init__()

    def convert(self, forcing: ExtOldForcing) -> Boundary:
        """Convert an old external forcing block to a boundary forcing block
        suitable for inclusion in a new external forcings file.

        This function takes a forcing block from an old external forcings
        file, represented by an instance of ExtOldForcing, and converts it
        into a boundary object. The Boundary object is suitable for use in new
        external forcings files, adhering to the updated format and
        specifications.

        Args:
            forcing (ExtOldForcing): The contents of a single forcing block
            in an old external forcings file. This object contains all the
            necessary information, such as quantity, values, and timestamps,
            required for the conversion process.

        Returns:
            Boundary: A Boundary object that represents the converted forcing
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


def create_initial_cond_and_parameter_input_dict(
    forcing: ExtOldForcing,
) -> Dict[str, str]:
    """Create the input dictionary for the `InitialField` or `ParameterField`

    Args:
        forcing: [ExtOldForcing]
            External forcing block from the old external forcings file.

    Returns:
        Dict[str, str]:
            the input dictionary to the `InitialField` or `ParameterField` constructor
    """
    block_data = {
        "quantity": forcing.quantity,
        "datafile": forcing.filename,
        "datafiletype": oldfiletype_to_forcing_file_type(forcing.filetype),
    }
    if block_data["datafiletype"] == "polygon":
        block_data["value"] = forcing.value

    if forcing.sourcemask != DiskOnlyFileModel(None):
        raise ValueError(
            f"Attribute 'SOURCEMASK' is no longer supported, cannot "
            f"convert this input. Encountered for QUANTITY="
            f"{forcing.quantity} and FILENAME={forcing.filename}."
        )
    block_data["interpolationmethod"] = oldmethod_to_interpolation_method(
        forcing.method
    )
    if block_data["interpolationmethod"] == InterpolationMethod.averaging:
        block_data["averagingtype"] = oldmethod_to_averaging_type(forcing.method)
        block_data["averagingrelsize"] = forcing.relativesearchcellsize
        block_data["averagingnummin"] = forcing.nummin
        block_data["averagingpercentile"] = forcing.percentileminmax
    block_data["operand"] = forcing.operand

    if hasattr(forcing, "extrapolation"):
        block_data["extrapolationmethod"] = (
            "yes" if forcing.extrapolation == 1 else "no"
        )

    return block_data


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
        data = create_initial_cond_and_parameter_input_dict(forcing)
        new_block = InitialField(**data)

        return new_block


class ParametersConverter(BaseConverter):

    def __init__(self):
        super().__init__()

    def convert(self, forcing: ExtOldForcing) -> ParameterField:
        """Convert an old external forcing block to a parameter forcing block
        suitable for inclusion in an initial field and parameter file.

        This function takes a forcing block from an old external forcings
        file, represented by an instance of ExtOldForcing, and converts it
        into a ParameterField object. The ParameterField object is suitable for use in
        an IniFieldModel, representing an initial field and parameter file, adhering
        to the updated format and specifications.

        Args:
            forcing (ExtOldForcing): The contents of a single forcing block
            in an old external forcings file. This object contains all the
            necessary information, such as quantity, values, and timestamps,
            required for the conversion process.

        Returns:
            ParameterField:
                A ParameterField object that represents the converted forcing
                block, ready to be included in an initial field and parameter file. The
                ParameterField object conforms to the new format specifications, ensuring
                compatibility with updated systems and models.

        Raises:
            ValueError: If the forcing block contains a quantity that is not
            supported by the converter, a ValueError is raised. This ensures
            that only compatible forcing blocks are processed, maintaining
            data integrity and preventing errors in the conversion process.
        """
        data = create_initial_cond_and_parameter_input_dict(forcing)
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
