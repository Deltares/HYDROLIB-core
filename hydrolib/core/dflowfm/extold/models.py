from enum import Enum, IntEnum
from typing import Optional, Union

from pydantic import Field, root_validator, validator

from hydrolib.core.basemodel import BaseModel, DiskOnlyFileModel


class Quantity(str, Enum):
    """Enum class containing the valid values for the boundary conditions category
    of the external forcings.
    """

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
    """Tangentional velocity"""
    QhBnd = "qhbnd"
    """Discharge-water level dependency"""
    TracerBnd = "tracerbnd"
    """User-defined tracer"""

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
    DischargeSalinityTemperatureSorSin = "discharge_salinity_temperature_sorsin"
    """Discharge, salinity and heat sources"""

    # Structure parameters
    Pump = "pump"
    """Pump capacity"""
    DamLevel = "damlevel"
    """Dam level"""
    GateLowerEdgeLevel = "gateloweredgelevel"
    """Gate lower edge level"""
    GeneralStructure = "generalstructure"
    """General structure"""

    # Initial fields
    InitialWaterLevel = "initialwaterlevel"
    """Initial water level"""
    InitialSalinity = "initialsalinity"
    """Initial salinity"""
    InitialSalinityTop = "initialsalinitytop"
    """Initial salinity top"""
    InitialTemperature = "initialtemperature"
    """Initial temperature"""
    InitialVerticalTemperatureProfile = "initialverticaltemperatureprofile"
    """Initial vertical temperature profile"""
    InitialVerticalSalinityProfile = "initialverticalsalinityprofile"
    """Initial vertical salinity profile"""
    InitialTracer = "initialtracer"
    """Initial tracer"""
    BedLevel = "bedlevel"
    """Bed level"""

    # Spatial physical properties
    FrictionCoefficient = "frictioncoefficient"
    """Friction coefficient"""
    HorizontalEddyViscosityCoefficient = "horizontaleddyviscositycoefficient"
    """Horizontal eddy viscosity coefficient"""
    InternalTidesFrictionCoefficient = "internaltidesfrictioncoefficient"
    """Internal tides friction coefficient"""
    HorizontalEddyDiffusivityCoefficient = "horizontaleddydiffusivitycoefficient"
    """Horizontal eddy diffusivity coefficient"""
    AdvectionType = "advectiontype"
    """Type of advection scheme"""
    IBotLevType = "ibotlevtype"
    """Type of bed-level handling"""

    # Miscellaneous
    ShiptXY = "shiptxy"
    """shiptxy"""
    MovingStationXY = "movingstationxy"
    """Moving observation point for output (time, x, y)"""
    WaveSignificantHeight = "wavesignificantheight"
    """Wave significant heigth"""
    WavePeriod = "waveperiod"
    """Wave period"""


class FileType(IntEnum):
    """Enum class containing the valid values for the `filetype` attribute
    in the [ExtForcing][hydrolib.core.dflowfm.extold.models.ExtForcing] class.
    """

    TimeSeries = 1
    """1. Time series"""
    TimeSeriesMagnitudeAndDirection = 2
    """2. Time series magnitude and direction"""
    SpatiallyVaryingWeather = 3
    """3. Spatially varying weather"""
    ArcInfo = 4
    """4. ArcInfo"""
    SpiderWebData = 5
    """5. Spiderweb data (cyclones)"""
    CurvilinearData = 6
    """6. Curvilinear data"""
    Samples = 7
    """7. Samples"""
    TriangulationMagnitudeAndDirection = 8
    """8. Triangulation magnitude and direction"""
    Polyline = 9
    """9. Polyline (<*.pli>-file)"""
    NetCDFGridData = 11
    """11. NetCDF grid data (e.g. meteo fields)"""
    NetCDFWaveData = 14
    """14. NetCDF wave data"""


