"""Utility functions for converting old external forcing files to new format."""

import os
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Type, Union

import yaml
from pydantic.v1 import BaseModel, Extra, Field, validator

from hydrolib import __path__
from hydrolib.core.base.file_manager import PathOrStr
from hydrolib.core.base.models import DiskOnlyFileModel, FileModel
from hydrolib.core.dflowfm.ext.models import (
    MeteoForcingFileType,
    MeteoInterpolationMethod,
)
from hydrolib.core.dflowfm.extold.models import (
    ExtOldFileType,
    ExtOldForcing,
    ExtOldModel,
    ExtOldQuantity,
)
from hydrolib.core.dflowfm.inifield.models import (
    AveragingType,
    DataFileType,
    InterpolationMethod,
)

SOURCESINK_SALINITY_IN_BC = "sourcesink_salinitydelta"
SOURCESINK_TEMP_IN_BC = "sourcesink_temperaturedelta"
SOURCESINK_NAME_IN_EXT = "discharge_salinity_temperature_sorsin"


__all__ = [
    "UnSupportedQuantitiesError",
    "CONVERTER_DATA",
    "find_temperature_salinity_in_quantities",
    "IgnoreUnknownKeyWordClass",
    "backup_file",
    "construct_filemodel_new_or_existing",
    "path_relative_to_parent",
]


AVERAGING_TYPE_DICT = {
    1: AveragingType.mean,
    2: AveragingType.nearestnb,
    3: AveragingType.max,
    4: AveragingType.min,
    5: AveragingType.invdist,
    6: AveragingType.minabs,
    7: AveragingType.median,
}


CONVERTER_DATA_PATH = Path(__path__[0]) / "tools/extforce_convert/data/data.yaml"
with CONVERTER_DATA_PATH.open("r") as fh:
    try:
        CONVERTER_DATA = yaml.safe_load(fh)
    except yaml.YAMLError as e:
        raise RuntimeError(f"Failed to parse YAML at {CONVERTER_DATA_PATH}: {e}") from e


def construct_filemodel_new_or_existing(
    model_class: Type[FileModel], filepath: PathOrStr, *args, **kwargs
) -> FileModel:
    """Construct a new instance of a FileModel subclass, either loading an existing model file, or starting a blank one.

    If the given filepath exists, it will be loaded, as if the constructor
    was directly called. If it does not exist, the blank model instance
    will only have its filepath attribute set, e.g., for future saving.

    Args:
        model_class (type[FileModel]): The FileModel subclass to construct or update.
        filepath (PathOrStr): The filepath to use for the new or existing model input.
        *args: Additional positional arguments to pass to the ModelClass constructor
        **kwargs: Additional keywords arguments to pass to the ModelClass constructor
    """
    if Path(filepath).is_file():
        model = model_class(filepath=filepath, *args, **kwargs)
    else:
        model = model_class(*args, **kwargs)
        model.filepath = filepath

    return model


def backup_file(filepath: PathOrStr) -> None:
    """Create a backup of the given file by copying it to a new file with a '.bak' extension.

    Args:
        filepath (PathOrStr): The path to the file to back up.
    """
    filepath = Path(filepath) if isinstance(filepath, str) else filepath
    if filepath.is_file():
        backup_path = filepath.with_suffix(filepath.suffix + ".bak")
        filepath.replace(backup_path)


