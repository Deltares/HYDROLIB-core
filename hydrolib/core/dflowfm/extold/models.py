from enum import IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import Field, field_validator, model_validator
from strenum import StrEnum

from hydrolib.core.base.models import (
    BaseModel,
    DiskOnlyFileModel,
    ModelSaveSettings,
    ParsableFileModel,
    SerializerConfig,
)
from hydrolib.core.base.utils import resolve_file_model
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.extold.parser import Parser
from hydrolib.core.dflowfm.extold.serializer import Serializer
from hydrolib.core.dflowfm.ini.util import enum_value_parser
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.tim.models import TimModel

INITIAL_CONDITION_QUANTITIES_VALID_PREFIXES = (
    "initialtracer",
    "initialsedfrac",
    "initialverticalsedfracprofile",
    "initialverticalsigmasedfracprofile",
)

BOUNDARY_CONDITION_QUANTITIES_VALID_PREFIXES = (
    "tracerbnd",
    "sedfracbnd",
)

FILETYPE_FILEMODEL_MAPPING = {
    1: TimModel,
    2: TimModel,
    3: DiskOnlyFileModel,
    4: DiskOnlyFileModel,
    5: DiskOnlyFileModel,
    6: DiskOnlyFileModel,
    7: DiskOnlyFileModel,
    8: DiskOnlyFileModel,
    9: PolyFile,
    10: PolyFile,
    11: DiskOnlyFileModel,
    12: DiskOnlyFileModel,
}

HEADER = """
 QUANTITY    : waterlevelbnd, velocitybnd, dischargebnd, tangentialvelocitybnd, normalvelocitybnd  filetype=9         method=2,3
             : outflowbnd, neumannbnd, qhbnd, uxuyadvectionvelocitybnd                             filetype=9         method=2,3
             : salinitybnd                                                                         filetype=9         method=2,3
             : gateloweredgelevel, damlevel, pump                                                  filetype=9         method=2,3
             : frictioncoefficient, horizontaleddyviscositycoefficient, advectiontype              filetype=4,7,10    method=4
             : bedlevel, ibotlevtype                                                               filetype=4,7,10    method=4..9
             : initialwaterlevel                                                                   filetype=4,7,10,12 method=4..9
             : initialtemperature                                                                  filetype=4,7,10,12 method=4..9
             : initialvelocityx, initialvelocityy                                                  filetype=4,7,10,12 method=4..9
             : initialvelocity                                                                     filetype=12        method=4..9
             : initialsalinity, initialsalinitytop: use initialsalinity for depth-uniform, or
             : as bed level value in combination with initialsalinitytop                           filetype=4,7,10    method=4
             : initialverticaltemperatureprofile                                                   filetype=9,10      method=
             : initialverticalsalinityprofile                                                      filetype=9,10      method=
             : windx, windy, windxy, rainfall, atmosphericpressure                                 filetype=1,2,4,6,7,8 method=1,2,3
             : shiptxy, movingstationtxy                                                           filetype=1         method=1
             : discharge_salinity_temperature_sorsin                                               filetype=9         method=1
             : windstresscoefficient                                                               filetype=4,7,10    method=4
             : nudge_salinity_temperature                                                          filetype=11        method=3

 kx = Vectormax = Nr of variables specified on the same time/space frame. Eg. Wind magnitude,direction: kx = 2
 FILETYPE=1  : uniform              kx = 1 value               1 dim array      uni
 FILETYPE=2  : unimagdir            kx = 2 values              1 dim array,     uni mag/dir transf to u,v, in index 1,2
 FILETYPE=3  : svwp                 kx = 3 fields  u,v,p       3 dim array      nointerpolation
 FILETYPE=4  : arcinfo              kx = 1 field               2 dim array      bilin/direct
 FILETYPE=5  : spiderweb            kx = 3 fields              3 dim array      bilin/spw
 FILETYPE=6  : curvi                kx = ?                                      bilin/findnm
 FILETYPE=7  : triangulation        kx = 1 field               1 dim array      triangulation
 FILETYPE=8  : triangulation_magdir kx = 2 fields consisting of Filetype=2      triangulation in (wind) stations

 FILETYPE=9  : polyline             kx = 1 For polyline points i= 1 through N specify boundary signals, either as
                                           timeseries or Fourier components or tidal constituents
                                           Timeseries are in files *_000i.tim, two columns: time (min)  values
                                           Fourier components and or tidal constituents are in files *_000i.cmp, three columns
                                           period (min) or constituent name (e.g. M2), amplitude and phase (deg)
                                           If no file is specified for a node, its value will be interpolated from surrounding nodes
                                           If only one signal file is specified, the boundary gets a uniform signal
                                           For a dischargebnd, only one signal file must be specified

 FILETYPE=10 : inside_polygon       kx = 1 field                                uniform value inside polygon for INITIAL fields
 FILETYPE=11 : ncgrid               kx = 1 field                    2 dim array      triangulation (should have proper standard_name in var, e.g., 'precipitation')
 FILETYPE=12 : ncflow (map file)    kx = 1 or 2 field               1 dim array      triangulation
 FILETYPE=14 : ncwave (com file)    kx = 1 field                    1 dim array      triangulation

 METHOD  =0  : provider just updates, another provider that pointers to this one does the actual interpolation
         =1  : intp space and time (getval) keep  2 meteofields in memory
         =2  : first intp space (update), next intp. time (getval) keep 2 flowfields in memory
         =3  : save weightfactors, intp space and time (getval),   keep 2 pointer- and weight sets in memory.
         =4  : only spatial, inside polygon
         =5  : only spatial, triangulation, (if samples from *.asc file then bilinear)
         =6  : only spatial, averaging
         =7  : only spatial, index triangulation
         =8  : only spatial, smoothing
         =9  : only spatial, internal diffusion
         =10 : only initial vertical profiles

 OPERAND =O  : Override at all points
         =+  : Add to previously specified value
         =*  : Multiply with previously specified value
         =A  : Apply only if no value specified previously (For Initial fields, similar to Quickin preserving best data specified first)
         =X  : MAX with prev. spec.
         =N  : MIN with prev. spec.

 EXTRAPOLATION_METHOD (ONLY WHEN METHOD=3)
         = 0 : No spatial extrapolation.
         = 1 : Do spatial extrapolation outside of source data bounding box.

 MAXSEARCHRADIUS (ONLY WHEN EXTRAPOLATION_METHOD=1)
         = search radius (in m) for model grid points that lie outside of the source data bounding box.

 AVERAGINGTYPE (ONLY WHEN METHOD=6)
         =1  : SIMPLE AVERAGING
         =2  : NEAREST NEIGHBOUR
         =3  : MAX (HIGHEST)
         =4  : MIN (LOWEST)
         =5  : INVERSE WEIGHTED DISTANCE-AVERAGE
         =6  : MINABS
         =7  : KDTREE (LIKE 1, BUT FAST AVERAGING)

 RELATIVESEARCHCELLSIZE : For METHOD=6, the relative search cell size for samples inside cell (default: 1.01)

 PERCENTILEMINMAX : (ONLY WHEN AVERAGINGTYPE=3 or 4) Changes the min/max operator to an average of the
               highest/lowest data points. The value sets the percentage of the total set that is to be included.

 NUMMIN  =   : For METHOD=6, minimum required number of source data points in each target cell.

 VALUE   =   : Offset value for this provider

 FACTOR  =   : Conversion factor for this provider

*************************************************************************************************************
"""


