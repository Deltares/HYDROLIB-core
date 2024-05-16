from typing import Optional, Literal

from pydantic.v1 import Field

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm import Geometry, FMModel
from hydrolib.core.dflowfm.ini.models import INIBasedModel


class ResearchGeometry(Geometry):
    class Comments(Geometry.Comments):
        toplayminthick: Optional[str] = Field(
            "Minimum top layer thickness(m), only for Z-layers.",
            alias="topLayMinThick",
        )

    comments: Comments = Comments()

    toplayminthick: Optional[float] = Field(None, alias="topLayMinThick")

class ResearchSedtrails(INIBasedModel):
    class Comments(INIBasedModel.Comments):
        sedtrailsoutputfile: Optional[str] = Field(
            "Sedtrails time-avgd output file.",
            alias="sedtrailsOutputFile",
        )

    comments: Comments = Comments()

    _header: Literal["Sedtrails"] = "Sedtrails"

    sedtrailsoutputfile: Optional[DiskOnlyFileModel] = Field(default=None, alias="sedtrailsOutputFile")


class ResearchFMModel(FMModel):
    geometry: ResearchGeometry = Field(default_factory=ResearchGeometry)
    sedtrails: Optional[ResearchSedtrails] = Field(None)

