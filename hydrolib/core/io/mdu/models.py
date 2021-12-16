from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

from pydantic import Field

from hydrolib.core.basemodel import FileModel, ResolveRelativeMode
from hydrolib.core.io.crosssection.models import CrossDefModel, CrossLocModel
from hydrolib.core.io.ext.models import ExtModel
from hydrolib.core.io.friction.models import FrictionModel
from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.util import get_split_string_on_delimiter_validator
from hydrolib.core.io.inifield.models import IniFieldModel
from hydrolib.core.io.net.models import NetworkModel
from hydrolib.core.io.polyfile.models import PolyFile
from hydrolib.core.io.storagenode.models import StorageNodeModel
from hydrolib.core.io.structure.models import StructureModel
from hydrolib.core.io.xyz.models import XYZModel


class General(INIGeneral):
    _header: Literal["General"] = "General"
    program: str = Field("D-Flow FM", alias="program")
    version: str = Field("1.2.94.66079M", alias="version")
    filetype: Literal["modelDef"] = Field("modelDef", alias="fileType")
    fileversion: str = Field("1.09", alias="fileVersion")
    autostart: bool = Field(False, alias="autoStart")
    pathsrelativetoparent: bool = Field(False, alias="pathsRelativeToParent")


class Numerics(INIBasedModel):
    """
    The `[Numerics]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.numerics`.

    All lowercased attributes match with the [Numerics] input as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.A).
    """

    _header: Literal["Numerics"] = "Numerics"
    cflmax: float = Field(0.7, alias="cflMax")
    advectype: int = Field(33, alias="advecType")
    timesteptype: int = Field(2, alias="timeStepType")
    limtyphu: int = Field(0, alias="limTypHu")
    limtypmom: int = Field(4, alias="limTypMom")
    limtypsa: int = Field(4, alias="limTypSa")
    icgsolver: int = Field(4, alias="icgSolver")
    maxdegree: int = Field(6, alias="maxDegree")
    fixedweirscheme: int = Field(9, alias="fixedWeirScheme")
    fixedweircontraction: float = Field(1.0, alias="fixedWeirContraction")
    izbndpos: int = Field(0, alias="izBndPos")
    tlfsmo: float = Field(0.0, alias="tlfSmo")
    slopedrop2d: float = Field(0.0, alias="slopeDrop2D")
    drop1d: bool = Field(False, alias="drop1D")
    chkadvd: float = Field(0.1, alias="chkAdvd")
    teta0: float = Field(0.55, alias="teta0")
    qhrelax: float = Field(0.01, alias="qhRelax")
    cstbnd: bool = Field(False, alias="cstBnd")
    maxitverticalforestersal: int = Field(0, alias="maxitVerticalForesterSal")
    maxitverticalforestertem: int = Field(0, alias="maxitVerticalForesterTem")
    turbulencemodel: int = Field(3, alias="turbulenceModel")
    turbulenceadvection: int = Field(3, alias="turbulenceAdvection")
    anticreep: bool = Field(False, alias="antiCreep")
    maxwaterleveldiff: float = Field(0.0, alias="maxWaterLevelDiff")
    maxvelocitydiff: float = Field(0.0, alias="maxVelocityDiff")
    epshu: float = Field(0.0001, alias="epsHu")


class VolumeTables(INIBasedModel):
    """
    The `[VolumeTables]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.volumetables`.

    All lowercased attributes match with the [VolumeTables] input as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.A).
    """

    _header: Literal["VolumeTables"] = "VolumeTables"
    usevolumetables: bool = Field(False, alias="useVolumeTables")
    increment: float = Field(0.2, alias="increment")
    usevolumetablefile: bool = Field(False, alias="useVolumeTableFile")


