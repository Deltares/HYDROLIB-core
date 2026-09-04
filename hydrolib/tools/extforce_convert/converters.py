"""External forcing converter."""

from __future__ import annotations
import os
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from hydrolib.core.base.file_manager import PathOrStr, resolve_relative_to_root
from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.common.models import Operand
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
    SOURCE_SINKS_IGNORE_QUANTITIES_PREFIXES,
    SOURCE_SINKS_QUANTITIES_VALID_PREFIXES,
    Boundary,
    BoundaryError,
    Spatial,
    SpatialError,
    Lateral,
    LateralError,
    SourceSink,
    SourceSinkError,
)
from hydrolib.core.dflowfm.extold.models import (
    ExtOldBoundaryQuantity,
    ExtOldForcing,
    ExtOldInitialConditionQuantity,
    ExtOldLateralQuantity,
    ExtOldMeteoQuantity,
    ExtOldParametersQuantity,
    ExtOldSourcesSinks,
)
from hydrolib.core.dflowfm.inifield.models import DataFileType, InterpolationMethod
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.substance.models import Substance, SubstanceModel
from hydrolib.core.dflowfm.t3d.models import T3DModel
from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.core.dflowfm.tim.parser import TimParser
from hydrolib.tools.extforce_convert.utils import (
    CONVERTER_DATA,
    SOURCESINK_SALINITY_IN_BC,
    SOURCESINK_TEMP_IN_BC,
    convert_interpolation_data,
    find_temperature_salinity_in_quantities,
    old_layer_to_target_layer,
    oldfiletype_to_forcing_file_type,
)

if TYPE_CHECKING:
    from hydrolib.tools.extforce_convert.mdu_parser import MDUParser


FACTOR_QUANTITIES = frozenset(
    {
        "windspeedfactor",
        "solarradiationfactor",
    }
)


class BaseConverter(ABC):
    """Abstract base class for converting old external forcings blocks to new blocks.

    Subclasses must implement the `convert` method, specific for the
    type of model data in the various old external forcing blocks.

    Class ConverterFactory uses these subclasses to create the correct
    converter, depending on the quantity of the forcing block.
    """

    def __init__(self, root_dir: PathOrStr = None):
        """Initialize the BaseConverter object.

        Args:
            root_dir (PathOrStr, optional):
                Root directory used to resolve the forcing file paths. Only the
                converters that read forcing files from disk (boundary conditions and
                source/sinks) need it. Defaults to None.
        """
        self._root_dir = Path(root_dir) if isinstance(root_dir, str) else root_dir
        self._legacy_files = []

    @property
    def root_dir(self) -> Path:
        """Get the root directory of the external forcing files."""
        return self._root_dir

    @root_dir.setter
    def root_dir(self, value: Union[Path, str]):
        if isinstance(value, str):
            value = Path(value)
        self._root_dir = value

    @property
    def legacy_files(self) -> List[Path]:
        return self._legacy_files

    @legacy_files.setter
    def legacy_files(self, value: Union[PathOrStr, List[PathOrStr]]):
        """Set the legacy files to be cleaned up after conversion."""
        if isinstance(value, list):
            self._legacy_files += [Path(file) for file in value]
        else:
            self._legacy_files += [Path(value)]

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