def oldfiletype_to_forcing_file_type(
    oldfiletype: int,
) -> Union[MeteoForcingFileType, str]:
    """Convert old external forcing `FILETYPE` integer value to valid `forcingFileType` string value.

    Args:
        oldfiletype (int): The FILETYPE value in an old external forcings file.

    Returns:
        Union[MeteoForcingFileType,str]: Corresponding value for `forcingFileType`,
            or "unknown" for invalid input.
    """
    forcing_file_type = "unknown"

    if oldfiletype == ExtOldFileType.TimeSeries:  # 1
        forcing_file_type = MeteoForcingFileType.uniform
    elif oldfiletype == ExtOldFileType.TimeSeriesMagnitudeAndDirection:  # 2
        forcing_file_type = MeteoForcingFileType.unimagdir
    elif oldfiletype == ExtOldFileType.SpatiallyVaryingWindPressure:  # 3
        raise NotImplementedError(
            "FILETYPE = 3 (spatially verying wind and pressure) is no longer supported."
        )
    elif oldfiletype == ExtOldFileType.ArcInfo:  # 4
        forcing_file_type = MeteoForcingFileType.arcinfo
    elif oldfiletype == ExtOldFileType.SpiderWebData:  # 5
        forcing_file_type = MeteoForcingFileType.spiderweb
    elif oldfiletype == ExtOldFileType.CurvilinearData:  # 6
        forcing_file_type = MeteoForcingFileType.curvigrid
    elif oldfiletype == ExtOldFileType.Samples:  # 7
        forcing_file_type = DataFileType.sample
    elif oldfiletype == ExtOldFileType.TriangulationMagnitudeAndDirection:  # 8
        raise NotImplementedError(
            "FILETYPE = 8 (magnitude+direction timeseries on stations) is no longer supported."
        )
    elif oldfiletype == ExtOldFileType.Polyline:  # 9
        # Boundary polyline files no longer need a filetype of their own (intentionally no error raised)
        pass
    elif oldfiletype == ExtOldFileType.InsidePolygon:  # 10
        forcing_file_type = DataFileType.polygon
    elif oldfiletype == ExtOldFileType.NetCDFGridData:  # 11
        forcing_file_type = MeteoForcingFileType.netcdf

    return forcing_file_type


def oldmethod_to_interpolation_method(
    oldmethod: int,
) -> Union[InterpolationMethod, MeteoInterpolationMethod, str]:
    """Convert old external forcing `METHOD` integer value to valid `interpolationMethod` string value.

    Args:
        oldmethod (int): The METHOD value in an old external forcings file.

    Returns:
        Union[InterpolationMethod,str]: Corresponding value for `interpolationMethod`,
            or "unknown" for invalid input.
    """
    if oldmethod in [1, 2, 3, 11]:
        interpolation_method = MeteoInterpolationMethod.linearSpaceTime
    elif oldmethod == 5:
        interpolation_method = InterpolationMethod.triangulation
    elif oldmethod == 4:
        interpolation_method = InterpolationMethod.constant
    elif oldmethod in range(6, 10):
        interpolation_method = InterpolationMethod.averaging
    else:
        interpolation_method = "unknown"
    return interpolation_method


def map_method_to_averaging_type(
    old_forcing_method: int,
    averaging_type: int,
) -> Union[AveragingType, str]:
    """Convert an old external forcing `METHOD` integer value to a valid ` averagingType ` string value.

    Args:
        old_forcing_method (int):
            The `METHOD` value in an old external forcings file.
        averaging_type (int):
            The `AVERAGINGTYPE` value in an old external forcings file.
            AVERAGINGTYPE (ONLY WHEN METHOD=6)
            ```ini
            =1  : SIMPLE AVERAGING
            =2  : NEAREST NEIGHBOUR
            =3  : MAX (HIGHEST)
            =4  : MIN (LOWEST)
            =5  : INVERSE WEIGHTED DISTANCE-AVERAGE
            =6  : MINABS
            =7  : KDTREE (LIKE 1, BUT FAST AVERAGING)
            ```

    Notes:
        - The new external forcing will have an Averaging type if the old external forcings had a `Method = 6`.


    Returns:
        Union[AveragingType,str]:
            Corresponding value for `averagingType`, or "unknown" for invalid input.
    """
    if old_forcing_method == 6:
        if averaging_type is None:
            averaging_type = AveragingType.mean
        else:
            averaging_type = AVERAGING_TYPE_DICT.get(int(averaging_type), "unknown")
    else:
        averaging_type = "unknown"

    return averaging_type


def convert_interpolation_data(
    forcing: ExtOldForcing, data: Dict[str, Any]
) -> Dict[str, str]:
    """Convert interpolation data from old to new format.

    Args:
        forcing (ExtOldForcing): The old forcing block with interpolation data.
        data (Dict[str, Any]): The dictionary to which the new data will be added.

    Returns:
        Dict[str, str]: The updated dictionary with the new interpolation data.
        - The dictionary will contain the "interpolationmethod" key with the new interpolation method.
        - if the interpolation method is "Averaging" (method = 6), the dictionary will also contain
            the "averagingtype", "averagingrelsize", "averagingnummin", and "averagingpercentile" keys.
    """
    data["interpolationmethod"] = oldmethod_to_interpolation_method(forcing.method)
    if data["interpolationmethod"] == InterpolationMethod.averaging:
        data["averagingtype"] = map_method_to_averaging_type(
            forcing.method, forcing.averagingtype
        )
        data["averagingrelsize"] = forcing.relativesearchcellsize
        data["averagingnummin"] = forcing.nummin
        data["averagingpercentile"] = forcing.percentileminmax

    return data