class Physics(INIBasedModel):
    """
    The `[Physics]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.physics`.

    All lowercased attributes match with the [Physics] input as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.A).
    """

    _header: Literal["Physics"] = "Physics"
    uniffrictcoef: float = Field(0.023, alias="unifFrictCoef")
    uniffricttype: int = Field(1, alias="unifFrictType")
    uniffrictcoef1d: float = Field(0.023, alias="unifFrictCoef1D")
    uniffrictcoeflin: float = Field(0.0, alias="unifFrictCoefLin")
    umodlin: int = Field(0, alias="umodLin")
    vicouv: float = Field(0.1, alias="vicouv")
    dicouv: float = Field(0.1, alias="dicouv")
    vicoww: float = Field(5e-05, alias="vicoww")
    dicoww: float = Field(5e-05, alias="dicoww")
    vicwminb: float = Field(0.0, alias="vicwminb")
    xlozmidov: float = Field(0.0, alias="xlozmidov")
    smagorinsky: float = Field(0.2, alias="smagorinsky")
    elder: float = Field(0.0, alias="elder")
    irov: int = Field(0, alias="irov")
    wall_ks: float = Field(0.0, alias="wall_ks")
    rhomean: float = Field(1000, alias="rhomean")
    idensform: int = Field(2, alias="idensform")
    ag: float = Field(9.81, alias="ag")
    tidalforcing: bool = Field(False, alias="tidalForcing")
    doodsonstart: float = Field(55.565, alias="doodsonStart")
    doodsonstop: float = Field(375.575, alias="doodsonStop")
    doodsoneps: float = Field(0.0, alias="doodsonEps")
    villemontecd1: float = Field(1.0, alias="villemonteCD1")
    villemontecd2: float = Field(10.0, alias="villemonteCD2")
    salinity: bool = Field(False, alias="salinity")
    initialsalinity: float = Field(0.0, alias="initialSalinity")
    sal0abovezlev: float = Field(-999.0, alias="sal0AboveZLev")
    deltasalinity: float = Field(-999.0, alias="deltaSalinity")
    backgroundsalinity: float = Field(30.0, alias="backgroundSalinity")
    temperature: int = Field(0, alias="temperature")
    initialtemperature: float = Field(6.0, alias="initialTemperature")
    backgroundwatertemperature: float = Field(6.0, alias="backgroundWaterTemperature")
    secchidepth: float = Field(2.0, alias="secchiDepth")
    stanton: float = Field(0.0013, alias="stanton")
    dalton: float = Field(0.0013, alias="dalton")
    secondaryflow: bool = Field(False, alias="secondaryFlow")
    betaspiral: int = Field(0, alias="betaSpiral")


class Sediment(INIBasedModel):
    _header: Literal["Sediment"] = "Sediment"
    sedimentmodelnr: Optional[int] = Field(alias="Sedimentmodelnr")
    morfile: Optional[str] = Field(alias="MorFile")
    sedfile: Optional[str] = Field(alias="SedFile")


class Wind(INIBasedModel):
    """
    The `[Wind]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.wind`.

    All lowercased attributes match with the [Wind] input as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.A).
    """

    _header: Literal["Wind"] = "Wind"
    icdtyp: int = Field(2, alias="icdTyp")
    cdbreakpoints: List[float] = Field([0.00063, 0.00723], alias="cdBreakpoints")
    windspeedbreakpoints: List[float] = Field(
        [0.0, 100.0], alias="windSpeedBreakpoints"
    )
    rhoair: float = Field(1.205, alias="rhoAir")
    relativewind: bool = Field(False, alias="relativeWind")
    windpartialdry: bool = Field(True, alias="windPartialDry")
    pavbnd: float = Field(0.0, alias="pavBnd")
    pavini: float = Field(0.0, alias="pavIni")

    @classmethod
    def list_delimiter(cls) -> str:
        return " "

    _split_to_list = get_split_string_on_delimiter_validator(
        "cdbreakpoints",
        "windspeedbreakpoints",
    )


class Waves(INIBasedModel):
    """
    The `[Waves]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.waves`.

    All lowercased attributes match with the [Waves] input as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.A).
    """

    _header: Literal["Waves"] = "Waves"
    wavemodelnr: int = Field(3, alias="waveModelNr")
    rouwav: str = Field("FR84", alias="rouWav")
    gammax: float = Field(0.5, alias="gammaX")


