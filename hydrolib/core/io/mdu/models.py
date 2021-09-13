from hydrolib.core.io.net.models import NetworkModel
from pathlib import Path
from typing import Callable, List, Literal, Optional, Union
from pydantic import Field
from hydrolib.core.basemodel import FileModel
from hydrolib.core.io.base import DummySerializer
from hydrolib.core.io.bc.models import ForcingModel
from hydrolib.core.io.ini.models import (
    CrossDefModel,
    CrossLocModel,
    FrictionModel,
    INIBasedModel,
    INIGeneral,
    INIModel,
)
from hydrolib.core.io.ini.parser import Parser
from hydrolib.core.io.ini.serializer import SerializerConfig, write_ini
from hydrolib.core.io.ini.util import (
    get_split_string_on_delimiter_validator,
    make_list_validator,
)
from hydrolib.core.io.polyfile.models import PolyFile
from hydrolib.core.io.structure.models import StructureModel
from hydrolib.core.io.xyz.models import XYZModel


class General(INIBasedModel):
    _header: Literal["general"] = "general"
    program: str = Field("D-Flow FM", alias="Program")
    version: str = Field("1.2.94.66079M", alias="Version")
    filetype: Literal["modelDef"] = Field("modelDef", alias="fileType")
    fileversion: str = Field("1.09", alias="fileVersion")
    autostart: bool = Field(False, alias="AutoStart")
    pathsrelativetoparent: bool = Field(False, alias="PathsRelativeToParent")


class Numerics(INIBasedModel):
    _header: Literal["numerics"] = "numerics"
    cflmax: float = Field(0.7, alias="CFLMax")
    advectype: int = Field(33, alias="AdvecType")
    timesteptype: int = Field(2, alias="TimeStepType")
    limtyphu: int = Field(0, alias="Limtyphu")
    limtypmom: int = Field(4, alias="Limtypmom")
    limtypsa: int = Field(4, alias="Limtypsa")
    icgsolver: int = Field(4, alias="Icgsolver")
    maxdegree: int = Field(6, alias="Maxdegree")
    fixedweirscheme: int = Field(9, alias="FixedWeirScheme")
    fixedweircontraction: float = Field(1.0, alias="FixedWeirContraction")
    izbndpos: int = Field(0, alias="Izbndpos")
    tlfsmo: float = Field(0.0, alias="Tlfsmo")
    slopedrop2d: float = Field(0.0, alias="Slopedrop2D")
    drop1d: bool = Field(False, alias="drop1D")
    chkadvd: float = Field(0.1, alias="Chkadvd")
    teta0: float = Field(0.55, alias="Teta0")
    qhrelax: float = Field(0.01, alias="Qhrelax")
    cstbnd: bool = Field(False, alias="cstbnd")
    maxitverticalforestersal: int = Field(0, alias="Maxitverticalforestersal")
    maxitverticalforestertem: int = Field(0, alias="Maxitverticalforestertem")
    turbulencemodel: int = Field(3, alias="Turbulencemodel")
    turbulenceadvection: int = Field(3, alias="Turbulenceadvection")
    anticreep: bool = Field(False, alias="AntiCreep")
    maxwaterleveldiff: float = Field(0.0, alias="Maxwaterleveldiff")
    maxvelocitydiff: float = Field(0.0, alias="Maxvelocitydiff")
    epshu: float = Field(0.0001, alias="Epshu")


class VolumeTables(INIBasedModel):
    _header: Literal["volumeTables"] = "volumeTables"
    usevolumetables: bool = Field(False, alias="useVolumeTables")
    increment: float = Field(0.2, alias="increment")
    usevolumetablefile: bool = Field(False, alias="useVolumeTableFile")


