from typing import Union

from hydrolib.core.dflowfm.ext.models import (
    MeteoForcingFileType,
    MeteoInterpolationMethod,
)
from hydrolib.core.dflowfm.extold.models import ExtOldFileType
from hydrolib.core.dflowfm.inifield.models import (
    AveragingType,
    DataFileType,
    InterpolationMethod,
)


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
        forcing_file_type = MeteoForcingFileType.meteogridequi
    elif oldfiletype == ExtOldFileType.SpiderWebData:  # 5
        forcing_file_type = MeteoForcingFileType.spiderweb
    elif oldfiletype == ExtOldFileType.CurvilinearData:  # 6
        forcing_file_type = MeteoForcingFileType.meteogridcurvi
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
        interpolation_method = "unknown"