class Time(INIBasedModel):
    """
    The `[Time]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.time`.

    All lowercased attributes match with the [Time] input as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.A).
    """

    _header: Literal["Time"] = "Time"
    refdate: int = Field(20200101, alias="refDate")  # TODO Convert to datetime
    tzone: float = Field(0.0, alias="tZone")
    tunit: str = Field("S", alias="tUnit")  # DHMS
    dtuser: float = Field(300.0, alias="dtUser")
    dtnodal: float = Field(21600.0, alias="dtNodal")
    dtmax: float = Field(30.0, alias="dtMax")
    dtinit: float = Field(1.0, alias="dtInit")
    tstart: float = Field(0.0, alias="tStart")
    tstop: float = Field(86400.0, alias="tStop")
    updateroughnessinterval: float = Field(86400.0, alias="updateRoughnessInterval")


class Restart(INIBasedModel):
    """
    The `[Restart]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.restart`.

    All lowercased attributes match with the [Restart] input as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.A).
    """

    _header: Literal["Restart"] = "Restart"
    restartfile: Optional[Path] = Field(None, alias="restartFile")
    restartdatetime: Optional[str] = Field(None, alias="restartDateTime")


class ExternalForcing(INIBasedModel):
    """
    The `[External Forcing]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.external_forcing`.

    All lowercased attributes match with the [External Forcing] input as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.A).
    """

    _header: Literal["External Forcing"] = "External Forcing"
    extforcefile: Optional[Path] = Field(None, alias="extForceFile")
    extforcefilenew: Optional[ExtModel] = Field(None, alias="extForceFileNew")
    rainfall: Optional[bool] = Field(None, alias="rainfall")
    qext: Optional[bool] = Field(None, alias="qExt")
    evaporation: Optional[bool] = Field(None, alias="evaporation")
    windext: Optional[int] = Field(None, alias="windExt")

    def is_intermediate_link(self) -> bool:
        return True


class Hydrology(INIBasedModel):
    """
    The `[Hydrology]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.hydrology`.

    All lowercased attributes match with the [Hydrology] input as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.A).
    """

    _header: Literal["Hydrology"] = "Hydrology"
    interceptionmodel: bool = Field(False, alias="interceptionModel")


class Trachytopes(INIBasedModel):
    """
    The `[Trachytopes]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.trachytopes`.

    All lowercased attributes match with the [Trachytopes] input as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.A).
    """

    _header: Literal["Trachytopes"] = "Trachytopes"
    trtrou: str = Field("N", alias="trtRou")  # TODO bool
    trtdef: Optional[int] = Field(None, alias="trtDef")  # no doc?
    trtl: Optional[int] = Field(None, alias="trtL")  # no doc?
    dttrt: float = Field(60.0, alias="dtTrt")