class Physics(INIBasedModel):
    _header: Literal["physics"] = "physics"
    uniffrictcoef: float = Field(0.023, alias="UnifFrictCoef")
    uniffricttype: int = Field(1, alias="UnifFrictType")
    uniffrictcoef1d: float = Field(0.023, alias="UnifFrictCoef1D")
    uniffrictcoeflin: float = Field(0.0, alias="UnifFrictCoefLin")
    umodlin: int = Field(0, alias="Umodlin")
    vicouv: float = Field(0.1, alias="Vicouv")
    dicouv: float = Field(0.1, alias="Dicouv")
    vicoww: float = Field(5e-05, alias="Vicoww")
    dicoww: float = Field(5e-05, alias="Dicoww")
    vicwminb: float = Field(0.0, alias="Vicwminb")
    xlozmidov: float = Field(0.0, alias="Xlozmidov")
    smagorinsky: float = Field(0.2, alias="Smagorinsky")
    elder: float = Field(0.0, alias="Elder")
    irov: int = Field(0, alias="irov")
    wall_ks: float = Field(0.0, alias="wall_ks")
    rhomean: float = Field(1000, alias="Rhomean")
    idensform: int = Field(2, alias="Idensform")
    ag: float = Field(9.81, alias="Ag")
    tidalforcing: bool = Field(False, alias="TidalForcing")
    doodsonstart: float = Field(55.565, alias="Doodsonstart")
    doodsonstop: float = Field(375.575, alias="Doodsonstop")
    doodsoneps: float = Field(0.0, alias="Doodsoneps")
    villemontecd1: float = Field(1.0, alias="VillemonteCD1")
    villemontecd2: float = Field(10.0, alias="VillemonteCD2")
    salinity: bool = Field(False, alias="Salinity")
    initialsalinity: float = Field(0.0, alias="InitialSalinity")
    sal0abovezlev: float = Field(-999.0, alias="Sal0abovezlev")
    deltasalinity: float = Field(-999.0, alias="DeltaSalinity")
    backgroundsalinity: float = Field(30.0, alias="Backgroundsalinity")
    temperature: int = Field(0, alias="Temperature")
    initialtemperature: float = Field(6.0, alias="InitialTemperature")
    backgroundwatertemperature: float = Field(6.0, alias="BackgroundwaterTemperature")
    secchidepth: float = Field(2.0, alias="Secchidepth")
    stanton: float = Field(0.0013, alias="Stanton")
    dalton: float = Field(0.0013, alias="Dalton")
    secondaryflow: bool = Field(False, alias="SecondaryFlow")
    betaspiral: int = Field(0, alias="BetaSpiral")


class Wind(INIBasedModel):
    _header: Literal["wind"] = "wind"
    icdtyp: int = Field(2, alias="ICdtyp")
    cdbreakpoints: List[float] = Field([0.00063, 0.00723], alias="Cdbreakpoints")
    windspeedbreakpoints: List[float] = Field(
        [0.0, 100.0], alias="Windspeedbreakpoints"
    )
    rhoair: float = Field(1.205, alias="Rhoair")
    relativewind: bool = Field(False, alias="Relativewind")
    windpartialdry: bool = Field(True, alias="Windpartialdry")
    pavbnd: float = Field(0.0, alias="PavBnd")
    pavini: float = Field(0.0, alias="PavIni")

    @classmethod
    def list_delimiter(cls) -> str:
        return " "

    _split_to_list = get_split_string_on_delimiter_validator(
        "cdbreakpoints",
        "windspeedbreakpoints",
    )


class Waves(INIBasedModel):
    _header: Literal["waves"] = "waves"
    wavemodelnr: int = Field(3, alias="Wavemodelnr")
    rouwav: str = Field("FR84", alias="Rouwav")
    gammax: float = Field(0.5, alias="Gammax")


class Time(INIBasedModel):
    _header: Literal["time"] = "time"
    refdate: int = Field(20200101, alias="RefDate")  # TODO Convert to datetime
    tzone: float = Field(0.0, alias="Tzone")
    tunit: str = Field("S", alias="Tunit")  # DHMS
    dtuser: float = Field(300.0, alias="DtUser")
    dtnodal: float = Field(21600.0, alias="DtNodal")
    dtmax: float = Field(30.0, alias="DtMax")
    dtinit: float = Field(1.0, alias="DtInit")
    tstart: float = Field(0.0, alias="TStart")
    tstop: float = Field(86400.0, alias="TStop")
    updateroughnessinterval: float = Field(86400.0, alias="UpdateRoughnessInterval")


class Restart(INIBasedModel):
    _header: Literal["restart"] = "restart"
    restartfile: Optional[Path] = Field(None, alias="RestartFile")
    restartdatetime: Optional[str] = Field(None, alias="RestartDateTime")


class Boundary(INIBasedModel):
    _header: Literal["Boundary"] = "Boundary"
    quantity: str
    nodeId: str
    forcingfile: Optional[ForcingModel] = "FlowFM_boundaryconditions1d.bc"
    bndWidth1D: float

    def is_intermediate_link(self) -> bool:
        return True


class Lateral(INIBasedModel):
    _header: Literal["Lateral"] = "Lateral"
    id: str
    name: str
    nodeId: str
    discharge: str


class ExtGeneral(INIGeneral):
    _header: Literal["General"] = "General"
    fileVersion: str = "2.01"
    fileType: Literal["extForce"] = "extForce"


