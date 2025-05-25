from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Type, Union

from pydantic.v1 import Extra

from hydrolib.core.base.file_manager import PathOrStr
from hydrolib.core.base.models import DiskOnlyFileModel, FileModel
from hydrolib.core.dflowfm.ext.models import (
    MeteoForcingFileType,
    MeteoInterpolationMethod,
)
from hydrolib.core.dflowfm.extold.models import ExtOldFileType, ExtOldForcing
from hydrolib.core.dflowfm.inifield.models import (
    AveragingType,
    DataFileType,
    InterpolationMethod,
)


def construct_filemodel_new_or_existing(
    model_class: Type[FileModel], filepath: PathOrStr, *args, **kwargs
) -> FileModel:
    """Construct a new instance of a FileModel subclass, either loading an
    existing model file, or starting a blank one.

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
    """Create a backup of the given file by copying it to a new file with a
    '.bak' extension.

    Args:
        filepath (PathOrStr): The path to the file to back up.
    """
    filepath = Path(filepath) if isinstance(filepath, str) else filepath
    if filepath.is_file():
        backup_path = filepath.with_suffix(filepath.suffix + ".bak")
        filepath.replace(backup_path)


def construct_filepath_with_postfix(filepath: PathOrStr, postfix: str) -> Path:
    """Construct a new filepath by adding a postfix to the existing
    filepath, still keeping the original file suffix.
    For example, 'file.txt' with postfix '_new' will become 'file_new.txt'.

    Args:
        filepath (PathOrStr): The path to the file.
        postfix (str): The postfix to add to the filename.

    Returns:
        Path: The new filepath with the postfix included.

    Examples:
        ```python
        >>> construct_filepath_with_postfix("file.txt", "_new") # doctest: +SKIP
        Path("file_new.txt")
        ```
    """
    file_as_path = Path(filepath)
    return file_as_path.with_stem(file_as_path.stem + postfix)


def oldfiletype_to_forcing_file_type(
    oldfiletype: int,
) -> Union[MeteoForcingFileType, str]:
    """Convert old external forcing `FILETYPE` integer value to valid
        `forcingFileType` string value.

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
    """Convert old external forcing `METHOD` integer value to valid
        `interpolationMethod` string value.

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


def oldmethod_to_averaging_type(
    oldmethod: int,
) -> Union[AveragingType, str]:
    """Convert old external forcing `METHOD` integer value to valid
        `averagingType` string value.

    Args:
        oldmethod (int): The METHOD value in an old external forcings file.

    Returns:
        Union[AveragingType,str]: Corresponding value for `averagingType`,
            or "unknown" for invalid input.
    """

    if oldmethod == 6:
        averaging_type = AveragingType.mean
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
        data["averagingtype"] = oldmethod_to_averaging_type(forcing.method)
        data["averagingrelsize"] = forcing.relativesearchcellsize
        data["averagingnummin"] = forcing.nummin
        data["averagingpercentile"] = forcing.percentileminmax

    return data


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
        "datafile": DiskOnlyFileModel(forcing.filename.filepath),
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

    return block_data


def find_temperature_salinity_in_quantities(strings: List[str]) -> Dict[str, int]:
    """
    Searches for keywords "temperature" and "salinity" in a list of strings
    and returns a dictionary with associated values.

    Args:
        strings (List[str]): A list of strings to search.

    Returns:
        Dict[str, int]: A dictionary with keys as "salinity" or "temperature"
                        and values 3 and 4 respectively.

     Examples:
         ```python
        >>> find_temperature_salinity_in_quantities(["temperature", "Salinity"])
        OrderedDict({'salinitydelta': 3, 'temperaturedelta': 4})
        >>> find_temperature_salinity_in_quantities(["Temperature"])
        OrderedDict({'temperaturedelta': 3})
        >>> find_temperature_salinity_in_quantities(["Salinity"])
        OrderedDict({'salinitydelta': 3})
        >>> find_temperature_salinity_in_quantities(["tracers"])
        OrderedDict()
        >>> find_temperature_salinity_in_quantities([])
        OrderedDict()
        >>> find_temperature_salinity_in_quantities(["discharge_salinity_temperature_sorsin", "Salinity"])
        OrderedDict({'salinitydelta': 3})

        ```

    Notes:
        - The function removes the `discharge_salinity_temperature_sorsin` from the given list of strings.
        - The function removes the duplicate strings in the list.
    """
    result = OrderedDict()
    strings = list(set(strings))
    # remove the `discharge_salinity_temperature_sorsin` quantity from the list
    if "discharge_salinity_temperature_sorsin" in strings:
        strings.remove("discharge_salinity_temperature_sorsin")

    if any("salinity" in string.lower() for string in strings):
        result["salinitydelta"] = 3
    if any("temperature" in string.lower() for string in strings):
        result["temperaturedelta"] = (
            result.get("salinitydelta", 2) + 1
        )  # Default temperature value is 2

    return result


class IgnoreUnknownKeyWord(type):
    """Metaclass to ignore unknown keyword arguments when creating a new class instance"""

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
    pass