class Output(INIBasedModel):
    """
    The `[Output]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.output`.

    All lowercased attributes match with the [Output] input as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.A).
    """

    _header: Literal["Output"] = "Output"
    wrishp_crs: bool = Field(False, alias="wrishp_crs")
    wrishp_weir: bool = Field(False, alias="wrishp_weir")
    wrishp_gate: bool = Field(False, alias="wrishp_gate")
    wrishp_fxw: bool = Field(False, alias="wrishp_fxw")
    wrishp_thd: bool = Field(False, alias="wrishp_thd")
    wrishp_obs: bool = Field(False, alias="wrishp_obs")
    wrishp_emb: bool = Field(False, alias="wrishp_emb")
    wrishp_dryarea: bool = Field(False, alias="wrishp_dryArea")
    wrishp_enc: bool = Field(False, alias="wrishp_enc")
    wrishp_src: bool = Field(False, alias="wrishp_src")
    wrishp_pump: bool = Field(False, alias="wrishp_pump")
    outputdir: Optional[Path] = Field(None, alias="outputDir")
    waqoutputdir: Optional[Path] = Field(None, alias="waqOutputDir")
    flowgeomfile: Optional[Path] = Field(None, alias="flowGeomFile")
    obsfile: Optional[List[Path]] = Field(None, alias="obsFile")
    crsfile: Optional[List[Path]] = Field(None, alias="crsFile")
    hisfile: Optional[Path] = Field(None, alias="hisFile")
    hisinterval: List[float] = Field([300], alias="hisInterval")
    xlsinterval: List[float] = Field([0.0], alias="xlsInterval")
    mapfile: Optional[Path] = Field(None, alias="mapFile")
    mapinterval: List[float] = Field([1200.0], alias="mapInterval")
    rstinterval: List[float] = Field([0.0], alias="rstInterval")
    mapformat: int = Field(4, alias="mapFormat")
    ncformat: int = Field(3, alias="ncFormat")
    ncnounlimited: bool = Field(False, alias="ncNoUnlimited")
    ncnoforcedflush: bool = Field(False, alias="ncNoForcedFlush")
    ncwritelatlon: bool = Field(False, alias="ncWriteLatLon")

    # his file
    wrihis_balance: bool = Field(True, alias="wrihis_balance")
    wrihis_sourcesink: bool = Field(True, alias="wrihis_sourceSink")
    wrihis_structure_gen: bool = Field(True, alias="wrihis_structure_gen")
    wrihis_structure_dam: bool = Field(True, alias="wrihis_structure_dam")
    wrihis_structure_pump: bool = Field(True, alias="wrihis_structure_pump")
    wrihis_structure_gate: bool = Field(True, alias="wrihis_structure_gate")
    wrihis_structure_weir: bool = Field(True, alias="wrihis_structure_weir")
    wrihis_structure_orifice: bool = Field(True, alias="wrihis_structure_orifice")
    wrihis_structure_bridge: bool = Field(True, alias="wrihis_structure_bridge")
    wrihis_structure_culvert: bool = Field(True, alias="wrihis_structure_culvert")
    wrihis_structure_longculvert: bool = Field(
        True, alias="wrihis_structure_longCulvert"
    )
    wrihis_structure_dambreak: bool = Field(True, alias="wrihis_structure_damBreak")
    wrihis_structure_uniweir: bool = Field(True, alias="wrihis_structure_uniWeir")
    wrihis_structure_compound: bool = Field(True, alias="wrihis_structure_compound")
    wrihis_lateral: bool = Field(True, alias="wrihis_lateral")
    wrihis_velocity: bool = Field(False, alias="wrihis_velocity")
    wrihis_discharge: bool = Field(False, alias="wrihis_discharge")

    # Map file
    wrimap_waterlevel_s0: bool = Field(True, alias="wrimap_waterLevel_s0")
    wrimap_waterlevel_s1: bool = Field(True, alias="wrimap_waterLevel_s1")
    wrimap_evaporation: bool = Field(True, alias="wrimap_evaporation")
    wrimap_velocity_component_u0: bool = Field(
        True, alias="wrimap_velocity_component_u0"
    )
    wrimap_velocity_component_u1: bool = Field(
        True, alias="wrimap_velocity_component_u1"
    )
    wrimap_velocity_vector: bool = Field(True, alias="wrimap_velocity_vector")
    wrimap_upward_velocity_component: bool = Field(
        False, alias="wrimap_upward_velocity_component"
    )
    wrimap_density_rho: bool = Field(True, alias="wrimap_density_rho")
    wrimap_horizontal_viscosity_viu: bool = Field(
        True, alias="wrimap_horizontal_viscosity_viu"
    )
    wrimap_horizontal_diffusivity_diu: bool = Field(
        True, alias="wrimap_horizontal_diffusivity_diu"
    )
    wrimap_flow_flux_q1: bool = Field(True, alias="wrimap_flow_flux_q1")
    wrimap_spiral_flow: bool = Field(True, alias="wrimap_spiral_flow")
    wrimap_numlimdt: bool = Field(True, alias="wrimap_numLimdt")
    wrimap_taucurrent: bool = Field(True, alias="wrimap_tauCurrent")
    wrimap_chezy: bool = Field(True, alias="wrimap_chezy")
    wrimap_turbulence: bool = Field(True, alias="wrimap_turbulence")
    wrimap_rain: bool = Field(False, alias="wrimap_rain")
    wrimap_wind: bool = Field(True, alias="wrimap_wind")
    wrimap_heat_fluxes: bool = Field(False, alias="wrimap_heat_fluxes")
    wrimap_wet_waterdepth_threshold: float = Field(
        2e-5, alias="wrimap_wet_waterDepth_threshold"
    )
    wrimap_time_water_on_ground: bool = Field(
        False, alias="wrimap_time_water_on_ground"
    )
    wrimap_freeboard: bool = Field(False, alias="wrimap_freeboard")
    wrimap_waterdepth_on_ground: bool = Field(
        False, alias="wrimap_waterDepth_on_ground"
    )
    wrimap_volume_on_ground: bool = Field(False, alias="wrimap_volume_on_ground")
    wrimap_total_net_inflow_1d2d: bool = Field(
        False, alias="wrimap_total_net_inflow_1d2d"
    )
    wrimap_total_net_inflow_lateral: bool = Field(
        False, alias="wrimap_total_net_inflow_lateral"
    )
    wrimap_water_level_gradient: bool = Field(
        False, alias="wrimap_water_level_gradient"
    )
    wrimap_flow_analysis: bool = Field(False, alias="wrimap_flow_analysis")
    mapoutputtimevector: Optional[Path] = Field(None, alias="mapOutputTimeVector")
    fullgridoutput: bool = Field(False, alias="fullGridOutput")
    eulervelocities: bool = Field(False, alias="eulerVelocities")
    classmapfile: Optional[Path] = Field(None, alias="classMapFile")
    waterlevelclasses: List[float] = Field([0.0], alias="waterLevelClasses")
    waterdepthclasses: List[float] = Field([0.0], alias="waterDepthClasses")
    classmapinterval: List[float] = Field([0.0], alias="classMapInterval")
    waqinterval: List[float] = Field([0.0], alias="waqInterval")
    statsinterval: List[float] = Field([0.0], alias="statsInterval")
    writebalancefile: bool = Field(False, alias="writeBalanceFile")
    timingsinterval: List[float] = Field([0.0], alias="timingsInterval")
    richardsononoutput: bool = Field(True, alias="richardsonOnOutput")

    _split_to_list = get_split_string_on_delimiter_validator(
        "waterlevelclasses",
        "waterdepthclasses",
        "crsfile",
        "obsfile",
        delimiter=";",
    )
    _split_to_list2 = get_split_string_on_delimiter_validator(
        "hisinterval",
        "xlsinterval",
        "mapinterval",
        "rstinterval",
        "classmapinterval",
        "waqinterval",
        "statsinterval",
        "timingsinterval",
        delimiter=" ",
    )

    def is_intermediate_link(self) -> bool:
        # TODO set to True once we replace Paths with FileModels
        return False