class SpatialBlockBuilder:
    """Assemble the constructor dict for a single `Spatial` block.

    A method object for the old-to-new spatial conversion: the source forcing and
    its resolved data-file path are held as state so the build steps cooperate
    through `self` (reading `self.forcing`, mutating `self.block`) instead of
    threading them as parameters. `SpatialConverter.convert` drives it via
    `SpatialBlockBuilder(forcing, path).build()`.
    """

    def __init__(self, forcing: ExtOldForcing, new_forcing_path: Path | None):
        """Capture the source forcing and derive the quantity name and file type.

        Args:
            forcing (ExtOldForcing):
                The old external forcing block being converted.
            new_forcing_path (Path | None):
                The path to the forcing data file in the new model.
        """
        self.forcing = forcing
        self.new_forcing_path = new_forcing_path

        quantity_str = str(forcing.quantity).lower()
        self._is_factor = quantity_str in FACTOR_QUANTITIES

        self.quantity_name = CONVERTER_DATA.external_forcing.rename_quantity(
            forcing.quantity
        )
        self.file_type = oldfiletype_to_forcing_file_type(forcing.filetype)
        self.block: Dict[str, Any] = {}

    def build(self) -> Dict[str, Any]:
        """Assemble and return the `Spatial` constructor dict.

        Returns:
            Dict[str, Any]: the keyword arguments for the `Spatial` constructor.
        """
        self._require_no_sourcemask()
        self._set_representation()
        self._set_common_fields()
        return self.block

    def _require_no_sourcemask(self):
        """Reject the removed `SOURCEMASK` attribute, which has no new equivalent."""
        if self.forcing.sourcemask != DiskOnlyFileModel(None):
            raise ValueError(
                f"Attribute 'SOURCEMASK' is no longer supported, cannot "
                f"convert this input. Encountered for QUANTITY="
                f"{self.forcing.quantity} and FILENAME={self.forcing.filename}."
            )

    def _set_operand(self) -> Operand:
        """Return the operand for the new Spatial block.

        Factor quantities (``windspeedfactor``, ``solarradiationfactor``) are
        always converted with ``operand = multiply``, regardless of the operand
        value recorded in the old external forcings file.

        Returns:
            Operand: ``Operand.multiply`` for factor quantities, otherwise the
                operand value as parsed from the old external forcings block.
        """
        if self._is_factor:
            operand = Operand.multiply
        else:
            operand = self.forcing.operand
        return operand

    def _set_representation(self):
        """Populate `self.block` with the spatial representation for this forcing.

        There are three mutually exclusive representations:

        - A polygon quantity (except `initialvertical*`) becomes a constant value
          masked by the polygon: `targetMaskFile=*.pol` + `dataValue` +
          `interpolationMethod=constant` (the idiom documented on `Spatial.dataValue`).
        - An `initialvertical*` polygon keeps the polygon as its `dataFile`.
        - Any other quantity is a gridded data file, carrying the interpolation /
          averaging settings, operand, extrapolation toggle and tracer fields.

        UNST-9218 / GitHub #1104: `initialvertical*` quantities must always use
        `interpolationMethod=constant`; the old `METHOD` value (typically 3 →
        linearSpaceTime) is meaningless for vertical profiles, since the kernel
        always applies constant (horizontal) + linear (vertical) interpolation.
        """
        is_polygon = self.file_type == DataFileType.polygon
        is_initial_vertical = self.quantity_name.startswith("initialvertical")
        if is_polygon and not is_initial_vertical:
            self.block = {
                "quantity": self.quantity_name,
                "targetmaskfile": DiskOnlyFileModel(self.new_forcing_path),
                "datavalue": self.forcing.value,
                "operand": self._set_operand(),
                "interpolationmethod": InterpolationMethod.constant,
            }
        elif is_polygon:
            self.block = {
                "quantity": self.quantity_name,
                "datafile": DiskOnlyFileModel(self.new_forcing_path),
                "datafiletype": self.file_type,
                "interpolationmethod": InterpolationMethod.constant,
                "operand": self._set_operand(),
            }
        else:
            self.block = {
                "quantity": self.quantity_name,
                "datafile": DiskOnlyFileModel(self.new_forcing_path),
                "datafiletype": self.file_type,
            }
            self.block = convert_interpolation_data(self.forcing, self.block)
            if is_initial_vertical:
                self.block["interpolationmethod"] = InterpolationMethod.constant
            self.block["operand"] = self._set_operand()
            self.block["extrapolationallowed"] = bool(
                self.forcing.extrapolation_method
            )
            self._add_tracers()

    def _add_tracers(self):
        """Copy any `tracer*` fields set on the forcing into the block unchanged."""
        for key, value in self.forcing.model_dump().items():
            if key.lower().startswith("tracer") and value is not None:
                self.block[key] = value

    def _set_common_fields(self):
        """Add the fields shared by every representation: variable name and layer.

        `VARNAME` maps to `dataVariableName`; the old `LAYER` maps to the new
        `targetLayer` (`-1` → bottom, `0` → all, positive kept).
        """
        if self.forcing.varname is not None:
            self.block["datavariablename"] = self.forcing.varname
        if self.forcing.layer is not None:
            self.block["targetlayer"] = old_layer_to_target_layer(self.forcing.layer)


class SpatialConverter(BaseConverter):
    """Spatial quantities Converter."""

    def __init__(self):
        """Spatial converter constructor."""
        super().__init__()

    def convert(self, forcing: ExtOldForcing, new_forcing_path: Path = None) -> Spatial:
        """Spatial converter.

        Convert an old external forcing block with spatial data to a Spatial
        forcing block suitable for inclusion in a new external forcings file.

        This function takes a forcing block from an old external forcings
        file, represented by an instance of ExtOldForcing, and converts it
        into a Spatial object. The Spatial object is suitable for use in new
        external forcings files, adhering to the updated format and
        specifications.

        Args:
            forcing (ExtOldForcing):
                The contents of a single forcing block
                in an old external forcings file. This object contains all the
                necessary information, such as quantity, values, and timestamps,
                required for the conversion process.
            new_forcing_path (Path):
                The updated path to the forcing data file.

        Returns:
            Spatial: A Spatial object that represents the converted forcing
            block, ready to be included in a new external forcings file.

        Raises:
            ValueError: If the forcing block contains a quantity that is not
            supported by the converter, a ValueError is raised.
        """
        data = SpatialBlockBuilder(forcing, new_forcing_path).build()

        try:
            spatial_block = Spatial(**data)
        except Exception as e:
            raise SpatialError(
                f"Failed to create the Spatial object. for the following Errors: {e}"
            )
        return spatial_block


