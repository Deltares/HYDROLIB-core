from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import Field, root_validator, validator

from hydrolib.core.basemodel import (
    BaseModel,
    DiskOnlyFileModel,
    ModelSaveSettings,
    ParsableFileModel,
    SerializerConfig,
)
from hydrolib.core.dflowfm.extold.parser import Parser
from hydrolib.core.dflowfm.extold.serializer import Serializer
from hydrolib.core.dflowfm.polyfile.models import PolyFile


class TracerQuantity(str, Enum):
    """Enum class containing the valid values for the boundary conditions category
    of the external forcings that are specific to tracers.
    """

    TracerBnd = "tracerbnd"
    """User-defined tracer"""
    InitialTracer = "initialtracer"
    """Initial tracer"""


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
    Averaging = 6
    """6. Averaging"""
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

    filename: Union[PolyFile, DiskOnlyFileModel] = Field(None, alias="FILENAME")
    """Union[PolyFile, DiskOnlyFileModel]: The file associated to this forcing."""

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
    6. Averaging
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
    """Optional[int]: The nummin."""

    @validator("quantity", pre=True)
    def validate_quantity(cls, value):
        if isinstance(value, Quantity):
            return value

        def raise_error_tracer_name(quantity: TracerQuantity):
            raise ValueError(
                f"QUANTITY '{quantity}' should be appended with a tracer name."
            )

        if isinstance(value, TracerQuantity):
            raise_error_tracer_name(value)

        value_str = str(value)
        lower_value = value_str.lower()

        for tracer_quantity in TracerQuantity:
            if lower_value.startswith(tracer_quantity):
                n = len(tracer_quantity)
                if n == len(value_str):
                    raise_error_tracer_name(tracer_quantity)
                return tracer_quantity + value_str[n:]

        if lower_value in list(Quantity):
            return Quantity(lower_value)

        supported_value_str = ", ".join(([x.value for x in Quantity]))
        raise ValueError(
            f"QUANTITY '{value_str}' not supported. Supported values: {supported_value_str}"
        )

    @validator("operand", pre=True)
    def validate_operand(cls, value):
        if isinstance(value, Operand):
            return value

        if isinstance(value, str):

            for operand in Operand:
                if value.lower() == operand.value.lower():
                    return operand

            supported_value_str = ", ".join(([x.value for x in Operand]))
            raise ValueError(
                f"OPERAND '{value}' not supported. Supported values: {supported_value_str}"
            )

        return value

    @root_validator(skip_on_failure=True)
    def validate_forcing(cls, values):
        def alias(field_key: str):
            return cls.__fields__[field_key].alias

        def raise_error_only_allowed_when(
            field_key: str, dependency_key: str, valid_dependency_value: str
        ):
            field_alias = alias(field_key)
            dependency_alias = alias(dependency_key)

            raise ValueError(
                f"{field_alias} only allowed when {dependency_alias} is {valid_dependency_value}"
            )

        def only_allowed_when(
            field_key: str, dependency_key: str, valid_dependency_value: Any
        ):
            """This function checks if a particular field is allowed to have a value only when a dependency field has a specific value."""
            field_value = values[field_key]
            dependency_value = values[dependency_key]

            if field_value is None or dependency_value == valid_dependency_value:
                return

            raise_error_only_allowed_when(
                field_key, dependency_key, valid_dependency_value
            )

        quantity_key = "quantity"
        filetype_key = "filetype"
        method_key = "method"

        only_allowed_when("varname", filetype_key, 11)
        only_allowed_when("value", method_key, 4)
        only_allowed_when("ifrctyp", quantity_key, Quantity.FrictionCoefficient)
        only_allowed_when("averagingtype", method_key, 6)
        only_allowed_when("relativesearchcellsize", method_key, 6)
        only_allowed_when("extrapoltol", method_key, 5)
        only_allowed_when("percentileminmax", method_key, 6)
        only_allowed_when(
            "area", quantity_key, Quantity.DischargeSalinityTemperatureSorSin
        )
        only_allowed_when("nummin", method_key, 6)

        sourcemask = values["sourcemask"]
        filetype = values[filetype_key]
        if sourcemask.filepath is not None and filetype not in [4, 6]:
            raise_error_only_allowed_when(
                "sourcemask", filetype_key, valid_dependency_value="4 or 6"
            )

        factor = values["factor"]
        quantity = values[quantity_key]
        quantity_alias = alias(quantity_key)
        if factor is not None and not quantity.startswith(TracerQuantity.InitialTracer):
            key = alias("factor")
            raise ValueError(
                f"{key} only allowed when {quantity_alias} starts with {TracerQuantity.InitialTracer}"
            )

        return values


class ExtOldModel(ParsableFileModel):
    """
    The overall external forcings model that contains the contents of one external forcings file (old format).

    This model is typically referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.external_forcing.extforcefile`.
    """

    comment: List[str] = []
    """List[str]: The comments in the header of the external forcing file."""
    forcing: List[ExtForcing] = []
    """List[ExtForcing]: The external forcing blocks in the external forcing file."""

    @classmethod
    def _ext(cls) -> str:
        return ".ext"

    @classmethod
    def _filename(cls) -> str:
        return "externalforcings"

    def dict(self, *args, **kwargs):
        return dict(comment=self.comment, forcing=[dict(f) for f in self.forcing])

    @classmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, SerializerConfig, ModelSaveSettings], None]:
        return Serializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return Parser.parse
