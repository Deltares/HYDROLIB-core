from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.ext.models import (
    SOURCE_SINKS_QUANTITIES_VALID_PREFIXES,
    Boundary,
    Meteo,
    SourceSink,
)
from hydrolib.core.dflowfm.extold.models import (
    ExtOldBoundaryQuantity,
    ExtOldForcing,
    ExtOldInitialConditionQuantity,
    ExtOldMeteoQuantity,
    ExtOldParametersQuantity,
)
from hydrolib.core.dflowfm.inifield.models import InitialField, ParameterField
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.core.dflowfm.tim.parser import TimParser
from hydrolib.tools.ext_old_to_new.utils import (
    convert_initial_cond_param_dict,
    convert_interpolation_data,
    find_temperature_salinity_in_quantities,
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


def get_time_series_data(tim_model: TimModel) -> Dict[str, List[float]]:
    """Extract time series data from a TIM model.

    Extract the time series data (each column) from the TimModel object

    Args:
        tim_model (TimModel): The TimModel object containing the time series data.

    Returns:
        Dict[str, List[float]]: A dictionary containing the time series data form each column.
        the keys of the dictionary will be index starting from 1 to the number of columns in the tim file
        (excluding the first column(time)).

    Examples:
        >>> tim_file = Path("tests/data/external_forcings/initial_waterlevel.tim")
        >>> time_file = TimParser.parse(tim_file)
        >>> tim_model = TimModel(**time_file)
        >>> time_series = get_time_series_data(tim_model)
        >>> print(time_series)
        {
            1: [1.0, 1.0, 3.0, 5.0, 8.0],
            2: [2.0, 2.0, 5.0, 8.0, 10.0],
            3: [3.0, 5.0, 12.0, 9.0, 23.0],
            4: [4.0, 4.0, 4.0, 4.0, 4.0]
        }
    """
    num_locations = len(tim_model.timeseries[0].data)

    # Initialize a dictionary to collect data for each location
    data = {loc: [] for loc in range(1, num_locations + 1)}

    # Extract time series data for each location
    for record in tim_model.timeseries:
        for loc_index, value in enumerate(record.data, start=1):
            data[loc_index].append(value)

    return data


class SourceSinkConverter(BaseConverter):

    def __init__(self):
        super().__init__()

    @staticmethod
    def get_z_sources_sinks(polyline: PolyFile) -> Tuple[float, List[float]]:
        """
        Get the z values of the source and sink points from the polyline file.

        Args:
            polyline: The polyline object containing the source and sink points.

        Returns:
            z_source, z_sinkA: Tuple[float, List[float]]:
            If the polyline has data (more than 3 columns), then both the z_source and z_sink will be a list of two values.
            Otherwise, the z_source and the z_sink will be a single value each.

        Examples:
        in case the polyline has 3 columns:
            >>> polyline = PolyFile("tests/data/input/source-sink/leftsor.pliz")
            >>> z_source, z_sink = SourceSinkConverter().get_z_sources_sinks(polyline)
            >>> print(z_source, z_sink)
            [-3] [-4.2]

        in case the polyline has more than 3 columns:
            >>> polyline = PolyFile("tests/data/input/source-sink/leftsor-5-columns.pliz") #Doctest: +SKIP
            >>> z_source, z_sink = SourceSinkConverter().get_z_sources_sinks(polyline)
            >>> print(z_source, z_sink)
            [-3, -2.9] [-4.2, -5.35]
        """
        has_data = True if polyline.objects[0].points[0].data else False

        z_source_sink = []
        for elem in [0, -1]:
            point = polyline.objects[0].points[elem]
            if has_data:
                z_source_sink.append([point.z, point.data[0]])
            else:
                z_source_sink.append([point.z])

        z_sink = z_source_sink[0]
        z_source = z_source_sink[1]
        return z_source, z_sink

    def convert(
        self, forcing: ExtOldForcing, ext_file_quantity_list: List[str] = None
    ) -> ParameterField:
        """Convert an old external forcing block with Sources and sinks to a boundary
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
            ext_file_quantity_list (List[str], default is None): A list of other quantities that are present in the
            external forcings file.

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

        References:
            - `Sources and Sinks <https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#C10>`_
            - `Polyline <https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#C2>`
             - `TIM file format <https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#C4>`_
             - `Sources and Sinks <https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#5.4.10>`_
             - `Source and sink definitions <https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#C5.2.4>`_

        """
        location_file = forcing.filename.filepath

        # move this to a validator in the source and sink model
        polyline = PolyFile(location_file)
        x_coords = [point.x for point in polyline.objects[0].points]
        y_coords = [point.y for point in polyline.objects[0].points]
        z_coords = [point.z for point in polyline.objects[0].points]

        # check the tim file
        tim_file = forcing.filename.filepath.with_suffix(".tim")
        if not tim_file.exists():
            raise ValueError(
                f"TIM file '{tim_file}' not found for QUANTITY={forcing.quantity}"
            )
        time_file = TimParser.parse(tim_file)
        tim_model = TimModel(**time_file)
        time_series = get_time_series_data(tim_model)
        # get the required quantities from the external file
        required_quantities_from_ext = [
            key
            for key in ext_file_quantity_list
            if key.startswith(SOURCE_SINKS_QUANTITIES_VALID_PREFIXES)
        ]
        # check if the temperature and salinity are present in the external file
        temp_salinity_dict = find_temperature_salinity_in_quantities(
            ext_file_quantity_list
        )

        ext_file_quantity_list = (
            ["discharge"]
            + list(temp_salinity_dict.keys())
            + required_quantities_from_ext
        )

        time_series = {
            ext_file_quantity_list[i]: time_series[i + 1]
            for i in range(len(ext_file_quantity_list))
        }

        data = {
            "id": "L1",
            "name": forcing.quantity,
            "locationfile": location_file,
            "numcoordinates": len(x_coords),
            "xcoordinates": x_coords,
            "ycoordinates": y_coords,
            "zsource": z_coords[-1],
            "zsink": z_coords[0],
        }
        data = data | time_series

        data = convert_interpolation_data(forcing, data)
        data["operand"] = forcing.operand

        new_block = SourceSink(**data)

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
