from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Union

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel, TimeSeries
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
    ExtOldSourcesSinks,
)
from hydrolib.core.dflowfm.inifield.models import InitialField, ParameterField
from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.core.dflowfm.tim.parser import TimParser
from hydrolib.tools.ext_old_to_new.utils import (
    convert_interpolation_data,
    create_initial_cond_and_parameter_input_dict,
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


class SourceSinkConverter(BaseConverter):

    def __init__(self):
        super().__init__()

    @staticmethod
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
            >>> tim_file = Path("tests/data/input/source-sink/leftsor.tim")
            >>> time_file = TimParser.parse(tim_file)
            >>> tim_model = TimModel(**time_file)
            >>> time_series = SourceSinkConverter().get_time_series_data(tim_model)
            >>> print(time_series) # doctest: +SKIP
            {
                1: [1.0, 1.0, 3.0, 5.0, 8.0],
                2: [2.0, 2.0, 5.0, 8.0, 10.0],
                3: [3.0, 5.0, 12.0, 9.0, 23.0],
                4: [4.0, 4.0, 4.0, 4.0, 4.0]
            }
        """
        num_columns = len(tim_model.timeseries[0].data)

        # Initialize a dictionary to collect data for each location
        data = {loc: [] for loc in range(1, num_columns + 1)}

        # Extract time series data for each location
        for record in tim_model.timeseries:
            for loc_index, value in enumerate(record.data, start=1):
                data[loc_index].append(value)

        return data

    @staticmethod
    def merge_mdu_and_ext_file_quantities(
        mdu_quantities: Dict[str, bool], temp_salinity_from_ext: Dict[str, int]
    ) -> List[str]:
        """Merge the temperature and salinity from the mdu file with the temperature and salinity from the external file.

        Args:
            mdu_quantities (Dict[str, bool]): A dictionary containing the temperature and salinity details from the
                mdu file, with bool values indecating if the temperature/salinity is activated in the mdu file.
            temp_salinity_from_ext (Dict[str,int]): A dictionary containing the temperature and salinity details from
                the external file.

        Returns:
            List[str]: A list of quantities that will be used in the tim file.
        """
        if mdu_quantities:
            mdu_file_quantity_list = [key for key, val in mdu_quantities.items() if val]
            temp_salinity_from_mdu = find_temperature_salinity_in_quantities(
                mdu_file_quantity_list
            )
            final_temp_salinity = temp_salinity_from_ext | temp_salinity_from_mdu
            # the kwargs will be provided only from the source and sink converter
            # Ensure 'temperature' comes before 'salinity'
            keys = list(final_temp_salinity.keys())
            if "temperaturedelta" in keys and "salinitydelta" in keys:
                keys.remove("salinitydelta")
                keys.insert(keys.index("temperaturedelta"), "salinitydelta")
        else:
            keys = list(temp_salinity_from_ext.keys())

        return keys

    def parse_tim_model(
        self, tim_file: Path, ext_file_quantity_list: List[str], **mdu_quantities
    ) -> TimModel:
        """Parse the source and sinks related time series from the tim file.

        - Parse the TIM file and extract the time series data for each column.
        - assign the time series data to the corresponding quantity name.

        The order of the quantities in the tim file should be as follows:
        - time
        - discharge
        - salinitydelta (optional)
        - temperaturedelta (optional)
        - initialtracer-anyname (optional)
        - any other quantities from the external forcings file.

        Args:
            tim_file (Path): The path to the TIM file.
            ext_file_quantity_list (List[str]): A list of other quantities that are present in the external forcings file.
            **mdu_quantities: keyword argumens that will be provided if you want to provide the temperature and salinity
                details from the mdu file, the dictionary will have two keys `temperature`, `salinity` and the values are
                only bool. (i.e. {"temperature", False, "salinity": True})

        Returns:
            TimeModel: The same `TimModel after assigning the quantity names,  the time series data form each column in
            the tim_file.
            the keys of the dictionary will be the quantity names, and the values will be the time series data.

        Raises:
            ValueError: If the number of columns in the TIM file does not match the number of quantities in the external
            forcings file that has one of the following prefixes `initialtracer`,`tracerbnd`,
            `sedfracbnd`,`initialsedfrac`, plus the discharge, temperature, and salinity.

        Notes:
            - The function will combine the temperature and salinity from the MDU file (value is 1) file with the
                quantities mentioned in the external forcing file, and will get the list of quantities that are in the tim file.
            - The function will return a dictionary with the quantities as keys and the time series data as values.

        Examples:
        if the tim file contains 5 columns (the first column is the time):
            ```
            0.0 1.0 2.0 3.0 4.0
            1.0 1.0 2.0 3.0 4.0
            2.0 1.0 2.0 3.0 4.0
            3.0 1.0 2.0 3.0 4.0
            4.0 1.0 2.0 3.0 4.0
            ```
        and the external file contains the following quantities:
            >>> ext_file_quantity_list = ["discharge", "temperature", "salinity", "initialtracer-anyname",
            ... "anyother-quantities"]

        - The function will filter the external forcing quantities that have one of the following prefixes
        `initialtracer`,`tracerbnd`, `sedfracbnd`,`initialsedfrac`, plus the discharge, temperature, and salinity.
        - If the mdu_quantities are provided, the function will merge the temperature and salinity from the mdu file
        with the filtered quantities mentioned in the external forcing file.
        - The merged list of quantities from both the ext and mdu files will then be compared with the number of
        columns in the TIM file, if they don't match a `Value Error` will be raised.
        - Here the filtered quantities are ["discharge", "temperature", "salinity", "initialtracer-anyname"] and the
        tim file contains 4 columns (excluding the time column).

            >>> tim_file = Path("tests/data/input/source-sink/leftsor.tim")

            >>> converter = SourceSinkConverter()
            >>> time_series = converter.parse_tim_model(tim_file, ext_file_quantity_list)
            >>> print(time_series) # doctest: +SKIP
            {
                "discharge": [1.0, 1.0, 1.0, 1.0, 1.0],
                "salinitydelta": [2.0, 2.0, 2.0, 2.0, 2.0],
                "temperaturedelta": [3.0, 3.0, 3.0, 3.0, 3.0],
                "initialtracer-anyname": [4.0, 4.0, 4.0, 4.0, 4.0],
            }


        mdu file:
        ```
        [physics]
        ...
        Salinity             = 1        # Include salinity, (0=no, 1=yes)
        ...
        Temperature          = 1        # Include temperature, (0=no, 1=only transport, 3=excess model of D3D,5=heat flux model (5) of D3D)
        ```
        external forcings file:
        ```
        QUANTITY=initialtemperature
        FILENAME=right.pol
        ...

        QUANTITY=initialsalinity
        FILENAME=right.pol
        ...
        ```
        """
        time_file = TimParser.parse(tim_file)
        tim_model = TimModel(**time_file)
        time_series = self.get_time_series_data(tim_model)
        # get the required quantities from the external file
        required_quantities_from_ext = [
            key
            for key in ext_file_quantity_list
            if key.startswith(SOURCE_SINKS_QUANTITIES_VALID_PREFIXES)
        ]

        # check if the temperature and salinity are present in the external file
        temp_salinity_from_ext = find_temperature_salinity_in_quantities(
            ext_file_quantity_list
        )

        final_temp_salinity = self.merge_mdu_and_ext_file_quantities(
            mdu_quantities, temp_salinity_from_ext
        )
        final_quantities_list = (
            ["discharge"] + final_temp_salinity + required_quantities_from_ext
        )

        if len(time_series) != len(final_quantities_list):
            raise ValueError(
                f"Number of columns in the TIM file '{tim_file}: {len(time_series)}' does not match the number of "
                f"quantities in the external forcing file: {final_quantities_list}."
            )
        tim_model.quantities_names = final_quantities_list
        return tim_model

    @property
    def root_dir(self) -> Path:
        return self._root_dir

    @root_dir.setter
    def root_dir(self, value: Union[Path, str]):
        if isinstance(value, str):
            value = Path(value)
        self._root_dir = value

    def convert(
        self,
        forcing: ExtOldForcing,
        ext_file_quantity_list: List[str] = None,
        **temp_salinity_mdu,
    ) -> SourceSink:
        """Convert an old external forcing block with Sources and sinks to a SourceSink
        forcing block suitable for inclusion in a new external forcings file.

        Args:
            forcing (ExtOldForcing): The contents of a single forcing block in an old external forcings file. This
                object contains all the necessary information, such as quantity, values, and timestamps, required for the
                conversion process.
            ext_file_quantity_list (List[str], default is None): A list of other quantities that are present in the
                external forcings file.
            **temp_salinity_mdu:
                keyword arguments that will be provided if you want to provide the temperature and salinity details from
                the mdu file, the dictionary will have two keys `temperature`, `salinity` and the values are only bool.
                ```python
                {'salinity': True, 'temperature': True}
                ```

        Returns:
            SourceSink: A SourceSink object that represents the converted forcing
            block, ready to be included in a new external forcings file. The
            SourceSink object conforms to the new format specifications, ensuring
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
        polyline = forcing.filename

        z_source, z_sink = polyline.get_z_sources_sinks()

        # check the tim file
        tim_file = self.root_dir / polyline.filepath.with_suffix(".tim").name
        if not tim_file.exists():
            raise ValueError(
                f"TIM file '{tim_file}' not found for QUANTITY={forcing.quantity}"
            )

        time_model = self.parse_tim_model(
            tim_file, ext_file_quantity_list, **temp_salinity_mdu
        )
        units = time_model.get_units()
        user_defined_names = [
            f"user-defines-{i}" for i in range(len(time_model.quantities_names))
        ]

        # get from the mdu file
        start_time = "minutes since 2015-01-01 00:00:00"
        forcing_model = TimToForcingConverter().convert(
            time_model, start_time, units=units, user_defined_names=user_defined_names
        )
        data = {
            "id": "L1",
            "name": forcing.quantity,
            "locationfile": location_file,
            "numcoordinates": len(polyline.x),
            "xcoordinates": polyline.x,
            "ycoordinates": polyline.y,
            "zsource": z_source,
            "zsink": z_sink,
            "bc_forcing": forcing_model,
        }
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
        elif ConverterFactory.contains(ExtOldSourcesSinks, quantity):
            return SourceSinkConverter()
        else:
            raise ValueError(f"No converter available for QUANTITY={quantity}.")

    @staticmethod
    def contains(quantity_class, quantity) -> bool:
        try:
            quantity_class(quantity)
        except ValueError:
            return False

        return True


class TimToForcingConverter:
    """
    A class to convert TimModel data into ForcingModel data for boundary condition definitions.

    The class provides a static method `convert` to convert a TimModel object into a ForcingModel object.

    The method requires the following arguments:
    - `tim_model`: A TimModel object containing the time series data.
    - `start_time`: The reference time for the forcing data.
    - `time_interpolation`: The time interpolation method for the forcing data.
    - `units`: A list of units corresponding to the forcing quantities.
    - `user_defined_names`: A list of user-defined names for the forcing blocks.
    """

    @staticmethod
    def convert(
        tim_model: TimModel,
        start_time: str,
        time_interpolation: str = "linear",
        units: List[str] = None,
        user_defined_names: List[str] = None,
    ) -> ForcingModel:
        """
        Convert a TimModel into a ForcingModel.

        Args:
            tim_model (TimModel):
                The input TimModel to be converted.
            start_time (str):
                The reference time for the forcing data.
            time_interpolation (str, optional):
                The time interpolation method for the forcing data. Defaults to "linear".
            units (List[str], optional):
                A list of units corresponding to the forcing quantities.
            user_defined_names (List[str], optional):
                A list of user-defined names for the forcing blocks.

        Returns:
            ForcingModel: The converted ForcingModel.
        """
        if units is None or user_defined_names is None:
            raise ValueError("Both 'units' and 'user_defined_names' must be provided.")

        first_record = tim_model.timeseries[0].data
        if len(units) != len(user_defined_names) != len(first_record):
            raise ValueError(
                "The lengths of 'units', 'user_defined_names' and length of the columns in the first row must match."
            )

        df = tim_model.as_dataframe()
        time_data = df.index.tolist()
        forcings_list = []

        for i, (column, vals) in enumerate(df.items()):
            unit = units[i]
            forcing = TimeSeries(
                name=user_defined_names[i],
                function="timeseries",
                timeinterpolation=time_interpolation,
                quantity=["time", column],
                unit=[start_time, unit],
                datablock=[time_data, vals.values.tolist()],
            )
            forcings_list.append(forcing)

        forcing_model = ForcingModel(forcing=forcings_list)
        return forcing_model
