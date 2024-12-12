from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.extold.models import ExtOldForcing
from hydrolib.core.dflowfm.inifield.models import InitialField, InterpolationMethod
from hydrolib.tools.ext_old_to_new.base_converter import BaseConverter
from hydrolib.tools.ext_old_to_new.enum_converters import (
    oldfiletype_to_forcing_file_type,
    oldmethod_to_averaging_type,
    oldmethod_to_interpolation_method,
)


class InitialConditionConverter(BaseConverter):
    def __init__(self):
        super().__init__()

    def convert(self, forcing: ExtOldForcing) -> InitialField:
        """Convert an old external forcing block with Initial condition data to a InitialField
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
            block_data["extrapolationmethod"] = forcing.extrapolation
        if hasattr(forcing, "locationtype"):
            block_data["locationtype"] = forcing.locationtype

        new_block = InitialField(**block_data)

        return new_block