class ExtOldTracerQuantity(StrEnum):
    """Enum class containing the valid values for the boundary conditions category
    of the external forcings that are specific to tracers.

    Attributes:
        TracerBnd (str):
            User-defined tracer boundary condition.
        InitialTracer (str):
            Initial tracer condition.
        SedFracBnd (str):
            Sediment fraction boundary condition.
    """

    TracerBnd = "tracerbnd"
    InitialTracer = "initialtracer"
    SedFracBnd = "sedfracbnd"


class ExtOldBoundaryQuantity(StrEnum):
    # Boundary conditions
    WaterLevelBnd = "waterlevelbnd"
    """Water level"""
    NeumannBnd = "neumannbnd"
    """Water level gradient"""
    RiemannBnd = "riemannbnd"
    """Riemann invariant"""
    OutflowBnd = "outflowbnd"
    """Outflow"""
    VelocityBnd = "velocitybnd"
    """Velocity"""
    DischargeBnd = "dischargebnd"
    """Discharge"""
    RiemannVelocityBnd = "riemann_velocitybnd"
    """Riemann invariant velocity"""
    SalinityBnd = "salinitybnd"
    """Salinity"""
    TemperatureBnd = "temperaturebnd"
    """Temperature"""
    SedimentBnd = "sedimentbnd"
    """Suspended sediment"""
    UXUYAdvectionVelocityBnd = "uxuyadvectionvelocitybnd"
    """ux-uy advection velocity"""
    NormalVelocityBnd = "normalvelocitybnd"
    """Normal velocity"""
    TangentialVelocityBnd = "tangentialvelocitybnd"
    """Tangential velocity"""
    QhBnd = "qhbnd"
    """Discharge-water level dependency"""

    @classmethod
    def _missing_(cls, value):
        """Custom implementation for handling missing values.

        the method parses any missing values and only allows the ones that start with "initialtracer".
        """
        # Allow strings starting with "tracer"
        if isinstance(value, str) and value.startswith(
            BOUNDARY_CONDITION_QUANTITIES_VALID_PREFIXES
        ):
            new_member = str.__new__(cls, value)
            new_member._value_ = value
            return new_member
        else:
            raise ValueError(
                f"{value} is not a valid {cls.__name__} possible quantities are {', '.join(cls.__members__)}, "
                f"and quantities that start with 'tracer'"
            )


