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
        helmert: Optional[str] = Field(
            "Use Helmert (0: no, 1: yes).",
            alias="helmert",
        )
        waterdepthini1d: Optional[str] = Field(
            "Initial waterdepth in 1D.",
            alias="waterDepthIni1d",
        )
        zlayeratubybob: Optional[str] = Field(
            "Lowest connected cells governed by bob instead of by bL L/R.",
            alias="zLayerAtuByBob",
        )
        shipdeffile: Optional[str] = Field(
            "File *.shd containing ship definitions.",
            alias="shipDefFile",
        )
        stripmesh: Optional[str] = Field(
            "Strip unused nodes and links from the mesh after clipping (1: strip, 0: do not strip).",
            alias="stripMesh",
        )
        bedwavelength: Optional[str] = Field(
            "Bed testcases.",
            alias="bedWaveLength",
        )
        removesmalllinkstrsh: Optional[str] = Field(
            "0.1	0-1, 0= no removes.",
            alias="removeSmallLinksTrsh",
        )
        createlinks1d2d: Optional[str] = Field(
            "Ruecksichtslos create links between 1D nodes and 2D cells when initializing model (1: yes, 0: no).",
            alias="createLinks1d2d",
        )
        bedwaveamplitude: Optional[str] = Field(
            "Bed testcases.",
            alias="bedWaveAmplitude",
        )
        uniformhu: Optional[str] = Field(
            "Waterdepth in rigid-lid-like solution.",
            alias="uniformhu",
        )
        tsigma: Optional[str] = Field(
            "Sigma Adaptation period for Layertype==4 (s).",
            alias="tSigma",
        )
        dpuopt: Optional[str] = Field(
            "Bed level interpolation at velocity point in case of tile approach bed level: 1 = max (default); 2 = mean.",
            alias="dpuopt",
        )
        ihuzcsig: Optional[str] = Field(
            "ihuzcsig",
            alias="ihuzcsig",
        )
        ihuz: Optional[str] = Field(
            "ihuz",
            alias="ihuz",
        )
        cosphiutrsh: Optional[str] = Field(
            "0-1, 1= no bad orthos.",
            alias="cosphiutrsh",
        )
        cutcelllist: Optional[str] = Field(
            "File with names of cutcell polygons, e.g. cutcellpolygons.lst.",
            alias="cutCellList",
        )
        uniformtyp1d: Optional[str] = Field(
            "Uniform type for channel profiles not specified by profloc.",
            alias="uniformTyp1d",
        )
        oned2dinternallinktype: Optional[str] = Field(
            "Link treatment method for type-3 internal links.",
            alias="oned2dInternalLinkType",
        )
        orgfloorlevtoplaydef: Optional[str] = Field(
            "Keep original definition of Floor level of top layer.",
            alias="orgFloorLevelTopLayDef",
        )
        pipefile: Optional[str] = Field(
            "File *.pliz containing pipe-based 'culverts'.",
            alias="pipeFile",
        )
        groundlayerthickness: Optional[str] = Field(
            "Only in pipes: groundlayer thickness (m).",
            alias="groundLayerThickness",
        )

    comments: Comments = Comments()

    toplayminthick: Optional[float] = Field(None, alias="topLayMinThick")
    helmert: Optional[bool] = Field(None, alias="helmert")
    waterdepthini1d: Optional[float] = Field(None, alias="waterDepthIni1d")
    zlayeratubybob: Optional[int] = Field(None, alias="zLayerAtuByBob")
    shipdeffile: Optional[DiskOnlyFileModel] = Field(None, alias="shipDefFile")
    stripmesh: Optional[bool] = Field(None, alias="stripMesh")
    bedwavelength: Optional[float] = Field(None, alias="bedWaveLength")
    removesmalllinkstrsh: Optional[float] = Field(None, alias="removeSmallLinksTrsh")
    createlinks1d2d: Optional[bool] = Field(None, alias="createLinks1d2d")
    bedwaveamplitude: Optional[float] = Field(None, alias="bedWaveAmplitude")
    uniformhu: Optional[float] = Field(None, alias="uniformhu")
    tsigma: Optional[float] = Field(None, alias="tSigma")
    dpuopt: Optional[int] = Field(None, alias="dpuopt")
    ihuzcsig: Optional[int] = Field(None, alias="ihuzcsig")
    ihuz: Optional[int] = Field(None, alias="ihuz")
    cosphiutrsh: Optional[float] = Field(None, alias="cosphiutrsh")
    cutcelllist: Optional[DiskOnlyFileModel] = Field(None, alias="cutCellList")
    uniformtyp1d: Optional[int] = Field(None, alias="uniformTyp1d")
    oned2dinternallinktype: Optional[int] = Field(None, alias="oned2dInternalLinkType")
    orgfloorlevtoplaydef: Optional[bool] = Field(None, alias="orgFloorLevelTopLayDef")
    pipefile: Optional[DiskOnlyFileModel] = Field(None, alias="pipeFile")
    groundlayerthickness: Optional[float] = Field(None, alias="groundLayerThickness")


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