class ExtModel(INIModel):
    general: ExtGeneral = ExtGeneral()
    boundary: List[Boundary] = []
    lateral: List[Lateral] = []

    _split_to_list = make_list_validator("boundary", "lateral")

    @classmethod
    def _ext(cls) -> str:
        return ".ext"

    @classmethod
    def _filename(cls) -> str:
        return "bnd"

    def _serialize(self, _: dict) -> None:
        # We skip the passed dict for a better one.
        config = SerializerConfig(section_indent=0, property_indent=0)
        write_ini(self.filepath, self._to_document(), config=config)


class ExternalForcing(INIBasedModel):
    _header: Literal["external forcing"] = "external forcing"
    extforcefile: Optional[Path] = Field(None, alias="ExtForceFile")
    extforcefilenew: Optional[ExtModel] = Field(None, alias="ExtForceFileNew")
    rainfall: Optional[bool] = Field(None, alias="Rainfall")
    qext: Optional[bool] = Field(None, alias="QExt")
    evaporation: Optional[bool] = Field(None, alias="Evaporation")
    windext: Optional[int] = Field(None, alias="WindExt")

    def is_intermediate_link(self) -> bool:
        return True


class Hydrology(INIBasedModel):
    _header: Literal["hydrology"] = "hydrology"
    interceptionmodel: bool = Field(False, alias="InterceptionModel")


class Trachytopes(INIBasedModel):
    _header: Literal["trachytopes"] = "trachytopes"
    trtrou: str = Field("N", alias="TrtRou")  # TODO bool
    trtdef: Optional[int] = Field(None, alias="TrtDef")  # no doc?
    trtl: Optional[int] = Field(None, alias="TrtL")  # no doc?
    dttrt: float = Field(60.0, alias="DtTrt")


