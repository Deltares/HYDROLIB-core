from pydantic import Field
from pyparsing import Optional

from hydrolib.core.basemodel import BaseModel, DiskOnlyFileModel


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

    filetype: int = Field(alias="FILETYPE")
    """int: Indication of the file type.
    
    Options:
    1. Time series
    2. Time series magnitude and direction
    3. Spatially varying weather
    4. ArcInfo
    5. Spiderweb data (cyclones)
    6. Curvilinear data
    7. Samples (C.3)
    8. Triangulation magnitude and direction
    9. Polyline (<∗.pli>-file, C.2)
    11. NetCDF grid data (e.g. meteo fields)
    14. NetCDF wave data
    """

    method: int = Field(alias="METHOD")
    """int: The method of interpolation.
    
    Options:
    1. Pass through (no interpolation)
    2. Interpolate time and space
    3. Interpolate time and space, save weights
    4. Interpolate space
    5. Interpolate time
    7. Interpolate/Extrapolate time
    """

    operand: str = Field(alias="OPERAND")
    """str: Overwriting or superimposing values already set for this quantity:
    'O' Values are overwritten.
    '+' New value is superimposed.
    """

    value: Optional[float] = Field(None, alias="SOURCEMASK")
    """Optional[float]: custom coefficients for transformation."""

    factor: Optional[float] = Field(None, alias="SOURCEMASK")
    """Optional[float]: The factor."""

    ifrctyp: Optional[float] = Field(None, alias="SOURCEMASK")
    """Optional[float]: The friction type."""

    averagingtype: Optional[float] = Field(None, alias="SOURCEMASK")
    """Optional[float]: The averging type."""

    relativesearchcellsize: Optional[float] = Field(None, alias="SOURCEMASK")
    """Optional[float]: The relative search cell size."""

    extrapoltol: Optional[float] = Field(None, alias="SOURCEMASK")
    """Optional[float]: The extrapolation tolerance."""

    area: Optional[float] = Field(None, alias="SOURCEMASK")
    """Optional[float]: The area for sources and sinks."""