class Geometry(INIBasedModel):
    """
    The `[Geometry]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry`.

    All lowercased attributes match with the [Geometry] input as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.A).
    """

    _header: Literal["Geometry"] = "Geometry"
    netfile: Optional[NetworkModel] = Field(
        default_factory=NetworkModel, alias="netFile"
    )
    bathymetryfile: Optional[XYZModel] = Field(None, alias="bathymetryFile")
    drypointsfile: Optional[List[Union[XYZModel, PolyFile]]] = Field(
        None, alias="dryPointsFile"
    )  # TODO Fix, this will always try XYZ first, alias="]")
    structurefile: Optional[List[StructureModel]] = Field(None, alias="structureFile")
    inifieldfile: Optional[IniFieldModel] = Field(None, alias="iniFieldFile")
    waterlevinifile: Optional[Path] = Field(None, alias="waterLevIniFile")
    landboundaryfile: Optional[List[Path]] = Field(None, alias="landBoundaryFile")
    thindamfile: Optional[List[PolyFile]] = Field(None, alias="thinDamFile")
    fixedweirfile: Optional[List[PolyFile]] = Field(None, alias="fixedWeirFile")
    pillarfile: Optional[List[PolyFile]] = Field(None, alias="pillarFile")
    usecaching: bool = Field(False, alias="useCaching")
    vertplizfile: Optional[PolyFile] = Field(None, alias="vertPlizFile")
    frictfile: Optional[List[FrictionModel]] = Field(None, alias="frictFile")
    crossdeffile: Optional[CrossDefModel] = Field(None, alias="crossDefFile")
    crosslocfile: Optional[CrossLocModel] = Field(None, alias="crossLocFile")
    storagenodefile: Optional[StorageNodeModel] = Field(None, alias="storageNodeFile")
    onedtwodlinkfile: Optional[Path] = Field(None, alias="1d2dLinkFile")
    proflocfile: Optional[Path] = Field(None, alias="profLocFile")
    profdeffile: Optional[Path] = Field(None, alias="profDefFile")
    profdefxyzfile: Optional[Path] = Field(None, alias="profDefXyzFile")
    manholefile: Optional[Path] = Field(None, alias="manholeFile")
    partitionfile: Optional[PolyFile] = Field(None, alias="partitionFile")
    uniformwidth1d: float = Field(2.0, alias="uniformWidth1D")
    waterlevini: float = Field(0.0, alias="waterLevIni")
    bedlevuni: float = Field(-5.0, alias="bedLevUni")
    bedslope: float = Field(0.0, alias="bedSlope")
    bedlevtype: int = Field(3, alias="bedLevType")
    blmeanbelow: float = Field(-999.0, alias="blMeanBelow")
    blminabove: float = Field(-999.0, alias="blMinAbove")
    anglat: float = Field(0.0, alias="angLat")
    anglon: float = Field(0.0, alias="angLon")
    conveyance2d: int = Field(-1, alias="conveyance2D")
    nonlin1d: int = Field(1, alias="nonlin1D")
    nonlin2d: int = Field(0, alias="nonlin2D")
    sillheightmin: float = Field(0.0, alias="sillHeightMin")
    makeorthocenters: bool = Field(False, alias="makeOrthoCenters")
    dcenterinside: float = Field(1.0, alias="dCenterInside")
    bamin: float = Field(1e-06, alias="baMin")
    openboundarytolerance: float = Field(3.0, alias="openBoundaryTolerance")
    renumberflownodes: bool = Field(True, alias="renumberFlowNodes")
    kmx: int = Field(0, alias="kmx")
    layertype: int = Field(1, alias="layerType")
    numtopsig: int = Field(0, alias="numTopSig")
    sigmagrowthfactor: float = Field(1.0, alias="sigmaGrowthFactor")
    dxdoubleat1dendnodes: bool = Field(True, alias="dxDoubleAt1DEndNodes")
    changevelocityatstructures: bool = Field(False, alias="changeVelocityAtStructures")
    changestructuredimensions: bool = Field(True, alias="changeStructureDimensions")

    _split_to_list = get_split_string_on_delimiter_validator(
        "frictfile",
        "structurefile",
        "drypointsfile",
        "landboundaryfile",
        "thindamfile",
        "fixedweirfile",
        "pillarfile",
        delimiter=";",
    )

    def is_intermediate_link(self) -> bool:
        return True