class Output(INIBasedModel):
    _header: Literal["output"] = "output"
    wrishp_crs: bool = Field(False, alias="Wrishp_crs")
    wrishp_weir: bool = Field(False, alias="Wrishp_weir")
    wrishp_gate: bool = Field(False, alias="Wrishp_gate")
    wrishp_fxw: bool = Field(False, alias="Wrishp_fxw")
    wrishp_thd: bool = Field(False, alias="Wrishp_thd")
    wrishp_obs: bool = Field(False, alias="Wrishp_obs")
    wrishp_emb: bool = Field(False, alias="Wrishp_emb")
    wrishp_dryarea: bool = Field(False, alias="Wrishp_dryarea")
    wrishp_enc: bool = Field(False, alias="Wrishp_enc")
    wrishp_src: bool = Field(False, alias="Wrishp_src")
    wrishp_pump: bool = Field(False, alias="Wrishp_pump")
    outputdir: Optional[Path] = Field(None, alias="OutputDir")
    waqoutputdir: Optional[Path] = Field(None, alias="WAQOutputDir")
    flowgeomfile: Optional[Path] = Field(None, alias="FlowGeomFile")
    obsfile: Optional[List[Path]] = Field(None, alias="ObsFile")
    crsfile: Optional[List[Path]] = Field(None, alias="CrsFile")
    hisfile: Optional[Path] = Field(None, alias="HisFile")
    hisinterval: List[float] = Field([300], alias="HisInterval")
    xlsinterval: List[float] = Field([0.0], alias="XLSInterval")
    mapfile: Optional[Path] = Field(None, alias="MapFile")
    mapinterval: List[float] = Field([1200.0], alias="MapInterval")
    rstinterval: List[float] = Field([0.0], alias="RstInterval")
    mapformat: int = Field(4, alias="MapFormat")
    ncformat: int = Field(3, alias="NcFormat")
    ncnounlimited: bool = Field(False, alias="NcNoUnlimited")
    ncnoforcedflush: bool = Field(False, alias="NcNoForcedFlush")
    ncwritelatlon: bool = Field(False, alias="NcWriteLatLon")

    # his file
    wrihis_balance: bool = Field(True, alias="Wrihis_balance")
    wrihis_sourcesink: bool = Field(True, alias="Wrihis_sourcesink")
    wrihis_structure_gen: bool = Field(True, alias="Wrihis_structure_gen")
    wrihis_structure_dam: bool = Field(True, alias="Wrihis_structure_dam")
    wrihis_structure_pump: bool = Field(True, alias="Wrihis_structure_pump")
    wrihis_structure_gate: bool = Field(True, alias="Wrihis_structure_gate")
    wrihis_structure_weir: bool = Field(True, alias="Wrihis_structure_weir")
    wrihis_structure_orifice: bool = Field(True, alias="Wrihis_structure_orifice")
    wrihis_structure_bridge: bool = Field(True, alias="Wrihis_structure_bridge")
    wrihis_structure_culvert: bool = Field(True, alias="Wrihis_structure_culvert")
    wrihis_structure_longculvert: bool = Field(
        True, alias="Wrihis_structure_longculvert"
    )
    wrihis_structure_dambreak: bool = Field(True, alias="Wrihis_structure_damBreak")
    wrihis_structure_uniweir: bool = Field(True, alias="Wrihis_structure_uniWeir")
    wrihis_structure_compound: bool = Field(True, alias="Wrihis_structure_compound")
    wrihis_lateral: bool = Field(True, alias="Wrihis_lateral")
    wrihis_velocity: bool = Field(False, alias="Wrihis_velocity")
    wrihis_discharge: bool = Field(False, alias="Wrihis_discharge")

    # Map file
    wrimap_waterlevel_s0: bool = Field(True, alias="Wrimap_waterlevel_s0")
    wrimap_waterlevel_s1: bool = Field(True, alias="Wrimap_waterlevel_s1")
    wrimap_evaporation: bool = Field(True, alias="Wrimap_evaporation")
    wrimap_velocity_component_u0: bool = Field(
        True, alias="Wrimap_velocity_component_u0"
    )
    wrimap_velocity_component_u1: bool = Field(
        True, alias="Wrimap_velocity_component_u1"
    )
    wrimap_velocity_vector: bool = Field(True, alias="Wrimap_velocity_vector")
    wrimap_upward_velocity_component: bool = Field(
        False, alias="Wrimap_upward_velocity_component"
    )
    wrimap_density_rho: bool = Field(True, alias="Wrimap_density_rho")
    wrimap_horizontal_viscosity_viu: bool = Field(
        True, alias="Wrimap_horizontal_viscosity_viu"
    )
    wrimap_horizontal_diffusivity_diu: bool = Field(
        True, alias="Wrimap_horizontal_diffusivity_diu"
    )
    wrimap_flow_flux_q1: bool = Field(True, alias="Wrimap_flow_flux_q1")
    wrimap_spiral_flow: bool = Field(True, alias="Wrimap_spiral_flow")
    wrimap_numlimdt: bool = Field(True, alias="Wrimap_numlimdt")
    wrimap_taucurrent: bool = Field(True, alias="Wrimap_taucurrent")
    wrimap_chezy: bool = Field(True, alias="Wrimap_chezy")
    wrimap_turbulence: bool = Field(True, alias="Wrimap_turbulence")
    wrimap_rain: bool = Field(False, alias="Wrimap_rain")
    wrimap_wind: bool = Field(True, alias="Wrimap_wind")
    wrimap_heat_fluxes: bool = Field(False, alias="Wrimap_heat_fluxes")
    wrimap_wet_waterdepth_threshold: float = Field(
        2e-5, alias="Wrimap_wet_waterdepth_threshold"
    )
    wrimap_time_water_on_ground: bool = Field(
        False, alias="Wrimap_time_water_on_ground"
    )
    wrimap_freeboard: bool = Field(False, alias="Wrimap_freeboard")
    wrimap_waterdepth_on_ground: bool = Field(
        False, alias="Wrimap_waterdepth_on_ground"
    )
    wrimap_volume_on_ground: bool = Field(False, alias="Wrimap_volume_on_ground")
    wrimap_total_net_inflow_1d2d: bool = Field(
        False, alias="Wrimap_total_net_inflow_1d2d"
    )
    wrimap_total_net_inflow_lateral: bool = Field(
        False, alias="Wrimap_total_net_inflow_lateral"
    )
    wrimap_water_level_gradient: bool = Field(
        False, alias="Wrimap_water_level_gradient"
    )
    wrimap_flow_analysis: bool = Field(False, alias="Wrimap_flow_analysis")
    mapoutputtimevector: Optional[Path] = Field(None, alias="MapOutputTimeVector")
    fullgridoutput: bool = Field(False, alias="FullGridOutput")
    eulervelocities: bool = Field(False, alias="EulerVelocities")
    classmapfile: Optional[Path] = Field(None, alias="ClassMapFile")
    waterlevelclasses: List[float] = Field([0.0], alias="WaterlevelClasses")
    waterdepthclasses: List[float] = Field([0.0], alias="WaterdepthClasses")
    classmapinterval: List[float] = Field([0.0], alias="ClassMapInterval")
    waqinterval: List[float] = Field([0.0], alias="WaqInterval")
    statsinterval: List[float] = Field([0.0], alias="StatsInterval")
    writebalancefile: bool = Field(False, alias="Writebalancefile")
    timingsinterval: List[float] = Field([0.0], alias="TimingsInterval")
    richardsononoutput: bool = Field(True, alias="Richardsononoutput")

    _split_to_list = get_split_string_on_delimiter_validator(
        "waterlevelclasses",
        "waterdepthclasses",
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

    _header: Literal["geometry"] = "geometry"
    netfile: Optional[NetworkModel] = Field(
        default_factory=NetworkModel, alias="NetFile"
    )
    bathymetryfile: Optional[XYZModel] = Field(None, alias="BathymetryFile")
    drypointsfile: Optional[List[Union[XYZModel, PolyFile]]] = Field(
        None, alias="DryPointsFile"
    )  # TODO Fix, this will always try XYZ first, alias="]")
    structurefile: Optional[List[StructureModel]] = Field(None, alias="StructureFile")
    inifieldfile: Optional[Path] = Field(None, alias="IniFieldFile")
    waterlevinifile: Optional[Path] = Field(None, alias="WaterLevIniFile")
    landboundaryfile: Optional[List[Path]] = Field(None, alias="LandBoundaryFile")
    thindamfile: Optional[List[PolyFile]] = Field(None, alias="ThinDamFile")
    fixedweirfile: Optional[List[PolyFile]] = Field(None, alias="FixedWeirFile")
    pillarfile: Optional[List[PolyFile]] = Field(None, alias="PillarFile")
    usecaching: bool = Field(False, alias="UseCaching")
    vertplizfile: Optional[PolyFile] = Field(None, alias="VertplizFile")
    frictfile: Optional[List[FrictionModel]] = Field(None, alias="FrictFile")
    crossdeffile: Optional[CrossDefModel] = Field(None, alias="CrossDefFile")
    crosslocfile: Optional[CrossLocModel] = Field(None, alias="CrossLocFile")
    storagenodefile: Optional[Path] = Field(None, alias="StorageNodeFile")
    onedtwodlinkfile: Optional[Path] = Field(None, alias="oneDtwoDLinkFile")
    proflocfilefile: Optional[Path] = Field(None, alias="ProflocFileFile")
    profdeffile: Optional[Path] = Field(None, alias="ProfdefFile")
    profdefxyzfile: Optional[Path] = Field(None, alias="ProfdefxyzFile")
    manholefile: Optional[Path] = Field(None, alias="ManholeFile")
    partitionfile: Optional[PolyFile] = Field(None, alias="PartitionFile")
    uniformwidth1d: float = Field(2.0, alias="Uniformwidth1D")
    waterlevini: float = Field(0.0, alias="WaterLevIni")
    bedlevuni: float = Field(-5.0, alias="Bedlevuni")
    bedslope: float = Field(0.0, alias="Bedslope")
    bedlevtype: int = Field(3, alias="BedlevType")
    blmeanbelow: float = Field(-999.0, alias="Blmeanbelow")
    blminabove: float = Field(-999.0, alias="Blminabove")
    anglat: float = Field(0.0, alias="AngLat")
    anglon: float = Field(0.0, alias="AngLon")
    conveyance2d: int = Field(-1, alias="Conveyance2D")
    nonlin1d: int = Field(1, alias="Nonlin1D")
    nonlin2d: int = Field(0, alias="Nonlin2D")
    sillheightmin: float = Field(0.0, alias="Sillheightmin")
    makeorthocenters: bool = Field(False, alias="Makeorthocenters")
    dcenterinside: float = Field(1.0, alias="Dcenterinside")
    bamin: float = Field(1e-06, alias="Bamin")
    openboundarytolerance: float = Field(3.0, alias="OpenBoundaryTolerance")
    renumberflownodes: bool = Field(True, alias="RenumberFlowNodes")
    kmx: int = Field(0, alias="Kmx")
    layertype: int = Field(1, alias="Layertype")
    numtopsig: int = Field(0, alias="Numtopsig")
    sigmagrowthfactor: float = Field(1.0, alias="SigmaGrowthFactor")
    dxdoubleat1dendnodes: bool = Field(True, alias="dxDoubleAt1DEndNodes")
    changevelocityatstructures: bool = Field(False, alias="ChangeVelocityAtStructures")
    changestructuredimensions: bool = Field(True, alias="ChangeStructureDimensions")

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
    """FM Model representation."""

    general: General = Field(default_factory=General)
    geometry: Geometry = Field(default_factory=Geometry)
    volumetables: VolumeTables = Field(default_factory=VolumeTables)
    numerics: Numerics = Field(default_factory=Numerics)
    physics: Physics = Field(default_factory=Physics)
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
