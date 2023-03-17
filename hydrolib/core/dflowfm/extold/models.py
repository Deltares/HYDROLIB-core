from enum import Enum, IntEnum

from pydantic import Field
from pyparsing import Optional

from hydrolib.core.basemodel import BaseModel, DiskOnlyFileModel


class Quantity:
    """Class contains the different external forcing category classes."""

    class QuantityBase(str, Enum):
        pass

    class Bnd(QuantityBase):
        """Enum class containing the valid values for the boundary conditions category
        of the external forcings.
        """

        WaterLevel = "waterlevelbnd"
        """Water level"""
        Neumann = "neumannbnd"
        """Water level gradient"""
        Riemann = "riemannbnd"
        """Riemann invariant"""
        Outflow = "outflowbnd"
        """Outflow"""
        Velocity = "velocitybnd"
        """Velocity"""
        Discharge = "dischargebnd"
        """Discharge"""
        RiemannVelocity = "riemann_velocitybnd"
        """Riemann invariant velocity"""
        Salinity = "salinitybnd"
        """Salinity"""
        Temperature = "temperaturebnd"
        """Temperature"""
        Sediment = "sedimentbnd"
        """Suspended sediment"""
        uxuyAdvectionVelocity = "uxuyadvectionvelocitybnd"
        """ux-uy advection velocity"""
        NormalVelocity = "normalvelocitybnd"
        """Normal velocity"""
        TangentialVelocity = "tangentialvelocitybnd"
        """Tangentional velocity"""
        Qh = "qhbnd"
        """Discharge-water level dependency"""
        Tracer = "tracerbnd"
        """User-defined tracer"""


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

    quantity: str = Field(alias="QUANTITY")
    """str: The name of the quantity."""

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