class ExtOldParametersQuantity(StrEnum):
    """Enum class containing the valid values for the Spatial parameter category
    of the external forcings.

    for more details check D-Flow FM User Manual 1D2D, Chapter D.3.1, Table D.2
    https://content.oss.deltares.nl/delft3d/D-Flow_FM_User_Manual_1D2D.pdf
    """

    FrictionCoefficient = "frictioncoefficient"
    HorizontalEddyViscosityCoefficient = "horizontaleddyviscositycoefficient"
    HorizontalEddyDiffusivityCoefficient = "horizontaleddydiffusivitycoefficient"
    AdvectionType = "advectiontype"
    InfiltrationCapacity = "infiltrationcapacity"
    BedRockSurfaceElevation = "bedrock_surface_elevation"
    WaveDirection = "wavedirection"
    XWaveForce = "xwaveforce"
    YWaveForce = "ywaveforce"
    WavePeriod = "waveperiod"
    WaveSignificantHeight = "wavesignificantheight"
    InternalTidesFrictionCoefficient = "internaltidesfrictioncoefficient"
    SecchiDepth = "secchidepth"
    SeaIceAreaFraction = "sea_ice_area_fraction"
    StemHeight = "stemheight"
    StemDensity = "stemdensity"
    StemDiameter = "stemdiameter"
    NudgeRate = "nudgerate"
    NudgeTime = "nudgetime"


class ExtOldMeteoQuantity(StrEnum):

    # Meteorological fields
    WindX = "windx"
    """Wind x component"""
    WindY = "windy"
    """Wind y component"""
    WindXY = "windxy"
    """Wind vector"""
    AirPressureWindXWindY = "airpressure_windx_windy"
    """Atmospheric pressure and wind components"""
    AirPressureWindXWindYCharnock = "airpressure_windx_windy_charnock"
    "Atmospheric pressure and wind components Charnock"
    AtmosphericPressure = "atmosphericpressure"
    """Atmospheric pressure"""
    Rainfall = "rainfall"
    """Precipitation"""
    RainfallRate = "rainfall_rate"
    """Precipitation"""
    HumidityAirTemperatureCloudiness = "humidity_airtemperature_cloudiness"
    """Combined heat flux terms"""
    HumidityAirTemperatureCloudinessSolarRadiation = (
        "humidity_airtemperature_cloudiness_solarradiation"
    )
    """Combined heat flux terms"""
    DewPointAirTemperatureCloudiness = "dewpoint_airtemperature_cloudiness"
    """Dew point air temperature cloudiness"""
    LongWaveRadiation = "longwaveradiation"
    """Long wave radiation"""
    SolarRadiation = "solarradiation"
    """Solar radiation"""
    NudgeSalinityTemperature = "nudge_salinity_temperature"
    """Nudging salinity and temperature"""
    AirPressure = "airpressure"
    """AirPressure"""
    StressX = "stressx"
    """eastward wind stress"""
    StressY = "stressy"
    """northward wind stress"""
    AirTemperature = "airtemperature"
    """AirTemperature"""
    Cloudiness = "cloudiness"
    """Cloudiness, or cloud cover (fraction)"""
    Humidity = "humidity"
    """Humidity"""
    StressXY = "stressxy"
    """eastward and northward wind stress"""
    AirpressureStressXStressY = "airpressure_stressx_stressy"
    """Airpressure, eastward and northward wind stress"""
    WindSpeed = "wind_speed"
    """WindSpeed"""
    WindSpeedFactor = "windspeedfactor"

    WindFromDirection = "wind_from_direction"
    """WindFromDirection"""
    DewpointAirTemperatureCloudinessSolarradiation = (
        "dewpoint_airtemperature_cloudiness_solarradiation"
    )
    """Dewpoint temperature, air temperature, cloudiness, solarradiation"""
    AirDensity = "airdensity"
    """Air density"""
    Charnock = "charnock"
    """Charnock coefficient"""
    Dewpoint = "dewpoint"
    """Dewpoint temperature"""