class Method(IntEnum):
    """Enum class containing the valid values for the `method` attribute
    in the [ExtForcing][hydrolib.core.dflowfm.extold.models.ExtForcing] class.
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
    InterpolateExtrapolateTime = 7
    """7. Interpolate/Extrapolate time"""


class Operand(str, Enum):
    """Enum class containing the valid values for the `operand` attribute
    in the [ExtForcing][hydrolib.core.dflowfm.extold.models.ExtForcing] class.
    """

    OverwriteExistingValues = "O"
    """Existing values are overwritten."""
    SuperimposeNewValues = "+"
    """New values are superimposed."""


class ExtForcing(BaseModel):
    """Class holding the external forcing values."""

    quantity: Union[Quantity, str] = Field(alias="QUANTITY")
    """Union[Quantity, str]: The name of the quantity."""

    filename: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="FILENAME"
    )
    """DiskOnlyFileModel: The file associated to this forcing."""

    varname: Optional[str] = Field(None, alias="VARNAME")
    """Optional[str]: The variable name used in `filename` associated with this forcing; some input files may contain multiple variables."""

    sourcemask: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="SOURCEMASK"
    )
    """DiskOnlyFileModel: The file containing a mask."""

    filetype: FileType = Field(alias="FILETYPE")
    """FileType: Indication of the file type.
    
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
    """

    method: Method = Field(alias="METHOD")
    """Method: The method of interpolation.
    
    Options:
    1. Pass through (no interpolation)
    2. Interpolate time and space
    3. Interpolate time and space, save weights
    4. Interpolate space
    5. Interpolate time
    7. Interpolate/Extrapolate time
    """

    operand: Operand = Field(alias="OPERAND")
    """Operand: Overwriting or superimposing values already set for this quantity:
    'O' Values are overwritten.
    '+' New value is superimposed.
    """

    value: Optional[float] = Field(None, alias="VALUE")
    """Optional[float]: custom coefficients for transformation."""

    factor: Optional[float] = Field(None, alias="FACTOR")
    """Optional[float]: The factor."""

    ifrctyp: Optional[float] = Field(None, alias="IFRCTYP")
    """Optional[float]: The friction type."""

    averagingtype: Optional[float] = Field(None, alias="AVERAGINGTYPE")
    """Optional[float]: The averging type."""

    relativesearchcellsize: Optional[float] = Field(
        None, alias="RELATIVESEARCHCELLSIZE"
    )
    """Optional[float]: The relative search cell size."""

    extrapoltol: Optional[float] = Field(None, alias="EXTRAPOLTOL")
    """Optional[float]: The extrapolation tolerance."""

    percentileminmax: Optional[float] = Field(None, alias="PERCENTILEMINMAX")
    """Optional[float]: The percentile min max."""

    area: Optional[float] = Field(None, alias="AREA")
    """Optional[float]: The area for sources and sinks."""

    nummin: Optional[int] = Field(None, alias="NUMMIN")
    """Optional[int]: The area for sources and sinks."""

    @validator("quantity", pre=True)
    def validate_quantity(cls, value):
        if isinstance(value, str):
            lower_value = value.lower()

            if lower_value.startswith(Quantity.TracerBnd):
                n = len(Quantity.TracerBnd.value)
                return Quantity.TracerBnd.value + value[n:]

            if lower_value.startswith(Quantity.InitialTracer):
                n = len(Quantity.InitialTracer.value)
                return Quantity.InitialTracer.value + value[n:]

            supported_values = list(Quantity)
            if lower_value in supported_values:
                return Quantity(lower_value)

            supported_value_str = ", ".join(([x.value for x in supported_values]))
            raise ValueError(
                f"QUANTITY '{value}' not supported. Supported values: {supported_value_str}"
            )

        return value

    @validator("operand", pre=True)
    def validate_operand(cls, value):
        if isinstance(value, str):

            for operand in Operand:
                if value.lower() == operand.value.lower():
                    return operand

            supported_value_str = ", ".join(([x.value for x in Operand]))
            raise ValueError(
                f"OPERAND '{value}' not supported. Supported values: {supported_value_str}"
            )

        return value

    @root_validator()
    def validate_forcing(cls, values):
        quantity = values["quantity"]
        filetype = values["filetype"]
        method = values["method"]

        varname = values["varname"]
        if varname is not None:
            if filetype != 11:
                raise ValueError(
                    "VARNAME only allowed when FILETYPE is 11 (NetCDF grid data)"
                )

        sourcemask = values["sourcemask"]
        if sourcemask.filepath is not None:
            if filetype not in [4, 6]:
                raise ValueError(
                    "SOURCEMASK only allowed when FILETYPE is 4 (ArcInfo) or 6 (Curvilinear data)"
                )

        value = values["value"]
        if value is not None:
            if method != 4:
                raise ValueError(
                    "VALUE only allowed when METHOD is 4 (Interpolate space)"
                )
            
        factor = values["factor"]
        if factor is not None:
            if not quantity.startswith(Quantity.InitialTracer):
                raise ValueError(
                    f"FACTOR only allowed when QUANTITY start with {Quantity.InitialTracer}"
                )

        return values
