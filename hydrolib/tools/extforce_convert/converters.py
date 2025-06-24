"""External forcing converter."""

from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from hydrolib.core.base.file_manager import PathOrStr
from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import (
    T3D,
    Astronomic,
    ForcingBase,
    ForcingModel,
    Harmonic,
    QuantityUnitPair,
    TimeSeries,
)
from hydrolib.core.dflowfm.cmp.models import AstronomicRecord, CMPModel, HarmonicRecord
from hydrolib.core.dflowfm.ext.models import (
    SOURCE_SINKS_QUANTITIES_VALID_PREFIXES,
    Boundary,
    BoundaryError,
    InitialFieldError,
    Meteo,
    MeteoError,
    SourceSink,
    SourceSinkError,
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
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.t3d.models import T3DModel
from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.core.dflowfm.tim.parser import TimParser
from hydrolib.tools.extforce_convert.utils import (
    convert_interpolation_data,
    create_initial_cond_and_parameter_input_dict,
    find_temperature_salinity_in_quantities,
    oldfiletype_to_forcing_file_type,
)


class BaseConverter(ABC):
    """Abstract base class for converting old external forcings blocks to new blocks.

    Subclasses must implement the `convert` method, specific for the
    type of model data in the various old external forcing blocks.

    Class ConverterFactory uses these subclasses to create the correct
    converter, depending on the quantity of the forcing block.
    """

    def __init__(self):
        """Initializes the BaseConverter object."""
        self._root_dir = None

    @property
    def root_dir(self) -> Path:
        """Get the root directory of the external forcing files."""
        return self._root_dir

    @root_dir.setter
    def root_dir(self, value: Union[Path, str]):
        if isinstance(value, str):
            value = Path(value)
        self._root_dir = value

    @abstractmethod
    def convert(self, forcing: ExtOldForcing) -> Any:
        """Converts the data from the old external forcings format to the proper/new model input block.

        Args:
            forcing (ExtOldForcing): The data read from an old format
                external forcings file.

        Returns:
            Any: The converted data in the new format. Should be
                included in some FileModel object by the caller.
        """
        raise NotImplementedError("Subclasses must implement convert method")


class MeteoConverter(BaseConverter):
    """Meteo quantities Converter."""

    def __init__(self):
        """Meteo converter constructor."""
        super().__init__()

    def convert(self, forcing: ExtOldForcing) -> Meteo:
        """Meteo converter.

        Convert an old external forcing block with meteo data to a Meteo
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
        try:
            meteo_block = Meteo(**meteo_data)
        except Exception as e:
            raise MeteoError(
                f"Failed to create the Meteo object. for the following Errors: {e}"
            )

        return meteo_block


class BoundaryConditionConverter(BaseConverter):
    """Boundary condition converter."""

    def __init__(self):
        """Boundary condition converter constructor."""
        super().__init__()

    @staticmethod
    def merge_tim_files(tim_files: List[Path], quantity: str) -> TimModel:
        """Parse the boundary condition related time series from the tim files.

        The function will merge all the tim files into one tim model and assign the quantity names to the tim model.

        Args:
            tim_files (List[Path]):
                List of TIM models paths.
            quantity (str):
                name of the quantity that the tim files represent.
        Returns:
            TimModel: A TimModel object containing the time series data from all given TIM files.
        """
        time_files_exist = all([tim_file.exists() for tim_file in tim_files])
        if not time_files_exist:
            raise FileNotFoundError(
                f"TIM files '{tim_files}' not found for QUANTITY={quantity}"
            )

        tim_models = [
            TimModel(file, quantities_names=[file.stem]) for file in tim_files
        ]
        # merge all the tim files into one tim model
        for tim_model in tim_models[1:]:
            data = tim_model.as_dict()
            if len(data.keys()) != 1:
                raise ValueError(
                    f"Number of columns in the TIM file '{tim_model.filepath}' should be 1 column. in addition to the "
                    "time column."
                )
            tim_models[0].add_column(
                list(data.values())[0], column_name=list(data.keys())[0]
            )
        return tim_models[0]

    def convert_tim_to_bc(
        self,
        tim_files: List[PathOrStr],
        time_unit: str,
        time_interpolation: str = "linear",
        quantity: str = None,
        label: str = None,
    ) -> List[TimeSeries]:
        """Convert a TimModel into a ForcingModel.

        wrapper on top of the `TimToForcingConverter.convert` method. to customize it for the source and sink

        Args:
            tim_files (List[Union[Path, str]]):
                paths to the tim files to be converted.
            time_unit (str):
                Formatted string containing the units of time, including absolute datetime reference information
                (according to UDunits). For example, "minutes since 1992-10-8 15:15:42.5 -6:00".
            time_interpolation (str, default is linear):
                The interpolation method to be used for the time series data.
            quantity (str, default is None):
                name of the quantity that the tim files represent.
            label (str, default is None):
                the label from the pli file to be used to name the time series sections in the .bc model.

        Returns:
            ForcingModel: The converted ForcingModel.

        Raises:
            ValueError: If `units` and `user_defined_names` are not provided.
            ValueError: If the lengths of `units`, `user_defined_names`, and the columns in the first row of the TimModel
        """
        tim_model = self.merge_tim_files(tim_files, quantity)

        num_tim_files = len(tim_files)
        # switch the quantity names from the Tim model (loction names) to quantity names.
        user_defined_names = [
            f"{label}_{str(i).zfill(4)}" for i in range(1, num_tim_files + 1)
        ]
        tim_model.quantities_names = [quantity] * len(tim_model.get_units())
        units = tim_model.get_units()
        time_series_list = TimToForcingConverter.convert(
            tim_model, time_unit, time_interpolation, units, user_defined_names
        )
        return time_series_list

    def convert(
        self, forcing: ExtOldForcing, time_unit: Optional[str] = None
    ) -> Boundary:
        """Boundary condition converter.

        Convert an old external forcing block to a boundary forcing block
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
            time_unit:
                The start date of the time series data.

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

        Notes:
            - The `root_dir` property must be set before calling this method.
            - Since the `start_time` argument must be provided from the mdu file to convert the time series data,
            boundary Condition can be only converted by reading the mdu file and the external forcing file is not
            enough.
        """
        quantity = forcing.quantity
        location_file = forcing.filename.filepath
        poly_line = forcing.filename
        if not isinstance(poly_line, PolyFile):
            poly_line = PolyFile(location_file)

        label = poly_line.objects[0].metadata.name
        if self.root_dir is None:
            raise ValueError(
                "The 'root_dir' property must be set before calling this method."
            )

        forcings_list = []
        tim_files = list(
            self.root_dir.glob(f"{poly_line.filepath.stem}_[0-9][0-9][0-9][0-9].tim")
        )
        if len(tim_files) > 0:
            time_series_list = self.convert_tim_to_bc(
                tim_files, time_unit, quantity=quantity, label=label
            )
            forcings_list.extend(time_series_list)

        # check t3d files
        t3d_files = list(
            self.root_dir.glob(f"{poly_line.filepath.stem}_[0-9][0-9][0-9][0-9]*.t3d")
        )
        if len(t3d_files) > 0:
            t3d_models = [T3DModel(path) for path in t3d_files]
            # this line assumed that the two t3d files will have the same number of layers and same number of quantities
            quantities_names = [quantity] * t3d_models[0].size[1]
            user_defined_names = [
                f"{label}_{str(i).zfill(4)}" for i in range(1, len(t3d_files) + 1)
            ]
            t3d_forcing_list = T3DToForcingConverter.convert(
                t3d_models, quantities_names, user_defined_names
            )
            forcings_list.extend(t3d_forcing_list)

        # check cmp files
        cmp_files = list(
            self.root_dir.glob(f"{poly_line.filepath.stem}_[0-9][0-9][0-9][0-9]*.cmp")
        )
        if len(cmp_files) > 0:
            cmp_models = [CMPModel(path) for path in cmp_files]
            for cmp_model in cmp_models:
                cmp_model.quantities_name = [forcing.quantity]
                user_defined_names = [
                    f"{label}_{str(i).zfill(4)}" for i in range(1, len(cmp_files) + 1)
                ]
            forcing_list = CMPToForcingConverter.convert(cmp_models, user_defined_names)
            forcings_list.extend(forcing_list)

        forcing_model = ForcingModel(forcing=forcings_list)

        # set the bc file names to the same names as the tim files.
        forcing_model.filepath = location_file.with_suffix(".bc")

        data = {
            "quantity": forcing.quantity,
            "locationfile": location_file,
            "forcingfile": forcing_model,
        }

        try:
            new_block = Boundary(**data)
        except Exception as e:
            raise BoundaryError(
                f"Failed to create the Boundary object. for the following Errors: {e}"
            )

        return new_block


class InitialConditionConverter(BaseConverter):
    """Initial condition converter."""

    def __init__(self):
        """Initial condition converter constructor."""
        super().__init__()

    def convert(self, forcing: ExtOldForcing) -> InitialField:
        """Convert the Initial condition quantities.

        Convert an old external forcing block with Initial condition data to a IinitialField
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
        try:
            new_block = InitialField(**data)
        except Exception as e:
            raise InitialFieldError(
                f"Failed to create the InitialField object. for the following Errors: {e}"
            )

        return new_block


class ParametersConverter(BaseConverter):
    """Parameter converter."""

    def __init__(self):
        """Parameter converter constructor."""
        super().__init__()

    def convert(self, forcing: ExtOldForcing) -> ParameterField:
        """Parameter converter.

        Convert an old external forcing block to a parameter forcing block
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
    """Source and sink converter."""

    def __init__(self):
        """Source and sink converter Constructor."""
        super().__init__()

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
        - tracer<anyname>delta (optional)
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
            >>> ext_file_quantity_list = ["discharge", "temperature", "salinity", "initialtracerAnyname",
            ... "anyother-quantities"]

        - The function will filter the external forcing quantities that have one of the following prefixes
        `initialtracer`,`tracerbnd`, `sedfracbnd`,`initialsedfrac`, plus the discharge, temperature, and salinity.
        - If the mdu_quantities are provided, the function will merge the temperature and salinity from the mdu file
        with the filtered quantities mentioned in the external forcing file.
        - The merged list of quantities from both the ext and mdu files will then be compared with the number of
        columns in the TIM file, if they don't match a `Value Error` will be raised.
        - Here the filtered quantities are ["discharge", "temperature", "salinity", "initialtracerAnyname"] and the
        tim file contains 4 columns (excluding the time column).

            >>> tim_file = Path("tests/data/input/source-sink/leftsor.tim")
            >>> converter = SourceSinkConverter()
            >>> tim_model = converter.parse_tim_model(tim_file, ext_file_quantity_list)
            >>> print(tim_model.quantities_names)
            ['discharge', 'salinitydelta', 'temperaturedelta', 'initialtracerAnyname']
            >>> print(tim_model.as_dict()) # doctest: +SKIP
            {
                "discharge": [1.0, 1.0, 1.0, 1.0, 1.0],
                "salinitydelta": [2.0, 2.0, 2.0, 2.0, 2.0],
                "temperaturedelta": [3.0, 3.0, 3.0, 3.0, 3.0],
                "initialtracerAnyname": [4.0, 4.0, 4.0, 4.0, 4.0],
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
        time_series = tim_model.as_dict()
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
        # assign the quantity names to the tim model
        tim_model.quantities_names = final_quantities_list
        return tim_model

    @property
    def root_dir(self) -> Path:
        """Root directory of the external forcing files."""
        return self._root_dir

    @root_dir.setter
    def root_dir(self, value: Union[Path, str]):
        if isinstance(value, str):
            value = Path(value)
        self._root_dir = value

    @staticmethod
    def convert_tim_to_bc(
        tim_model: TimModel,
        time_unit: str,
        user_defined_names: List[str] = None,
    ) -> ForcingModel:
        """Convert a TimModel into a ForcingModel.

            wrapper in top of the `TimToForcingConverter.convert` method. to customize it for the source and sink

        Args:
            tim_model (TimModel):
                The input TimModel to be converted.
            time_unit (str):
                Formatted string containing the units of time, including absolute datetime reference information
                (according to UDunits). For example, "minutes since 1992-10-8 15:15:42.5 -6:00".
            user_defined_names (List[str], optional):
                A list of user-defined names for the forcing blocks.

        Returns:
            ForcingModel: The converted ForcingModel.

        Raises:
            ValueError: If `units` and `user_defined_names` are not provided.
            ValueError: If the lengths of `units`, `user_defined_names`, and the columns in the first row of the TimModel
        """
        units = tim_model.get_units()
        time_series_list = TimToForcingConverter.convert(
            tim_model, time_unit, units=units, user_defined_names=user_defined_names
        )
        forcing_model = ForcingModel(forcing=time_series_list)
        return forcing_model

    @staticmethod
    def separate_forcing_model(forcing_model: ForcingModel) -> Dict[str, ForcingModel]:
        """Separate the forcing model into a list of forcing models.

        each forcing model will contain only one forcing quantity.
        """
        forcing_list = [deepcopy(forcing) for forcing in forcing_model.forcing]

        forcing_model_list = []
        forcings = {}
        for forcing in forcing_list:
            model = deepcopy(forcing_model)
            model.forcing = [forcing]
            forcing_model_list.append(model)
            name = forcing.quantityunitpair[1].quantity
            forcings[name] = model

        return forcings

    def convert(
        self,
        forcing: ExtOldForcing,
        ext_file_quantity_list: List[str] = None,
        start_time: str = None,
        **temp_salinity_mdu,
    ) -> SourceSink:
        """Source and sink converter.

        Convert an old external forcing block with Sources and sinks to a SourceSink
        forcing block suitable for inclusion in a new external forcings file.

        Args:
            forcing (ExtOldForcing): The contents of a single forcing block in an old external forcings file. This
                object contains all the necessary information, such as quantity, values, and timestamps, required for the
                conversion process.
            ext_file_quantity_list (List[str], default is None): A list of other quantities that are present in the
                external forcings file.
            start_time (str, default is None):
                The start date of the time series data.
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

        Notes:
            - Since the `start_time` argument must be provided from the mdu file to convert the time series data,
            SourceSink can be only converted by reading the mdu file and the external forcing file is not
            enough.

        References:
            - `Sources and Sinks <https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#C10>`_
            - `Polyline <https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#C2>`
            - `TIM file format <https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#C4>`_
            - `Sources and Sinks <https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#5.4.10>`_
            - `Source and sink definitions <https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#C5.2.4>`_

        """
        location_file = forcing.filename.filepath
        polyline = forcing.filename
        location_name = location_file.stem
        z_source, z_sink = polyline.get_z_sources_sinks()

        # check the tim file
        tim_file = self.root_dir / polyline.filepath.with_suffix(".tim").name
        if not tim_file.exists():
            raise ValueError(
                f"TIM file '{tim_file}' not found for QUANTITY={forcing.quantity}"
            )

        tim_model = self.parse_tim_model(
            tim_file, ext_file_quantity_list, **temp_salinity_mdu
        )
        labels = [f"{location_name}"] * len(tim_model.quantities_names)

        forcing_model = self.convert_tim_to_bc(
            tim_model, start_time, user_defined_names=labels
        )
        # set the bc file names to the same names as the tim files.
        forcing_model.filepath = location_file.with_suffix(".bc").name

        data = {
            "id": location_name,
            "name": forcing.quantity,
            "numcoordinates": len(polyline.x),
            "xcoordinates": polyline.x,
            "ycoordinates": polyline.y,
        }
        forcings = self.separate_forcing_model(forcing_model)

        # the same forcing model will be used for all the forcings to be able to save all the forcings (sourcesinks)
        # in the same file.
        for name, _ in forcings.items():
            forcings[name] = forcing_model

        data = data | forcings

        if None not in z_source:
            # if the z_source and z_sink are not None, then add them to the data
            z_source_sink_data = {
                "zsource": z_source,
                "zsink": z_sink,
            }
            data = data | z_source_sink_data

        try:
            new_block = SourceSink(**data)
        except Exception as e:  # pragma: no cover
            raise SourceSinkError(
                f"Failed to create the SourceSink object. for the following Errors: {e}"
            )

        return new_block


class ConverterFactory:
    """A factory class for creating converters based on the given quantity."""

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
        """Check if the given quantity is in the specified class."""
        try:
            quantity_class(quantity)
        except ValueError:
            return False

        return True


class CMPToForcingConverter:
    """A class to convert CmpModel data into ForcingModel data for boundary condition definitions."""

    @staticmethod
    def convert(
        cmp_models: List[CMPModel], user_defined_names: List[str] = None
    ) -> List[ForcingBase]:
        """
        Convert a CmpModel into a ForcingModel.

        Args:
            cmp_models (List[CmpModel]):
                The input CmpModel to be converted.
            user_defined_names (List[str]):
                user defined names for the quantities.Default is None.

        Returns:
            ForcingModel: The converted ForcingModel.

        Raises:
            ValueError: If the lengths of the columns in the first row of the CmpModel do not match the number of
                quantities in the CmpModel.

        Examples:
            Convert a CmpModel into a ForcingModel.
                ```python
                >>> harmonic_data = {
                ...     "comments": ["# Example comment"],
                ...     "component": {
                ...         "harmonics": [{"period": 0.0, "amplitude": 1.0, "phase": 2.0}],
                ...     },
                ...     "quantities_name": ["discharge"],
                ... }
                >>> astronomic_data = {
                ...     "comments": ["# Example comment"],
                ...     "component": {
                ...         "astronomics": [{"name": "4MS10", "amplitude": 1.0, "phase": 2.0}],
                ...     },
                ...     "quantities_name": ["waterlevel"],
                ... }
                >>> cmp_models = [CMPModel(**harmonic_data), CMPModel(**astronomic_data)]
                >>> forcing_model = CMPToForcingConverter.convert(cmp_models,["L1_0001", "L1_0002"])
                >>> forcing_model[0].datablock
                [[0.0, 1.0, 2.0]]
                >>> forcing_model[1].datablock
                [['4MS10', 1.0, 2.0]]

                ```
        """
        forcing_list = []

        for label, cmp_model in zip(user_defined_names, cmp_models):
            if cmp_model.component.harmonics:
                harmonic_model = CMPToForcingConverter.convert_harmonic(
                    label,
                    cmp_model.component.harmonics,
                    cmp_model.quantities_name[0],
                    unit=cmp_model.get_units()[0],
                )
                forcing_list.append(harmonic_model)

            if cmp_model.component.astronomics:
                astronomic_model = CMPToForcingConverter.convert_astronomic(
                    label,
                    cmp_model.component.astronomics,
                    cmp_model.quantities_name[0],
                    unit=cmp_model.get_units()[0],
                )
                forcing_list.append(astronomic_model)

        return forcing_list

    @staticmethod
    def convert_harmonic(
        user_defined_name,
        harmonics: List[HarmonicRecord],
        quantity_name: str,
        unit: str,
    ) -> Harmonic:
        """Convert a list of harmonic records into a Harmonic object."""
        harmonic_block = [
            [harmonic.period, harmonic.amplitude, harmonic.phase]
            for harmonic in harmonics
        ]
        harmonic_model = Harmonic(
            name=user_defined_name,
            function="harmonic",
            quantityunitpair=[
                QuantityUnitPair(quantity="harmonic component", unit="minutes"),
                QuantityUnitPair(quantity=f"{quantity_name} amplitude", unit=unit),
                QuantityUnitPair(quantity=f"{quantity_name} phase", unit="deg"),
            ],
            datablock=harmonic_block,
        )
        return harmonic_model

    @staticmethod
    def convert_astronomic(
        user_defined_name,
        astronomics: List[AstronomicRecord],
        quantity_name: str,
        unit: str,
    ) -> Astronomic:
        """Convert a list of astronomic records into an Astronomic object."""
        astronomic_block = [
            [astronomic.name, astronomic.amplitude, astronomic.phase]
            for astronomic in astronomics
        ]
        astronomic_model = Astronomic(
            name=user_defined_name,
            function="astronomic",
            quantityunitpair=[
                QuantityUnitPair(quantity="astronomic component", unit="-"),
                QuantityUnitPair(quantity=f"{quantity_name} amplitude", unit=unit),
                QuantityUnitPair(quantity=f"{quantity_name} phase", unit="deg"),
            ],
            datablock=astronomic_block,
        )
        return astronomic_model


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
        time_unit: str,
        time_interpolation: str = "linear",
        units: List[str] = None,
        user_defined_names: List[str] = None,
    ) -> List[TimeSeries]:
        """
        Convert a TimModel into a ForcingModel.

        Args:
            tim_model (TimModel):
                The input TimModel to be converted.
            time_unit (str):
                Formatted string containing the units of time, including absolute datetime reference information
                (according to UDunits). For example, "minutes since 1992-10-8 15:15:42.5 -6:00".
            time_interpolation (str, optional):
                The time interpolation method for the forcing data. Defaults to "linear".
            units (List[str], optional):
                A list of units corresponding to the forcing quantities.
            user_defined_names (List[str], optional):
                A list of user-defined names for the forcing blocks.

        Returns:
            TimeSeries:
                The converted TimeSeries.

        Raises:
            ValueError: If `units` and `user_defined_names` are not provided.
            ValueError: If the lengths of `units`, `user_defined_names`, and the columns in the first row of the TimModel
                do not match.

        Examples:
            ```python
            >>> from hydrolib.core.dflowfm.tim.models import TimModel
            >>> from hydrolib.tools.extforce_convert.converters import TimToForcingConverter
            >>> file_path = "tests/data/input/tim/single_data_for_timeseries.tim"
            >>> user_defined_names = ["discharge"]
            >>> tim_model = TimModel(file_path, user_defined_names)
            >>> print(tim_model.as_dict())
            {'discharge': [0.0, 0.01, 0.0, -0.01, 0.0, 0.01, 0.0, -0.01, 0.0, 0.01, 0.0, -0.01, 0.0]}
            >>> converter = TimToForcingConverter()
            >>> time_series = converter.convert(
            ...     tim_model, "minutes since 2015-01-01 00:00:00", "linear", ["m3/s"], ["discharge"]
            ... )
            >>> print(time_series[0].name)
            discharge
            >>> print(time_series[0].datablock)
            [[0.0, 0.0], [10.0, 0.01], [20.0, 0.0], [30.0, -0.01], [40.0, 0.0], [50.0, 0.01], [60.0, 0.0], [70.0, -0.01], [80.0, 0.0], [90.0, 0.01], [100.0, 0.0], [110.0, -0.01], [120.0, 0.0]]

            ```
        """
        if units is None or user_defined_names is None:
            raise ValueError("Both 'units' and 'user_defined_names' must be provided.")

        if time_unit is None:
            raise ValueError("The 'start_time' must be provided.")

        first_record = tim_model.timeseries[0].data
        if len(units) != len(user_defined_names) != len(first_record):
            raise ValueError(
                "The lengths of 'units', 'user_defined_names' and length of the columns in the first row must match."
            )

        df = tim_model.as_dataframe()
        time_data = df.index.tolist()
        time_series_list = []
        for i, (column, vals) in enumerate(df.items()):
            unit = units[i]
            forcing = TimeSeries(
                name=user_defined_names[i],
                function="timeseries",
                timeinterpolation=time_interpolation,
                quantityunitpair=[
                    QuantityUnitPair(quantity="time", unit=time_unit),
                    QuantityUnitPair(quantity=column, unit=unit),
                ],
                datablock=[[i, j] for i, j in zip(time_data, vals.values.tolist())],
            )

            time_series_list.append(forcing)

        return time_series_list


class T3DToForcingConverter:
    """T3D to Forcing Converter."""

    @staticmethod
    def convert(
        t3d_models: List[T3DModel],
        quantities_names: List[str],
        user_defined_names: List[str] = None,
    ) -> List[T3D]:
        """Convert a list of T3DModel into a list of T3D Forcing to be saved into the .bc file."""
        t3d_forcings = []
        for label, model in zip(user_defined_names, t3d_models):
            model.quantities_names = quantities_names
            t3d = T3DToForcingConverter.convert_t3d_model(model, label)
            t3d_forcings.append(t3d)

        return t3d_forcings

    @staticmethod
    def convert_t3d_model(
        t3d_model: T3DModel,
        user_defined_name: List[str] = None,
    ) -> T3D:
        """Convert a T3DModel into a T3D Forcing to be saved into the .bc file.

        Args:
            t3d_model(T3DModel):
                T3DModel representing the .t3d file model.
            user_defined_name (List[str], optional):
                user-defined name for the forcing block.

        Returns:
            T3D: The converted T3D object.

        Examples:
            ```python
            >>> from hydrolib.core.dflowfm.t3d.models import T3DModel, T3DTimeRecord
            >>> from hydrolib.tools.extforce_convert.converters import T3DToForcingConverter
            >>> from hydrolib.core.dflowfm.bc.models import QuantityUnitPair, T3D
            >>> t3d_model = T3DModel(
            ...     layer_type="SIGMA",
            ...     layers=[0.0, 0.1, 0.2, 0.3, 0.4],
            ...     records = [
            ...         T3DTimeRecord(time="0 seconds since 2006-01-01 00:00:00 +00:00", data=[5.0, 5.0, 10.0, 10.0]),
            ...         T3DTimeRecord(time="1e9 seconds since 2001-01-01 00:00:00 +00:00", data=[5.0, 5.0, 10.0, 10.0])
            ...     ],
            ...     quantities_names=["temperature", "salinity", "discharge", "any quantity"]
            ... )
            >>> converter = T3DToForcingConverter()
            >>> t3d_forcing = converter.convert_t3d_model(t3d_model,"sigma-5-layers-time-steps")
            >>> print(t3d_forcing.name)
            sigma-5-layers-time-steps
            >>> print(t3d_forcing.function)
            t3d
            >>> print(t3d_forcing.datablock)
            [[0.0, 5.0, 5.0, 10.0, 10.0], [1000000000.0, 5.0, 5.0, 10.0, 10.0]]
            >>> print(t3d_forcing.quantityunitpair) # doctest: +SKIP
            [
                QuantityUnitPair(quantity='time', unit='seconds since 2006-01-01 00:00:00 +00:00', vertpositionindex=None),
                QuantityUnitPair(quantity='temperature', unit='degC', vertpositionindex=1),
                QuantityUnitPair(quantity='salinity', unit='ppt', vertpositionindex=2),
                QuantityUnitPair(quantity='discharge', unit='m3/s', vertpositionindex=3)
            ]
            >>> print(t3d_forcing.vertpositions)
            [0.0, 0.1, 0.2, 0.3, 0.4]
            >>> print(t3d_forcing.vertpositiontype)
            percBed

            ```
        """
        data = {
            "name": user_defined_name,
            "vertpositions": t3d_model.layers,
            "vertpositiontype": "percBed",
        }
        data_dict = t3d_model.as_dict()
        updated = [[k] + v for k, v in data_dict.items()]
        data["datablock"] = updated

        time_unit = t3d_model.records[0].time_unit
        ref_date = t3d_model.records[0].reference_date
        quantities_list = [
            QuantityUnitPair(quantity="time", unit=f"{time_unit} since {ref_date}")
        ]

        units = t3d_model.get_units()
        quantities_names = t3d_model.quantities_names
        for i, (quantity, unit) in enumerate(zip(quantities_names, units)):
            quantities_list.append(
                QuantityUnitPair(quantity=quantity, unit=unit, vertpositionindex=i + 1)
            )

        data["quantityunitpair"] = quantities_list

        t3d = T3D(**data)
        return t3d