class ExtOldInitialConditionQuantity(StrEnum):
    """
    Initial Condition quantities:
        initialwaterlevel, initialsalinity, initialsalinitytop, initialtemperature,
        initialverticaltemperatureprofile, initialverticalsalinityprofile, initialvelocityx,
        initialvelocityy, initialvelocity

    If there is a missing quantity that is mentioned in the "Accepted quantity names" section of the user manual
    [Sec.C.5.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.3).
    and [Sec.D.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.D.3).
    please open and issue in github.
    """

    # Initial Condition fields
    BedLevel = "bedlevel"
    BedLevel1D = "bedlevel1D"
    BedLevel2D = "bedlevel2D"

    InitialWaterLevel = "initialwaterlevel"
    InitialWaterLevel1D = "initialwaterlevel1d"
    InitialWaterLevel2D = "initialwaterlevel2d"

    InitialSalinity = "initialsalinity"
    InitialSalinityTop = "initialsalinitytop"
    InitialSalinityBot = "initialsalinitybot"
    InitialVerticalSalinityProfile = "initialverticalsalinityprofile"

    InitialTemperature = "initialtemperature"
    InitialVerticalTemperatureProfile = "initialverticaltemperatureprofile"

    initialUnsaturatedZoneThickness = "initialunsaturatedzonethickness"
    InitialVelocityX = "initialvelocityx"
    InitialVelocityY = "initialvelocityy"
    InitialVelocity = "initialvelocity"
    InitialWaqBot = "initialwaqbot"

    @classmethod
    def _missing_(cls, value):
        """Custom implementation for handling missing values.

        the method parses any missing values and only allows the ones that start with "initialtracer".
        """
        # Allow strings starting with "tracer"
        if isinstance(value, str) and value.startswith(
            INITIAL_CONDITION_QUANTITIES_VALID_PREFIXES
        ):
            new_member = str.__new__(cls, value)
            new_member._value_ = value
            return new_member
        else:
            raise ValueError(
                f"{value} is not a valid {cls.__name__} possible quantities are {', '.join(cls.__members__)}, "
                f"and quantities that start with 'tracer'"
            )


class ExtOldSourcesSinks(StrEnum):
    """Source and sink quantities"""

    DischargeSalinityTemperatureSorSin = "discharge_salinity_temperature_sorsin"


class ExtOldQuantity(StrEnum):
    """Enum class containing the valid values for the boundary conditions category
    of the external forcings.
    """

    # Boundary conditions
    WaterLevelBnd = "waterlevelbnd"
    NeumannBnd = "neumannbnd"
    RiemannBnd = "riemannbnd"
    OutflowBnd = "outflowbnd"
    VelocityBnd = "velocitybnd"
    DischargeBnd = "dischargebnd"
    RiemannVelocityBnd = "riemann_velocitybnd"
    SalinityBnd = "salinitybnd"
    TemperatureBnd = "temperaturebnd"
    SedimentBnd = "sedimentbnd"
    UXUYAdvectionVelocityBnd = "uxuyadvectionvelocitybnd"
    NormalVelocityBnd = "normalvelocitybnd"
    TangentialVelocityBnd = "tangentialvelocitybnd"
    QhBnd = "qhbnd"

    # Meteorological fields
    WindX = "windx"
    WindY = "windy"
    WindXY = "windxy"
    AirPressureWindXWindY = "airpressure_windx_windy"
    AirPressureWindXWindYCharnock = "airpressure_windx_windy_charnock"
    AtmosphericPressure = "atmosphericpressure"
    Rainfall = "rainfall"
    RainfallRate = "rainfall_rate"
    HumidityAirTemperatureCloudiness = "humidity_airtemperature_cloudiness"
    HumidityAirTemperatureCloudinessSolarRadiation = (
        "humidity_airtemperature_cloudiness_solarradiation"
    )
    DewPointAirTemperatureCloudiness = "dewpoint_airtemperature_cloudiness"
    LongWaveRadiation = "longwaveradiation"
    SolarRadiation = "solarradiation"
    DischargeSalinityTemperatureSorSin = "discharge_salinity_temperature_sorsin"
    NudgeSalinityTemperature = "nudge_salinity_temperature"
    AirPressure = "airpressure"
    StressX = "stressx"
    StressY = "stressy"
    AirTemperature = "airtemperature"
    Cloudiness = "cloudiness"
    Humidity = "humidity"
    StressXY = "stressxy"
    AirpressureStressXStressY = "airpressure_stressx_stressy"
    WindSpeed = "wind_speed"
    WindSpeedFactor = "windspeedfactor"
    WindFromDirection = "wind_from_direction"
    DewpointAirTemperatureCloudinessSolarradiation = (
        "dewpoint_airtemperature_cloudiness_solarradiation"
    )
    AirDensity = "airdensity"
    Charnock = "charnock"
    Dewpoint = "dewpoint"

    # Structure parameters
    Pump = "pump"
    DamLevel = "damlevel"
    GateLowerEdgeLevel = "gateloweredgelevel"
    GeneralStructure = "generalstructure"

    # Initial fields
    InitialWaterLevel = "initialwaterlevel"
    InitialSalinity = "initialsalinity"
    InitialSalinityTop = "initialsalinitytop"
    InitialTemperature = "initialtemperature"
    InitialVerticalTemperatureProfile = "initialverticaltemperatureprofile"
    InitialVerticalSalinityProfile = "initialverticalsalinityprofile"
    BedLevel = "bedlevel"
    SecchiDepth = "secchidepth"
    SeaIceAreaFraction = "sea_ice_area_fraction"
    StemHeight = "stemheight"
    StemDensity = "stemdensity"
    StemDiameter = "stemdiameter"
    NudgeRate = "nudgerate"
    NudgeTime = "nudgetime"

    # Spatial physical properties
    FrictionCoefficient = "frictioncoefficient"
    HorizontalEddyViscosityCoefficient = "horizontaleddyviscositycoefficient"
    InternalTidesFrictionCoefficient = "internaltidesfrictioncoefficient"
    HorizontalEddyDiffusivityCoefficient = "horizontaleddydiffusivitycoefficient"
    AdvectionType = "advectiontype"
    IBotLevType = "ibotlevtype"
    BedRockSurfaceElevation = "bedrock_surface_elevation"

    # Miscellaneous
    ShiptXY = "shiptxy"
    MovingStationXY = "movingstationxy"
    WaveSignificantHeight = "wavesignificantheight"
    WavePeriod = "waveperiod"
    WaveDirection = "wavedirection"
    XWaveForce = "xwaveforce"
    YWaveForce = "ywaveforce"

    InitialVelocityX = "initialvelocityx"
    InitialVelocityY = "initialvelocityy"
    InitialVelocity = "initialvelocity"