class BoundaryConditionConverter(BaseConverter):
    """Boundary condition converter."""

    def __init__(self, mdu_parser: MDUParser = None, root_dir: PathOrStr = None):
        """Boundary condition converter constructor.

        Args:
            mdu_parser (MDUParser, optional):
                Parser for the FM model. Required at `convert` time: the boundary
                condition conversion needs the reference time the parser exposes.
                Defaults to None.
            root_dir (PathOrStr, optional):
                Root directory used to resolve the forcing file paths. Defaults to None.
        """
        super().__init__(root_dir=root_dir)
        self._mdu_parser = mdu_parser

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

        # switch the quantity names from the Tim model (loction names) to quantity names.
        user_defined_names = BoundaryConditionConverter._get_file_labels(
            label, tim_files
        )
        tim_model.quantities_names = [quantity] * len(tim_model.get_units())

        units = tim_model.get_units()
        time_series_list = TimToForcingConverter.convert(
            tim_model, time_unit, time_interpolation, units, user_defined_names
        )
        return time_series_list

    def locate_files(self, location_file: Path):
        """Locate the tim, t3d, and cmp files related to the location file.

        Args:
            location_file(Path):
                the pli file that contains the location of the boundary condition.

        Returns:
            tim_files (List[Path]):
                list of all the tim files related to the location file.
            t3d_files (List[Path]):
                list of all the t3d files related to the location file.
            cmp_files (List[Path]):
                list of all the cmp files related to the location file.
        """
        forcings_local_dir = resolve_relative_to_root(location_file, self.root_dir)
        FILE_NUMBERING_PATTERN = "[0-9][0-9][0-9][0-9]*"
        stem_pattern = f"{location_file.stem}_{FILE_NUMBERING_PATTERN}"
        tim_files = list(forcings_local_dir.parent.glob(f"{stem_pattern}.tim"))
        t3d_files = list(forcings_local_dir.parent.glob(f"{stem_pattern}.t3d"))
        cmp_files = list(forcings_local_dir.parent.glob(f"{stem_pattern}.cmp"))
        return tim_files, t3d_files, cmp_files

    def convert(self, forcing: ExtOldForcing) -> Boundary:
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

        Note:
            The reference time is derived from the `MDUParser` injected at construction
            (see `__init__`), so `convert` needs no separate `time_unit` argument.

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
            - Since the reference time is read from the mdu file, boundary conditions can only be converted when an
            `MDUParser` was injected at construction; the external forcing file alone is not enough.
            - The new labels for all quantities in the .bc file will be taken from the pli file and the number at the
            end of the label is taken from the file name of the tim, t3d, or cmp files.
        """
        if (
            self._mdu_parser is None
            or self._mdu_parser.temperature_salinity_data is None
        ):
            raise ValueError("MDU model is required to convert Boundary conditions.")
        time_unit = self._mdu_parser.temperature_salinity_data.get("refdate")

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

        tim_files, t3d_files, cmp_files = self.locate_files(location_file)
        forcings_list = []

        if len(tim_files) > 0:
            time_series_list = self.convert_tim_to_bc(
                tim_files, time_unit, quantity=quantity, label=label
            )
            forcings_list.extend(time_series_list)
            self.legacy_files = tim_files

        # check t3d files
        if len(t3d_files) > 0:
            t3d_forcing_list = self._convert_t3d_files(t3d_files, quantity, label)
            forcings_list.extend(t3d_forcing_list)
            self.legacy_files = t3d_files

        # check cmp files
        if len(cmp_files) > 0:
            forcing_list = self._convert_cmp_files(cmp_files, quantity, label)
            forcings_list.extend(forcing_list)
            self.legacy_files = cmp_files

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

    @staticmethod
    def _convert_t3d_files(
        t3d_files: List[Path], quantity: str, label: str
    ) -> List[T3D]:
        """Convert T3D files to T3D forcing objects.

        Args:
            t3d_files (List[Path]):
                t3d files to be converted.
            quantity (str):
                quantity name that the t3d files represent.
            label (str):
                label from the pli file to be used to name the time series sections in the .bc model.

        Returns:
            List[T3D]:
                A list of T3D objects representing the converted T3D files.
        """
        t3d_models = [T3DModel(path) for path in t3d_files]
        # this line assumed that the two t3d files will have the same number of layers and same number of quantities
        quantities_names = [quantity] * t3d_models[0].size[1]
        user_defined_names = BoundaryConditionConverter._get_file_labels(
            label, t3d_files
        )
        t3d_forcing_list = T3DToForcingConverter.convert(
            t3d_models, quantities_names, user_defined_names
        )
        return t3d_forcing_list

    @staticmethod
    def _convert_cmp_files(
        cmp_files: List[Path], quantity: str, label: str
    ) -> List[ForcingBase]:
        """Convert CMP files to ForcingModel.

        Args:
            cmp_files (List[Path]):
                List of CMP files to be converted.
            quantity (str):
                quantity name that the cmp files represent.
            label (str):
                label from the pli file names to be used to name the time series sections in the .bc model.

        Returns:
            List[ForcingBase]:
                The converted ForcingBase object.
        """
        cmp_models = [CMPModel(path) for path in cmp_files]
        user_defined_names = BoundaryConditionConverter._get_file_labels(
            label, cmp_files
        )

        for cmp_model in cmp_models:
            cmp_model.quantities_name = [quantity]
        forcing_list = CMPToForcingConverter.convert(cmp_models, user_defined_names)
        return forcing_list

    @staticmethod
    def _get_file_labels(label: str, files: List[Path]) -> List[str]:
        """
        Get the labels of the files based on their filenames and a provided label.

        Args:
            label (str):
                A string label to prefix the generated file labels.
            files (List[Path]):
                A list of file paths. Each file's name is expected to end with '_<number>',
                where <number> is an integer used to generate the labels.

        Returns:
            List[str]:
                A list of strings representing the labels for the files. Each label is
                generated by appending '_<number>' (zero-padded to 4 digits) to the provided label.

        Assumptions:
            - Filenames must end with '_<number>', where <number> is an integer.
            - The method extracts this integer from the filename to generate the labels.
        """
        try:
            file_int = [file.stem.split("_")[-1] for file in files]
            file_int_id = [int(i) for i in file_int]
        except ValueError:
            raise ValueError(
                f"Cannot get the file number from the file name. file name should be <NAME>_<INT-NUMBER> "
                f"Please check the file names: {files}"
            )
        user_defined_names = [f"{label}_{str(i).zfill(4)}" for i in file_int_id]
        return user_defined_names


class SourceSinkConverter(BaseConverter):
    """Source and sink converter."""

    def __init__(self, mdu_parser: MDUParser = None, root_dir: PathOrStr = None):
        """Source and sink converter constructor.

        Args:
            mdu_parser (MDUParser, optional):
                Parser for the FM model. Required at `convert` time: the source and
                sink conversion needs the substance file and the temperature/salinity
                settings the parser exposes. Defaults to None.
            root_dir (PathOrStr, optional):
                Root directory used to resolve the forcing file paths. Defaults to None.
        """
        super().__init__(root_dir=root_dir)
        self._mdu_parser = mdu_parser

    def _active_substances(self) -> Optional[List[Substance]]:
        """Read the active substances from the MDU's `SubstanceFile`.

        Each returned `Substance` carries both its `name` and its
        `concentration_unit`, so callers can derive the substance names as well as
        the units to apply to the source/sink `.bc` quantities.

        Returns:
            Optional[List[Substance]]:
                The active substance definitions, or None when the MDU file does
                not reference a substance file.

        Raises:
            FileNotFoundError:
                If the MDU references a substance file that does not exist.
        """
        substances = None
        substance_file = self._mdu_parser.get_keyword("SubstanceFile")
        if substance_file:
            substance_path = (
                self._mdu_parser.mdu_path.parent / substance_file
            ).resolve()
            if not substance_path.exists():
                raise FileNotFoundError(
                    f"Substance file {substance_path} not found, required to convert "
                    f"SourceSink quantities."
                )
            substance_model = SubstanceModel(substance_path)
            substances = substance_model.get_active_substances()
        return substances

    def _resolve_active_substances(
        self,
    ) -> Tuple[Optional[List[str]], Dict[str, str]]:
        """Read the active substances and derive the names and concentration-unit map.

        Returns:
            Tuple[Optional[List[str]], Dict[str, str]]:
                The active substance names (or None when the MDU references no substance
                file), and a mapping of substance name to concentration unit (empty when
                there are none).
        """
        active_substances = self._active_substances()
        names = [s.name for s in active_substances] if active_substances else None
        units = (
            {s.name: s.concentration_unit for s in active_substances}
            if active_substances
            else {}
        )
        return names, units

    @staticmethod
    def filter_source_sink_quantities(quantities: List[str]) -> List[str]:
        """Keep only the quantities relevant to the source and sink conversion.

        Quantities starting with a source/sink ignore prefix (e.g. `initialtracer`,
        `initialsedfrac`) are converted as initial conditions by other converters, so
        they must not be counted as source/sink columns.

        Args:
            quantities (List[str]):
                All quantities present in the old external forcings file.

        Returns:
            List[str]:
                The quantities that are not carrying a source/sink ignore prefix.
        """
        return [
            quantity
            for quantity in quantities
            if not quantity.lower().startswith(SOURCE_SINKS_IGNORE_QUANTITIES_PREFIXES)
        ]

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
            if SOURCESINK_TEMP_IN_BC in keys and SOURCESINK_SALINITY_IN_BC in keys:
                keys.remove(SOURCESINK_SALINITY_IN_BC)
                keys.insert(
                    keys.index(SOURCESINK_TEMP_IN_BC),
                    SOURCESINK_SALINITY_IN_BC,
                )
        else:
            keys = list(temp_salinity_from_ext.keys())

        return keys

    def parse_tim_model(
        self,
        tim_file: Path,
        ext_file_quantity_list: List[str],
        active_substance_names: List[str] = None,
        **mdu_quantities,
    ) -> TimModel:
        """Parse the source and sinks related time series from the tim file.

        - Parse the TIM file and extract the time series data for each column.
        - assign the time series data to the corresponding quantity name.

        The order of the quantities in the tim file should be as follows:
        - time
        - sourcesink_discharge
        - sourcesink_salinity (optional)
        - sourcesink_temperature (optional)
        - tracer<anyname>delta (optional)
        - any other quantities from the external forcings file.

        Args:
            tim_file (Path): The path to the TIM file.
            ext_file_quantity_list (List[str]): A list of other quantities that are present in the external forcings file.
            active_substance_names (List[str], default is None):
                A list of active substance names to include in the conversion.
                When provided, only the substances in this list will be processed.
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
            ```python
            >>> from pathlib import Path
            >>> from hydrolib.tools.extforce_convert.converters import SourceSinkConverter
            >>> tim_file = Path("tests/data/input/source-sink/leftsor.tim")
            >>> converter = SourceSinkConverter()
            >>> tim_model = converter.parse_tim_model(tim_file, ext_file_quantity_list)
            >>> print(tim_model.quantities_names)
            ['sourcesink_discharge', 'sourcesink_salinity', 'sourcesink_temperature', 'initialtracerAnyname']
            >>> print(tim_model.as_dict()) # doctest: +SKIP
            {
                "discharge": [1.0, 1.0, 1.0, 1.0, 1.0],
                "sourcesink_salinity": [2.0, 2.0, 2.0, 2.0, 2.0],
                "sourcesink_temperature": [3.0, 3.0, 3.0, 3.0, 3.0],
                "initialtracerAnyname": [4.0, 4.0, 4.0, 4.0, 4.0],
            }

            ```

        mdu file:
            ```ini
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
            if key.lower().startswith(SOURCE_SINKS_QUANTITIES_VALID_PREFIXES)
        ]
        # Remove duplicate quantities that might be present in the list due to quantities that share names,
        # therefore occurring multiple times in the external forcing file.
        # TimeSeries columns are expected to be linked to unique quantity names.
        required_quantities_from_ext = list(set(required_quantities_from_ext))

        # check if the temperature and salinity are present in the external file
        temp_salinity_from_ext = find_temperature_salinity_in_quantities(
            ext_file_quantity_list
        )

        final_temp_salinity = self.merge_mdu_and_ext_file_quantities(
            mdu_quantities, temp_salinity_from_ext
        )
        active_substance_names = active_substance_names or []

        final_quantities_list = (
            ["sourcesink_discharge"]
            + final_temp_salinity
            + required_quantities_from_ext
            + active_substance_names
        )

        if len(time_series) != len(final_quantities_list):
            raise ValueError(
                f"Number of columns in the TIM file '{tim_file}: {len(time_series)}' does not match the number of "
                f"quantities in the external forcing file: {final_quantities_list}."
            )
        # assign the quantity names to the tim model
        tim_model.quantities_names = final_quantities_list
        return tim_model

    @staticmethod
    def convert_tim_to_bc(
        tim_model: TimModel,
        time_unit: str,
        user_defined_names: List[str] = None,
        substance_units: Dict[str, str] = None,
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
            substance_units (Dict[str, str], optional):
                Mapping of substance name to its concentration unit. When provided, the
                placeholder unit (``"-"``) that `TimModel.get_units` assigns to substance
                columns is replaced with the substance's concentration unit.

        Returns:
            ForcingModel: The converted ForcingModel.

        Raises:
            ValueError: If `units` and `user_defined_names` are not provided.
            ValueError: If the lengths of `units`, `user_defined_names`, and the columns in the first row of the TimModel
        """
        units = tim_model.get_units()
        units = SourceSinkConverter._correct_substance_units(
            units, tim_model.quantities_names, substance_units
        )
        time_series_list = TimToForcingConverter.convert(
            tim_model, time_unit, units=units, user_defined_names=user_defined_names
        )
        forcing_model = ForcingModel(forcing=time_series_list)
        return forcing_model

    @staticmethod
    def _correct_substance_units(
        units: List[str],
        quantities_names: List[str],
        substance_units: Dict[str, str] = None,
    ) -> List[str]:
        """Replace the placeholder unit of substance columns with their concentration unit.

        `TimModel.get_units` maps any column that is not discharge/waterlevel/salinity/
        temperature to the placeholder ``"-"``. Substance columns fall into that bucket,
        so this method overrides those placeholders with the concentration unit declared
        in the substance file. Units are aligned with `quantities_names` positionally.

        Args:
            units (List[str]): The units extracted from the TIM model, one per quantity.
            quantities_names (List[str]): The quantity names, aligned with `units`.
            substance_units (Dict[str, str], optional): Mapping of substance name to
                concentration unit. When falsy, `units` is returned unchanged.

        Returns:
            List[str]: The units with substance placeholders corrected.
        """
        result = units
        if substance_units:
            result = [
                substance_units.get(name.removeprefix("sourcesink_"), unit)
                for name, unit in zip(quantities_names, units)
            ]
        return result

    @staticmethod
    def separate_forcing_model(forcing_model: ForcingModel) -> Dict[str, ForcingModel]:
        """Separate the forcing model into a list of forcing models.

        each forcing model will contain only one forcing quantity.
        """
        forcing_list = [deepcopy(forcing) for forcing in forcing_model.forcing]

        forcings = {}
        for forcing in forcing_list:
            model = deepcopy(forcing_model)
            model.forcing = [forcing]
            name = forcing.quantityunitpair[1].quantity
            # remove the prefix 'sourcesink_' from the name as the extforce file will not have this prefix.
            forcings[name.removeprefix("sourcesink_")] = model

        return forcings

    def _resolve_tim_file(self, polyline: PolyFile, quantity: str) -> Path:
        """Resolve the TIM file that accompanies the source/sink polyline.

        The TIM file is expected to sit next to the polyline, sharing its stem with a
        `.tim` suffix, resolved relative to the converter's `root_dir`.

        Args:
            polyline (PolyFile): The source/sink polyline whose filepath locates the
                accompanying TIM file.
            quantity (str): The old external forcing quantity, used only for the error
                message when the TIM file is missing.

        Returns:
            Path: The resolved path to the existing TIM file.

        Raises:
            ValueError: If the resolved TIM file does not exist.
        """
        tim_file = resolve_relative_to_root(
            polyline.filepath, self.root_dir
        ).with_suffix(".tim")
        if not tim_file.exists():
            raise ValueError(f"TIM file '{tim_file}' not found for QUANTITY={quantity}")
        return tim_file

    def convert(
        self,
        forcing: ExtOldForcing,
        ext_file_quantity_list: List[str] = None,
    ) -> SourceSink:
        """Source and sink converter.

        Convert an old external forcing block with Sources and sinks to a SourceSink
        forcing block suitable for inclusion in a new external forcings file.

        Args:
            forcing (ExtOldForcing): The contents of a single forcing block in an old external forcings file. This
                object contains all the necessary information, such as quantity, values, and timestamps, required for the
                conversion process.
            ext_file_quantity_list (List[str], default is None): A list of other quantities that are present in the
                external forcings file. The caller is expected to pass the quantities relevant to the source/sink
                conversion; this method does not filter the list itself.

        Note:
            The start time, the active substance names, and the temperature/salinity settings are derived from the
            `MDUParser` injected at construction (see `__init__`), so `convert` needs no separate arguments for them.

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
        if (
            self._mdu_parser is None
            or self._mdu_parser.temperature_salinity_data is None
        ):
            raise ValueError("MDU model is required to convert SourceSink quantities.")

        temp_salinity_mdu = self._mdu_parser.temperature_salinity_data
        start_time = temp_salinity_mdu.get("refdate")
        active_substance_names, substance_units = self._resolve_active_substances()

        location_file = forcing.filename.filepath
        polyline = forcing.filename
        location_name = location_file.stem
        z_source, z_sink = polyline.get_z_sources_sinks()

        tim_file = self._resolve_tim_file(polyline, forcing.quantity)
        self.legacy_files = tim_file

        tim_model = self.parse_tim_model(
            tim_file,
            ext_file_quantity_list,
            active_substance_names,
            **temp_salinity_mdu,
        )
        labels = [f"{location_name}"] * len(tim_model.quantities_names)

        forcing_model = self.convert_tim_to_bc(
            tim_model,
            start_time,
            user_defined_names=labels,
            substance_units=substance_units,
        )
        # set the bc file names to the same names as the tim files.
        forcing_model.filepath = Path(
            os.path.relpath(tim_file, self.root_dir.resolve())
        ).with_suffix(".bc")

        data = {
            "id": location_name,
            "name": forcing.quantity,
            "numcoordinates": len(polyline.x),
            "xcoordinates": polyline.x,
            "ycoordinates": polyline.y,
        }
        if forcing.area is not None:
            data["area"] = forcing.area
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
            new_block = SourceSink(dynamic_fields=active_substance_names, **data)
        except Exception as e:  # pragma: no cover
            raise SourceSinkError(
                f"Failed to create the SourceSink object. for the following Errors: {e}"
            )

        return new_block


class LateralConverter(BaseConverter):
    """Lateral discharge converter."""

    _QUANTITY_TO_LOCATION_TYPE = {
        "lateraldischarge": None,
        "lateraldischarge1d": "1d",
        "lateraldischarge2d": "2d",
    }

    def __init__(self, root_dir: PathOrStr = None, mdu_parser=None):
        """Lateral converter constructor.

        Args:
            root_dir (PathOrStr, optional): Root directory used to resolve file paths.
            mdu_parser (MDUParser, optional): MDU parser used to obtain the reference
                date (time_unit) required when converting time-series discharge from
                a TIM file. When *None*, the ``time_unit`` argument of :meth:`convert`
                must be supplied manually.
        """
        super().__init__(root_dir=root_dir)
        self._mdu_parser = mdu_parser

    def convert(
        self, forcing: ExtOldForcing, time_unit: str | None = None
    ) -> Lateral:
        """Lateral discharge converter.

        Convert an old external forcing block with lateral discharge data to a
        Lateral forcing block suitable for inclusion in a new external forcings file.

        This function takes a forcing block from an old external forcings
        file, represented by an instance of ExtOldForcing, and converts it
        into a Lateral object. The Lateral object is suitable for use in new
        external forcings files, adhering to the updated format and
        specifications.

        Args:
            forcing (ExtOldForcing): The contents of a single forcing block
                in an old external forcings file. This object contains all the
                necessary information, such as quantity, values, and timestamps,
                required for the conversion process.
            time_unit (Optional[str]):
                Formatted string containing the units of time, including absolute
                datetime reference information (according to UDunits). For example,
                "minutes since 1992-10-8 15:15:42.5 -6:00". Required when the
                discharge is given as a time series.

        Returns:
            Lateral: A Lateral object that represents the converted forcing
            block, ready to be included in a new external forcings file.

        Raises:
            ValueError: If the forcing block contains a quantity that is not
                supported by the converter.
            LateralError: If the Lateral object could not be created.
        """
        quantity = str(forcing.quantity).lower()
        if quantity not in self._QUANTITY_TO_LOCATION_TYPE:
            raise ValueError(f"Unsupported lateral quantity: {forcing.quantity}")
        location_type = self._QUANTITY_TO_LOCATION_TYPE[quantity]

        # Determine discharge and location data
        discharge = self._get_discharge(forcing, self._get_time_unit(time_unit))
        location_data = self._get_location_data(forcing)

        data = {
            "id": location_data.pop("id"),
            "name": forcing.quantity
        }
        if location_type is not None:
            data["locationtype"] = location_type
        data.update(location_data)
        data["discharge"] = discharge

        try:
            new_block = Lateral(**data)
        except Exception as e:
            raise LateralError(
                f"Failed to create the Lateral object for the following errors: {e}"
            )

        return new_block

    def _get_time_unit(self, time_unit: str | None) -> str | None:
        """Return *time_unit*, falling back to the MDU reference date when available."""
        result = time_unit
        if result is None and self._mdu_parser is not None:
            temperature_salinity_data = self._mdu_parser.temperature_salinity_data
            if temperature_salinity_data is not None:
                result = temperature_salinity_data.get("refdate")
        return result

    def _resolve_tim_file(self, polyline: PolyFile, quantity: str) -> TimModel | None:
        """Resolve and merge any TIM files accompanying the lateral polyline.

        Searches the directory next to the polyline file for any ``.tim`` files
        whose stem starts with the polyline stem (e.g. ``lateral.tim``,
        ``lateral_0001.tim``, ``lateral_0002.tim``, …), merges them into a
        single `TimModel` via
        :meth:`BoundaryConditionConverter.merge_tim_files`, and sets every
        column's quantity name to ``"discharge"``.

        The matched file paths are also appended to :attr:`legacy_files` so they
        can be cleaned up after the conversion.

        Args:
            polyline (PolyFile): The lateral polyline whose filepath locates the
                accompanying TIM file(s).
            quantity (str): The old external forcing quantity, used only in the
                error message raised by :meth:`BoundaryConditionConverter.merge_tim_files`
                when a listed file is missing.

        Returns:
            Optional[TimModel]: The merged `TimModel` (with ``quantities_names``
                set to ``"discharge"`` for every column), or ``None`` when no
                ``.tim`` files are found next to the polyline.
        """
        resolved = resolve_relative_to_root(polyline.filepath, self.root_dir)
        stem = polyline.filepath.stem
        tim_files = sorted(resolved.parent.glob(f"{stem}*.tim"))
        if tim_files:
            tim_model = BoundaryConditionConverter.merge_tim_files(tim_files, quantity)
            n_columns = len(tim_model.get_units())
            tim_model.quantities_names = ["discharge"] * n_columns
            self.legacy_files = tim_files
            result = tim_model
        else:
            result = None
        return result

    def _get_discharge(
        self, forcing: ExtOldForcing, time_unit: str | None
    ) -> Any:
        """Derive the discharge value from the old forcing block.

        Args:
            forcing (ExtOldForcing): The old forcing block.
            time_unit (Optional[str]): The time unit string for time series data.

        Returns:
            Any: A constant float, a ForcingModel, or a file path representing the discharge.
        """
        result = forcing.value

        if forcing.value is None or isinstance(forcing.filename, PolyFile):
            if isinstance(forcing.filename, TimModel):
                result = self._get_discharge_from_tim_model(forcing, time_unit)
            elif isinstance(forcing.filename, PolyFile):
                result = self._get_discharge_from_poly_file(forcing, time_unit)

        return result

    def _get_discharge_from_tim_model(
        self, forcing: ExtOldForcing, time_unit: str | None
    ) -> ForcingModel:
        """Convert a TIM file referenced directly in the forcing block into a ForcingModel.

        Args:
            forcing (ExtOldForcing): The old forcing block whose filename is a TimModel.
            time_unit (Optional[str]): The time unit string for time series data.

        Returns:
            ForcingModel: The converted forcing model.

        Raises:
            ValueError: If time_unit is None.
        """
        if time_unit is None:
            raise ValueError(
                "The 'time_unit' argument must be provided when converting a "
                "lateral discharge from a TIM file."
            )

        tim_file = resolve_relative_to_root(forcing.filename.filepath, self.root_dir)
        location_name = tim_file.stem
        tim_model = TimModel(tim_file, quantities_names=["discharge"])
        units = tim_model.get_units()
        user_defined_names = [location_name]
        time_series_list = TimToForcingConverter.convert(
            tim_model, time_unit, units=units, user_defined_names=user_defined_names
        )
        forcing_model = ForcingModel(forcing=time_series_list)
        forcing_model.filepath = tim_file.with_suffix(".bc")
        self.legacy_files = tim_file
        return forcing_model

    def _get_discharge_from_poly_file(
        self, forcing: ExtOldForcing, time_unit: str | None
    ) -> Any:
        """Derive the discharge for a lateral defined via a PolyFile.

        Tries to resolve an associated TIM file first; falls back to a constant
        value if present; otherwise raises an error.

        Args:
            forcing (ExtOldForcing): The old forcing block whose filename is a PolyFile.
            time_unit (Optional[str]): The time unit string for time series data.

        Returns:
            Any: A ForcingModel (when a TIM file is found) or a constant float.

        Raises:
            ValueError: If neither a TIM file nor a constant value can be found.
        """
        location_file = forcing.filename.filepath
        tim_model = self._resolve_tim_file(forcing.filename, forcing.quantity)

        if tim_model is not None:
            result = self._convert_poly_tim_to_forcing_model(
                tim_model, location_file, time_unit
            )
        elif forcing.value is not None:
            result = forcing.value
        else:
            raise ValueError(
                f"Could not determine the discharge for lateral '{location_file.stem}': "
                f"no constant VALUE, no '{location_file.stem}.tim', and no "
                f"'{location_file.stem}_0001.tim' were found next to the polygon file. "
                "Ensure a time-series (.tim) file or a VALUE field is present in the "
                "old external forcings block."
            )
        return result

    def _convert_poly_tim_to_forcing_model(
        self, tim_model: TimModel, location_file: Any, time_unit: str | None
    ) -> ForcingModel:
        """Convert a TIM model associated with a PolyFile into a ForcingModel.

        Args:
            tim_model (TimModel): The resolved TIM model.
            location_file: The path of the polygon file (used to derive names and output path).
            time_unit (Optional[str]): The time unit string for time series data.

        Returns:
            ForcingModel: The converted forcing model.

        Raises:
            ValueError: If time_unit is None.
        """
        if time_unit is None:
            raise ValueError(
                "The 'time_unit' argument must be provided when converting a "
                "lateral discharge from a TIM file."
            )

        location_name = location_file.stem
        units = tim_model.get_units()
        if len(units) == 1:
            user_defined_names = [location_name]
        else:
            user_defined_names = [f"{location_name}_{i + 1:04d}" for i in
                                  range(len(units))]

        time_series_list = TimToForcingConverter.convert(
            tim_model,
            time_unit,
            units=units,
            user_defined_names=user_defined_names,
        )
        forcing_model = ForcingModel(forcing=time_series_list)
        forcing_model.filepath = location_file.with_suffix(".bc")
        return forcing_model

    def _get_location_data(self, forcing: ExtOldForcing) -> dict[str, Any]:
        """Extract location data from the old forcing block.

        Args:
            forcing (ExtOldForcing): The old forcing block.

        Returns:
            Dict[str, Any]: A dict with 'id' and either a 'locationfile' key (when
                the source is a PolyFile) or inline coordinate fields.
        """
        if isinstance(forcing.filename, PolyFile):
            poly_file = forcing.filename
            location_name = poly_file.filepath.stem
            result = {"id": location_name}
            if poly_file.objects:
                first_obj = poly_file.objects[0]
                if first_obj.metadata and first_obj.metadata.name:
                    result["id"] = first_obj.metadata.name
            result["locationfile"] = poly_file.filepath
        elif isinstance(forcing.filename, TimModel):
            location_name = forcing.filename.filepath.stem
            result = {"id": location_name}
        elif (
            hasattr(forcing.filename, "filepath")
            and forcing.filename.filepath is not None
        ):
            result = {"id": forcing.filename.filepath.stem}
        else:
            result = {"id": str(forcing.quantity)}

        return result


class ConverterFactory:
    """A factory class for creating converters based on the given quantity."""

    @staticmethod
    def create_converter(
        quantity, root_dir: PathOrStr = None, mdu_parser: MDUParser = None
    ) -> BaseConverter:
        """
        Create converter based on the given quantity.

        Args:
            quantity: The quantity for which the converter needs to be created.
            root_dir (PathOrStr, optional): Root directory used to resolve the forcing
                file paths, forwarded to every converter. Only the boundary condition
                and source/sink converters read it. Defaults to None.
            mdu_parser (MDUParser, optional): Parser for the FM model, forwarded to
                the converters that need it. Only the `SourceSinkConverter` uses it
                at present. Defaults to None.

        Returns:
            BaseConverter: An instance of a specific BaseConverter subclass
                for the given quantity.

        Raises:
            ValueError: If no converter is available for the given quantity.
        """
        if (
            ConverterFactory.contains(ExtOldMeteoQuantity, quantity)
            or ConverterFactory.contains(ExtOldInitialConditionQuantity, quantity)
            or ConverterFactory.contains(ExtOldParametersQuantity, quantity)
        ):
            return SpatialConverter()
        elif ConverterFactory.contains(ExtOldBoundaryQuantity, quantity):
            return BoundaryConditionConverter(mdu_parser=mdu_parser, root_dir=root_dir)
        elif ConverterFactory.contains(ExtOldSourcesSinks, quantity):
            return SourceSinkConverter(mdu_parser=mdu_parser, root_dir=root_dir)
        elif ConverterFactory.contains(ExtOldLateralQuantity, quantity):
            return LateralConverter(root_dir=root_dir, mdu_parser=mdu_parser)
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
            "function": "t3d",
            "vertpositions": t3d_model.layers,
            "vertpositiontype": (
                "percBed"
                if not hasattr(t3d_model, "vertpositiontype")
                else t3d_model.vertpositiontype
            ),
        }

        if hasattr(t3d_model, "vertinterpolation"):
            data["vertinterpolation"] = t3d_model.vertinterpolation

        if hasattr(t3d_model, "timeinterpolation"):
            data["timeinterpolation"] = t3d_model.timeinterpolation

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
