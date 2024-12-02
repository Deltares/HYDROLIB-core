from abc import abstractmethod

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.ext.models import Meteo
from hydrolib.core.dflowfm.extold.models import ExtOldForcing
from hydrolib.core.dflowfm.inifield.models import InterpolationMethod
from hydrolib.tools.ext_old_to_new.enum_converters import (
    oldfiletype_to_forcing_file_type,
    oldmethod_to_averaging_type,
    oldmethod_to_interpolation_method,
)

from .base_converter import BaseConverter


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
        meteo_data = {}
        meteo_data["quantity"] = forcing.quantity
        meteo_data["forcingfile"] = forcing.filename
        meteo_data["forcingfiletype"] = oldfiletype_to_forcing_file_type(
            forcing.filetype
        )
        meteo_data["forcingVariableName"] = forcing.varname
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
        meteo_data = {}
        meteo_data["quantity"] = forcing.quantity
        meteo_data["forcingfile"] = forcing.filename
        meteo_data["forcingfiletype"] = oldfiletype_to_forcing_file_type(
            forcing.filetype
        )
        meteo_data["forcingVariableName"] = forcing.varname
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