class FMModel(INIModel):
    """
    The overall FM model that contains the contents of the toplevel MDU file.

    All lowercased attributes match with the supported "[section]"s as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#subsection.A).

    Each of these class attributes refers to an underlying model class for that particular section.
    """

    general: General = Field(default_factory=General)
    geometry: Geometry = Field(default_factory=Geometry)
    volumetables: VolumeTables = Field(default_factory=VolumeTables)
    numerics: Numerics = Field(default_factory=Numerics)
    physics: Physics = Field(default_factory=Physics)
    sediment: Sediment = Field(default_factory=Sediment)
    wind: Wind = Field(default_factory=Wind)
    waves: Optional[Waves] = None
    time: Time = Field(default_factory=Time)
    restart: Restart = Field(default_factory=Restart)
    external_forcing: ExternalForcing = Field(default_factory=ExternalForcing)
    hydrology: Hydrology = Field(default_factory=Hydrology)
    trachytopes: Trachytopes = Field(default_factory=Trachytopes)
    output: Output = Field(default_factory=Output)

    @classmethod
    def _ext(cls) -> str:
        return ".mdu"

    @classmethod
    def _filename(cls) -> str:
        return "fm"

    @FileModel._relative_mode.getter
    def _relative_mode(self) -> ResolveRelativeMode:
        # This method overrides the _relative_mode property of the FileModel:
        # The FMModel has a "special" feature which determines how relative filepaths
        # should be resolved. When the field "pathsRelativeToParent" is set to False
        # all relative paths should be resolved in respect to the parent directory of
        # the mdu file. As such we need to explicitly set the resolve mode to ToAnchor
        # when this attribute is set.

        if not hasattr(self, "general") or self.general is None:
            return ResolveRelativeMode.ToParent

        if self.general.pathsrelativetoparent:
            return ResolveRelativeMode.ToParent
        else:
            return ResolveRelativeMode.ToAnchor