def path_relative_to_parent(
    forcing: ExtOldForcing,
    inifile_path: Path,
    ext_old_path: Path,
    mdu_parser: Any,
) -> Path:
    """Resolve the path of the forcing file relative to the parent file if needed.

    Args:
        forcing (ExtOldForcing):
            The old forcing block with the filename to resolve.
        inifile_path (Path):
            The path to the inifields file.
        ext_old_path (Path):
            The path to the old external forcing file.
        mdu_parser (MDUParser):
            The MDU parser object containing the loaded MDU data.
            This holds the "pathsRelativeToParent" setting.

    Returns:
        Path: The resolved path of the forcing file.
    """
    if mdu_parser is None:
        resolve_parent = False
    else:
        resolve_parent = mdu_parser.is_relative_to_parent

    update_path_condition = (
        forcing.filename.filepath.is_absolute() or not resolve_parent
    )

    forcing_path = (
        forcing.filename.filepath
        if update_path_condition
        else os.path.relpath(
            ext_old_path.parent / forcing.filename.filepath, inifile_path.parent
        )
    )
    return forcing_path


def create_initial_cond_and_parameter_input_dict(
    forcing: ExtOldForcing,
    new_forcing_path: Path,
) -> Dict[str, str]:
    """Create the input dictionary for the `InitialField` or `ParameterField`.

    Args:
        forcing: [ExtOldForcing]
            External forcing block from the old external forcings file.
        new_forcing_path: [Path]
            The path to the new forcing file.

    Returns:
        Dict[str, str]:
            the input dictionary to the `InitialField` or `ParameterField` constructor
    """
    quantity_name = (
        forcing.quantity
        if forcing.quantity != ExtOldQuantity.BedRockSurfaceElevation
        else "bedrockSurfaceElevation"
    )
    block_data = {
        "quantity": quantity_name,
        "datafile": DiskOnlyFileModel(new_forcing_path),
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
    block_data = convert_interpolation_data(forcing, block_data)
    block_data["operand"] = forcing.operand

    if hasattr(forcing, "extrapolation"):
        block_data["extrapolationmethod"] = (
            "yes" if forcing.extrapolation == 1 else "no"
        )
    for key, value in forcing.dict().items():
        if key.lower().startswith("tracer") and value is not None:
            block_data[key] = value
    return block_data


def find_temperature_salinity_in_quantities(strings: List[str]) -> Dict[str, int]:
    """Find temperature and salinity in quantities.

    Searches for keywords "temperature" and "salinity" in a list of strings
    and returns a dictionary with associated values.

    Args:
        strings (List[str]):
            A list of strings to search.

    Returns:
        Dict[str, int]:
            A dictionary with keys as "salinity" or "temperature" and values 3 and 4 respectively.

     Examples:
        ```python
        >>> from hydrolib.tools.extforce_convert.utils import find_temperature_salinity_in_quantities
        >>> find_temperature_salinity_in_quantities(["temperature", "Salinity"])
        OrderedDict({'sourcesink_salinitydelta': 3, 'sourcesink_temperaturedelta': 4})
        >>> find_temperature_salinity_in_quantities(["Temperature"])
        OrderedDict({'sourcesink_temperaturedelta': 3})
        >>> find_temperature_salinity_in_quantities(["Salinity"])
        OrderedDict({'sourcesink_salinitydelta': 3})
        >>> find_temperature_salinity_in_quantities(["tracers"])
        OrderedDict()
        >>> find_temperature_salinity_in_quantities([])
        OrderedDict()
        >>> find_temperature_salinity_in_quantities(["discharge_salinity_temperature_sorsin", "Salinity"])
        OrderedDict({'sourcesink_salinitydelta': 3})

        ```

    Notes:
        - The function removes the `discharge_salinity_temperature_sorsin` from the given list of strings.
        - The function removes the duplicate strings in the list.
    """
    result = OrderedDict()
    strings = list(set(strings))
    # remove the `discharge_salinity_temperature_sorsin` quantity from the list
    if SOURCESINK_NAME_IN_EXT in strings:
        strings.remove(SOURCESINK_NAME_IN_EXT)

    if any("salinity" in string.lower() for string in strings):
        result[SOURCESINK_SALINITY_IN_BC] = 3
    if any("temperature" in string.lower() for string in strings):
        result[SOURCESINK_TEMP_IN_BC] = (
            result.get(SOURCESINK_SALINITY_IN_BC, 2) + 1
        )  # Default temperature value is 2

    return result


class IgnoreUnknownKeyWord(type):
    """Metaclass to ignore unknown keyword arguments when creating a new class instance."""

    def __call__(cls, base_class, **data):
        """Dynamically create and instantiate a subclass of base_class."""

        class DynamicClass(base_class):
            class Config:
                extra = Extra.ignore

            def __init__(self, **data):
                valid_fields = self.__annotations__.keys()
                filtered_data = {k: v for k, v in data.items() if k in valid_fields}
                super().__init__(**filtered_data)

        return DynamicClass(**data)


class IgnoreUnknownKeyWordClass(metaclass=IgnoreUnknownKeyWord):
    """Base class to ignore unknown keyword arguments when creating a new class instance."""

    pass


def check_unique(v):
    """Checks and filters unique non-empty strings from the input list.

        This function processes a given input list, ensuring that all strings are:
        - Trimmed of any leading or trailing whitespace.
        - Converted to lowercase for case-insensitive uniqueness.
        - Added to the result list only if they haven't been seen before.

        Empty strings or non-string elements are ignored.

    Args:
        v (list[str] | None):
            A list of strings to be processed. May contain None or non-string elements.
            If the input is None, it is treated as an empty list.

    Returns:
        list[str]
            A list of unique, lowercase, trimmed strings in the order of their first
            appearance.
    """
    seen = set()
    unique = []
    for s in v or []:
        if isinstance(s, str):
            key = s.strip().lower()
            if key and key not in seen:
                seen.add(key)
                unique.append(key)
    return unique


class MDUConfig(BaseModel):
    deprecated_keywords: Set[str] = Field(default_factory=set)
    deprecated_value: int = 0

    @validator("deprecated_keywords", pre=True)
    def _to_set(cls, v):
        """convert the deprecated keywords to a set."""
        if v is None:
            return set()

        if isinstance(v, str):
            v = [v]
        return set(check_unique(v))


class ExternalForcingConfigs(BaseModel):
    unsupported_quantity_names: List[str] = Field(default_factory=list)
    unsupported_prefixes: List[str] = Field(default_factory=list)

    @validator("unsupported_quantity_names", "unsupported_prefixes", pre=True)
    def ensure_unique(cls, v: List[str]) -> List[str]:
        return check_unique(v)

    def find_unsupported(self, quantities: Iterable[str]) -> Set[str]:
        """Return the set of unsupported quantities present in the given iterable."""
        normalized = [str(q).lower() for q in quantities]
        result = set(self.unsupported_quantity_names).intersection(normalized)

        for q in normalized:
            if any(q.startswith(p) for p in self.unsupported_prefixes):
                result.add(q)
        return result

    def check_unsupported_quantities(
        self, quantities: Iterable[str], raise_error: bool = True
    ) -> Set[str]:
        """Raise an error if any of the given quantities are unsupported."""
        un_supported = self.find_unsupported(quantities)
        if raise_error and un_supported:
            raise UnSupportedQuantitiesError(
                f"The following quantities are not supported by the converter yet: {un_supported}"
            )
        else:
            return un_supported


class ConverterData(BaseModel):
    version: str
    mdu: MDUConfig = Field(default_factory=MDUConfig)
    external_forcing: ExternalForcingConfigs = Field(
        default_factory=ExternalForcingConfigs
    )

    def check_unsupported_quantities(
        self, ext_old_model: ExtOldModel, raise_error: bool = True
    ):
        """Check if the old external forcing file contains unsupported quantities."""
        quantities = [forcing.quantity for forcing in ext_old_model.forcing]
        unsupported_quantities = self.external_forcing.check_unsupported_quantities(
            quantities, raise_error=raise_error
        )
        return unsupported_quantities


CONVERTER_DATA = ConverterData(**CONVERTER_DATA)


class UnSupportedQuantitiesError(Exception):
    pass
