from typing import Optional, Literal

from pydantic.v1 import Field

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm import Geometry, FMModel, General
from hydrolib.core.dflowfm.ini.models import INIBasedModel


class ResearchGeneral(General):
    class Comments(General.Comments):
        modelspecific: Optional[str] = Field(
            "Optional 'model specific ID', to enable certain custom runtime function calls (instead of via MDU name).",
            alias="modelspecific",
        )
        inputspecific: Optional[str] = Field(
            "Use of hardcoded specific inputs, shall not be used by users (0: no, 1: yes).",
            alias="inputspecific",
        )

    comments: Comments = Comments()

    modelspecific: Optional[str] = Field(None, alias="modelspecific")
    inputspecific: Optional[bool] = Field(None, alias="inputspecific")


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
    general: ResearchGeneral = Field(default_factory=ResearchGeneral)
    geometry: ResearchGeometry = Field(default_factory=ResearchGeometry)
    sedtrails: Optional[ResearchSedtrails] = Field(None)