class ExtOldFileType(IntEnum):
    """Enum class containing the valid values for the `filetype` attribute
    in the [ExtOldForcing][hydrolib.core.dflowfm.extold.models.ExtOldForcing] class.
    """

    TimeSeries = 1
    """1. Time series"""
    TimeSeriesMagnitudeAndDirection = 2
    """2. Time series magnitude and direction"""
    SpatiallyVaryingWindPressure = 3
    """3. Spatially varying wind and pressure"""
    ArcInfo = 4
    """4. ArcInfo"""
    SpiderWebData = 5
    """5. Spiderweb data (cyclones)"""
    CurvilinearData = 6
    """6. Space-time data on curvilinear grid"""
    Samples = 7
    """7. Samples"""
    TriangulationMagnitudeAndDirection = 8
    """8. Triangulation magnitude and direction"""
    Polyline = 9
    """9. Polyline (<*.pli>-file) with boundary signals on support points"""
    InsidePolygon = 10
    """10. Polyfile (<*.pol>-file). Uniform value inside polygon for INITIAL fields"""
    NetCDFGridData = 11
    """11. NetCDF grid data (e.g. meteo fields)"""
    NetCDFWaveData = 14
    """14. NetCDF wave data"""


class ExtOldMethod(IntEnum):
    """Enum class containing the valid values for the `method` attribute
    in the [ExtOldForcing][hydrolib.core.dflowfm.extold.models.ExtOldForcing] class.
    """

    PassThrough = 1
    """1. Pass through (no interpolation)"""
    InterpolateTimeAndSpace = 2
    """2. Interpolate time and space"""
    InterpolateTimeAndSpaceSaveWeights = 3
    """3. Interpolate time and space, save weights"""
    InterpolateSpace = 4
    """4. Interpolate space"""
    InterpolateTime = 5
    """5. Interpolate time"""
    AveragingSpace = 6
    """6. Averaging in space"""
    InterpolateExtrapolateTime = 7
    """7. Interpolate/Extrapolate time"""
    Obsolete = 11
    """11. METHOD=11 is obsolete; use METHOD=3 and EXTRAPOLATION_METHOD=1"""


class ExtOldExtrapolationMethod(IntEnum):
    """Enum class containing the valid values for the `extrapolation_method` attribute
    in the [ExtOldForcing][hydrolib.core.dflowfm.extold.models.ExtOldForcing] class.
    """

    NoSpatialExtrapolation = 0
    """0. No spatial extrapolation."""
    SpatialExtrapolationOutsideOfSourceDataBoundingBox = 1
    """1. Do spatial extrapolation outside of source data bounding box."""


class ExtOldForcing(BaseModel):
    """Class holding the external forcing values.

    This class is used to represent the external forcing values in the D-Flow FM model.

    Attributes:
        quantity (Union[ExtOldQuantity, str]):
            The name of the quantity.
        filename (Union[PolyFile, TimModel, DiskOnlyFileModel]):
            The file associated with this forcing.
        varname (Optional[str]):
            The variable name used in `filename` associated with this forcing; some input files may contain multiple variables.
        sourcemask (DiskOnlyFileModel):
            The file containing a mask.
        filetype (ExtOldFileType):
            Indication of the file type.
            Options:
                1. Time series
                2. Time series magnitude and direction
                3. Spatially varying weather
                4. ArcInfo
                5. Spiderweb data (cyclones)
                6. Curvilinear data
                7. Samples (C.3)
                8. Triangulation magnitude and direction
                9. Polyline (<*.pli>-file, C.2)
                11. NetCDF grid data (e.g. meteo fields)
                14. NetCDF wave data
        method (ExtOldMethod):
            The method of interpolation.
            Options:
                1. Pass through (no interpolation)
                2. Interpolate time and space
                3. Interpolate time and space, save weights
                4. Interpolate space
                5. Interpolate time
                6. Averaging space
                7. Interpolate/Extrapolate time
        extrapolation_method (Optional[ExtOldExtrapolationMethod]):
            The extrapolation method.
                Options:
                    0. No spatial extrapolation.
                    1. Do spatial extrapolation outside of source data bounding box.
        maxsearchradius (Optional[float]):
            Search radius for model grid points that lie outside of the source data bounding box.
        operand (Operand):
            The operand to use for adding the provided values.

            Options:
                'O' Existing values are overwritten with the provided values.
                'A' Provided values are used where existing values are missing.
                '+' Existing values are summed with the provided values.
                '*' Existing values are multiplied with the provided values.
                'X' The maximum values of the existing values and provided values are used.
                'N' The minimum values of the existing values and provided values are used.
        value (Optional[float]):
            Custom coefficients for transformation.
        factor (Optional[float]):
            The conversion factor.
        ifrctyp (Optional[float]):
            The friction type.
        averagingtype (Optional[float]):
            The averaging type.
        relativesearchcellsize (Optional[float]):
            The relative search cell size for samples inside a cell.
        extrapoltol (Optional[float]):
            The extrapolation tolerance.
        percentileminmax (Optional[float]):
            Changes the min/max operator to an average of the highest/lowest data points.
            The value sets the percentage of the total set that is to be included.
        area (Optional[float]):
            The area for sources and sinks.
        nummin (Optional[int]):
            The minimum required number of source data points in each target cell.
    """

    quantity: Union[ExtOldQuantity, str] = Field(alias="QUANTITY")
    filename: Union[PolyFile, TimModel, DiskOnlyFileModel] = Field(
        None, alias="FILENAME"
    )
    varname: Optional[str] = Field(None, alias="VARNAME")
    sourcemask: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="SOURCEMASK"
    )
    filetype: ExtOldFileType = Field(alias="FILETYPE")
    method: ExtOldMethod = Field(alias="METHOD")
    extrapolation_method: Optional[ExtOldExtrapolationMethod] = Field(
        None, alias="EXTRAPOLATION_METHOD"
    )

    maxsearchradius: Optional[float] = Field(None, alias="MAXSEARCHRADIUS")
    operand: Operand = Field(alias="OPERAND")
    value: Optional[float] = Field(None, alias="VALUE")
    factor: Optional[float] = Field(None, alias="FACTOR")
    ifrctyp: Optional[float] = Field(None, alias="IFRCTYP")
    averagingtype: Optional[float] = Field(None, alias="AVERAGINGTYPE")

    relativesearchcellsize: Optional[float] = Field(
        None, alias="RELATIVESEARCHCELLSIZE"
    )
    extrapoltol: Optional[float] = Field(None, alias="EXTRAPOLTOL")
    percentileminmax: Optional[float] = Field(None, alias="PERCENTILEMINMAX")
    area: Optional[float] = Field(None, alias="AREA")
    nummin: Optional[int] = Field(None, alias="NUMMIN")

    tracerfallvelocity: Optional[float] = Field(None, alias="TRACERFALLVELOCITY")
    tracerdecaytime: Optional[float] = Field(None, alias="TRACERDECAYTIME")

    def is_intermediate_link(self) -> bool:
        return True

    @model_validator(mode="before")
    @classmethod
    def handle_case_insensitive_tracer_fields(cls, values):
        """Handle case-insensitive matching for tracer fields."""
        values_copy = dict(values)

        # Define the field names and their aliases
        tracer_fields = ["tracerfallvelocity", "tracerdecaytime"]

        for field_i in values.keys():
            if field_i.lower() in tracer_fields:
                # if the field is already lowercase no need to change it
                if field_i != field_i.lower():
                    # If the key is not in the expected lowercase format, add it with the correct format
                    values_copy[field_i.lower()] = values_copy[field_i]
                    # Remove the original key to avoid "extra fields not permitted" error
                    values_copy.pop(field_i)

        return values_copy

    @field_validator("quantity", mode="before")
    @classmethod
    def validate_quantity(cls, value) -> Any:
        if isinstance(value, ExtOldQuantity):
            return value

        def raise_error_tracer_name(quantity: ExtOldTracerQuantity):
            raise ValueError(
                f"QUANTITY '{quantity}' should be appended with a tracer name."
            )

        if isinstance(value, ExtOldTracerQuantity):
            raise_error_tracer_name(value)

        value_str = str(value)
        lower_value = value_str.lower()

        for tracer_quantity in ExtOldTracerQuantity:
            if lower_value.startswith(tracer_quantity):
                n = len(tracer_quantity)
                if n == len(value_str):
                    raise_error_tracer_name(tracer_quantity)
                return tracer_quantity + value_str[n:]

        if lower_value in list(ExtOldQuantity):
            return ExtOldQuantity(lower_value)

        supported_value_str = ", ".join(([x.value for x in ExtOldQuantity]))
        raise ValueError(
            f"QUANTITY '{value_str}' not supported. Supported values: {supported_value_str}"
        )

    @field_validator("operand", mode="before")
    @classmethod
    def validate_operand(cls, value):
        return enum_value_parser(value, Operand)

    @model_validator(mode="after")
    def validate_varname(self):
        if self.varname and self.filetype != ExtOldFileType.NetCDFGridData:
            raise ValueError(
                "VARNAME only allowed when FILETYPE is 11 (NetCDFGridData)"
            )
        return self

    @field_validator("extrapolation_method")
    @classmethod
    def validate_extrapolation_method(cls, v, info):
        method = info.data.get("method")
        valid_extrapolation_method = (
            ExtOldExtrapolationMethod.SpatialExtrapolationOutsideOfSourceDataBoundingBox
        )
        available_extrapolation_methods = [
            ExtOldMethod.InterpolateTimeAndSpaceSaveWeights,
            ExtOldMethod.Obsolete,
        ]
        if (
            v == valid_extrapolation_method
            and method not in available_extrapolation_methods
        ):
            raise ValueError(
                f"EXTRAPOLATION_METHOD only allowed to be {valid_extrapolation_method} when METHOD is "
                f"{available_extrapolation_methods[0]} or {available_extrapolation_methods[1]}"
            )
        return v

    @model_validator(mode="after")
    def validate_factor(self):
        quantity = self.quantity
        if self.factor is not None and not str(quantity).startswith(
            ExtOldTracerQuantity.InitialTracer
        ):
            raise ValueError(
                f"FACTOR only allowed when QUANTITY starts with {ExtOldTracerQuantity.InitialTracer}"
            )
        return self

    @model_validator(mode="after")
    def validate_ifrctyp(self):
        if (
            self.ifrctyp is not None
            and self.quantity != ExtOldQuantity.FrictionCoefficient
        ):
            raise ValueError(
                f"IFRCTYP only allowed when QUANTITY is {ExtOldQuantity.FrictionCoefficient}"
            )
        return self

    @model_validator(mode="after")
    def validate_averagingtype(self):
        if (
            self.averagingtype is not None
            and self.method != ExtOldMethod.AveragingSpace
        ):
            raise ValueError(
                f"AVERAGINGTYPE only allowed when METHOD is {ExtOldMethod.AveragingSpace}"
            )
        return self

    @model_validator(mode="after")
    def validate_relativesearchcellsize(self):
        if (
            self.relativesearchcellsize is not None
            and self.method != ExtOldMethod.AveragingSpace
        ):
            raise ValueError(
                f"RELATIVESEARCHCELLSIZE only allowed when METHOD is {ExtOldMethod.AveragingSpace}"
            )
        return self

    @model_validator(mode="after")
    def validate_extrapoltol(self):
        if self.extrapoltol is not None and self.method != ExtOldMethod.InterpolateTime:
            raise ValueError("EXTRAPOLTOL only allowed when METHOD is 5")
        return self

    @model_validator(mode="after")
    def validate_percentileminmax(self):
        if (
            self.percentileminmax is not None
            and self.method != ExtOldMethod.AveragingSpace
        ):
            raise ValueError(
                f"PERCENTILEMINMAX only allowed when METHOD is {ExtOldMethod.AveragingSpace}"
            )
        return self

    @model_validator(mode="after")
    def validate_area(self):
        if (
            self.area is not None
            and self.quantity != ExtOldQuantity.DischargeSalinityTemperatureSorSin
        ):
            raise ValueError(
                f"AREA only allowed when QUANTITY is {ExtOldQuantity.DischargeSalinityTemperatureSorSin}"
            )
        return self

    @model_validator(mode="after")
    def validate_nummin(self):
        if self.nummin is not None and self.method != ExtOldMethod.AveragingSpace:
            raise ValueError(
                f"NUMMIN only allowed when METHOD is {ExtOldMethod.AveragingSpace}"
            )
        return self

    @field_validator("maxsearchradius")
    def validate_maxsearchradius(cls, v, info):
        if v is not None:
            extrap = info.data.get("extrapolation_method")
            extrapolation_method_value = (
                ExtOldExtrapolationMethod.SpatialExtrapolationOutsideOfSourceDataBoundingBox
            )
            if extrap != extrapolation_method_value:
                raise ValueError(
                    f"MAXSEARCHRADIUS only allowed when EXTRAPOLATION_METHOD is {extrapolation_method_value}"
                )
        return v

    @field_validator("value")
    @classmethod
    def validate_value(cls, v, info):
        if v is not None:
            method = info.data.get("method")
            if method != ExtOldMethod.InterpolateSpace:
                raise ValueError(
                    f"VALUE only allowed when METHOD is {ExtOldMethod.InterpolateSpace} (InterpolateSpace)"
                )
        return v

    @model_validator(mode="before")
    @classmethod
    def choose_file_model(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Root-level validator to the right class for the filename parameter based on the filetype.

        The validator chooses the right class for the filename parameter based on the FileType_FileModel_mapping
        dictionary.

        FileType_FileModel_mapping = {
            1: TimModel,
            2: TimModel,
            3: DiskOnlyFileModel,
            4: DiskOnlyFileModel,
            5: DiskOnlyFileModel,
            6: DiskOnlyFileModel,
            7: DiskOnlyFileModel,
            8: DiskOnlyFileModel,
            9: PolyFile,
            10: PolyFile,
            11: DiskOnlyFileModel,
            12: DiskOnlyFileModel,
        }
        """
        # if the filetype and the filename are present in the values
        if any(par in values for par in ["filetype", "FILETYPE"]) and any(
            par in values for par in ["filename", "FILENAME"]
        ):
            file_type_var_name = "filetype" if "filetype" in values else "FILETYPE"
            filename_var_name = "filename" if "filename" in values else "FILENAME"
            file_type = values.get(file_type_var_name)
            raw_path = values.get(filename_var_name)

            if isinstance(raw_path, (Path, str)):
                model = FILETYPE_FILEMODEL_MAPPING.get(int(file_type))
                values[filename_var_name] = resolve_file_model(raw_path, model)

        return values

    @model_validator(mode="before")
    @classmethod
    def validate_sourcemask(cls, data: Any) -> Any:
        filetype = data.get("filetype")
        sourcemask = data.get("sourcemask")

        # Convert string to DiskOnlyFileModel if needed
        if isinstance(sourcemask, str):
            data["sourcemask"] = DiskOnlyFileModel(sourcemask)
            sourcemask = data["sourcemask"]

        if sourcemask and filetype not in [
            ExtOldFileType.ArcInfo,
            ExtOldFileType.CurvilinearData,
        ]:
            raise ValueError("SOURCEMASK only allowed when FILETYPE is 4 or 6")
        return data


class ExtOldModel(ParsableFileModel):
    """
    The overall external forcings model that contains the contents of one external forcings file (old format).

    This model is typically referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.external_forcing.extforcefile`.

    Attributes:
        comment (List[str]):
            The comments in the header of the external forcing file.
        forcing (List[ExtOldForcing]):
            The external forcing/QUANTITY blocks in the external forcing file.
    """

    comment: List[str] = Field(default=HEADER.splitlines()[1:])
    forcing: List[ExtOldForcing] = Field(default_factory=list)

    @classmethod
    def _ext(cls) -> str:
        return ".ext"

    @classmethod
    def _filename(cls) -> str:
        return "externalforcings"

    @classmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, SerializerConfig, ModelSaveSettings], None]:
        return Serializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return Parser.parse

    @property
    def quantities(self) -> List[str]:
        """List all the quantities in the external forcings file."""
        return [forcing.quantity for forcing in self.forcing]
