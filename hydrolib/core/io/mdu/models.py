from hydrolib.core.io.xyz.models import XYZModel
from hydrolib.core.io.polyfile.models import PolyFile
from hydrolib.core.io.bc.models import ForcingModel
from pathlib import Path
from typing import Callable, List, Optional, Literal, Union

from hydrolib.core.basemodel import FileModel
from hydrolib.core.io.base import DummySerializer
from hydrolib.core.io.ini.models import (
    CrossDefModel,
    CrossLocModel,
    FrictionModel,
    IniBasedModel,
    INIModel,
    INIGeneral,
)
from hydrolib.core.io.ini.parser import Parser
from hydrolib.core.io.ini.util import (
    get_split_string_on_delimeter_validator,
    make_list_validator,
)
from hydrolib.core.io.structure.models import StructureModel


class General(IniBasedModel):
    Program: str = "D-Flow FM"
    Version: str = "1.2.94.66079M"
    fileType: str = "modelDef"
    fileVersion: str = "1.09"
    GuiVersion: str = "1.5.0.49132"
    AutoStart: bool = False
    PathsRelativeToParent: bool = False


class Numerics(IniBasedModel):
    CFLMax = 0.7
    AdvecType = 0
    TimeStepType = 2
    Limtyphu = 0
    Limtypmom = 4
    Limtypsa = 4
    TransportMethod = 1
    Vertadvtypsal = 5
    Icgsolver = 4
    Maxdegree = 6
    FixedWeirScheme = 6
    FixedWeirContraction = 1
    FixedWeirfrictscheme = 1
    Fixedweirtopwidth = 3
    Fixedweirtopfrictcoef = -999
    Fixedweirtalud = 4
    Izbndpos = 0
    Tlfsmo = 60
    Slopedrop2D = 0
    drop1D = 1
    Chkadvd = 0.1
    Teta0 = 0.55
    Qhrelax = 0.01
    Jbasqbnddownwindhs = 0
    cstbnd = 0
    Maxitverticalforestersal = 0
    Maxitverticalforestertem = 0
    Jaorgsethu = 1
    Turbulencemodel = 3
    Turbulenceadvection = 3
    AntiCreep = 0
    Maxwaterleveldiff = 0
    Maxvelocitydiff = 0
    Epshu = 0.0001


class Physics(IniBasedModel):
    UnifFrictCoef = 0.023
    UnifFrictType = 1
    UnifFrictCoef1D = 0.023
    UnifFrictCoefLin = 0
    Umodlin = 0
    Vicouv = 1
    Dicouv = 1
    Vicoww = 5e-05
    Dicoww = 5e-05
    Vicwminb = 0
    Smagorinsky = 0
    Elder = 0
    Irov = 0
    wall_ks = 0
    Rhomean = 1000
    Idensform = 2
    Ag = 9.81
    TidalForcing = 0
    Doodsonstart = 55.565
    Doodsonstop = 375.575
    Doodsoneps = 0
    Salinity = 0
    InitialSalinity = 0
    Sal0abovezlev = -999
    DeltaSalinity = -999
    Backgroundsalinity = 30
    InitialTemperature = 6
    Secchidepth = 2
    Stanton = -1
    Dalton = -1
    Backgroundwatertemperature = 6
    SecondaryFlow = 0
    EffectSpiral = 0
    BetaSpiral = 0
    Temperature = 0


class Wind(IniBasedModel):
    ICdtyp = 2
    Cdbreakpoints: List[float] = [0.00063, 0.00723]
    Windspeedbreakpoints: List[int] = [0, 100]
    Rhoair = 1.205
    PavBnd = 0
    PavIni = 0

    _split_to_list = get_split_string_on_delimeter_validator(
        "Cdbreakpoints", "Windspeedbreakpoints", delimiter=" "
    )


class Waves(IniBasedModel):
    Wavemodelnr = 0
    WaveNikuradse = 0.01
    Rouwav = "FR84"
    Gammax = 1


class Time(IniBasedModel):
    RefDate = 20200101
    Tzone = 0
    DtUser = 60
    DtNodal: Optional[int] = None
    DtMax = 10
    DtInit = 1
    Tunit = "S"
    TStart = 0
    TStop = 7200
    AutoTimestepNoStruct = 1


class Restart(IniBasedModel):
    RestartFile: Optional[Path] = None
    RestartDateTime: Optional[str] = None


class Boundary(IniBasedModel):
    quantity: str
    nodeId: str
    forcingfile: Optional[ForcingModel] = "FlowFM_boundaryconditions1d.bc"
    bndWidth1D: float


class Lateral(IniBasedModel):
    id: str
    name: str
    nodeId: str
    discharge: str


class ExtGeneral(INIGeneral):
    fileVersion: str = "2.01"
    fileType: Literal["extForce"] = "extForce"


class ExtModel(INIModel):
    general: ExtGeneral
    boundary: List[Boundary]
    lateral: List[Lateral]

    _split_to_list = make_list_validator("boundary", "lateral")

    @classmethod
    def _ext(cls) -> str:
        return ".ext"

    @classmethod
    def _filename(cls) -> str:
        return "bnd"


class ExternalForcing(IniBasedModel):
    ExtForceFile: Optional[Path] = None
    ExtForceFileNew: Optional[ExtModel] = "FlowFM_bnd.ext"


class Trachytopes(IniBasedModel):
    TrtRou = "N"
    TrtDef: Optional[int] = None
    TrtL: Optional[int] = None
    DtTrt = 60


class Output(IniBasedModel):
    Wrishp_crs = 0
    Wrishp_weir = 0
    Wrishp_gate = 0
    Wrishp_fxw = 0
    Wrishp_thd = 0
    Wrishp_obs = 0
    Wrishp_emb = 0
    Wrishp_dryarea = 0
    Wrishp_enc = 0
    Wrishp_src = 0
    Wrishp_pump = 0
    OutputDir: Optional[Path] = None
    FlowGeomFile: Optional[Path] = None
    ObsFile: Optional[List[Path]] = None
    CrsFile: Optional[List[Path]] = None
    HisFile: Optional[Path] = None
    HisInterval = 60
    XLSInterval: Optional[int] = None
    MapFile: Optional[Path] = None
    MapInterval = 60
    RstInterval = 86400
    S1incinterval: Optional[int] = None
    MapFormat = 4
    Wrihis_balance = 1
    Wrihis_sourcesink = 1
    Wrihis_structure_gen = 1
    Wrihis_structure_dam = 1
    Wrihis_structure_pump = 1
    Wrihis_structure_gate = 1
    Wrihis_structure_weir = 1
    Wrihis_structure_orifice = 1
    Wrihis_structure_bridge = 1
    Wrihis_structure_culvert = 1
    Wrihis_structure_damBreak = 1
    Wrihis_structure_uniWeir = 1
    Wrihis_structure_compound = 1
    Wrihis_turbulence = 0
    Wrihis_wind = 0
    Wrihis_rain = 1
    Wrihis_temperature = 0
    Wrihis_heat_fluxes = 0
    Wrihis_salinity = 0
    Wrihis_density = 0
    Wrihis_waterlevel_s1 = 1
    Wrihis_waterdepth = 0
    Wrihis_velocity_vector = 1
    Wrihis_upward_velocity_component = 0
    Wrihis_sediment = 0
    Wrihis_constituents = 0
    Wrimap_waterlevel_s0 = 0
    Wrimap_waterlevel_s1 = 1
    Wrimap_velocity_component_u0 = 0
    Wrimap_velocity_component_u1 = 1
    Wrimap_velocity_vector = 1
    Wrimap_upward_velocity_component = 0
    Wrimap_density_rho = 0
    Wrimap_horizontal_viscosity_viu = 0
    Wrimap_horizontal_diffusivity_diu = 0
    Wrimap_flow_flux_q1 = 1
    Wrimap_spiral_flow = 0
    Wrimap_numlimdt = 1
    Wrimap_taucurrent = 0
    Wrimap_chezy = 0
    Wrimap_turbulence = 0
    Wrimap_wind = 0
    Wrimap_heat_fluxes = 0
    Wrimap_freeboard = 1
    Wrimap_wet_waterdepth_threshold = 0
    Wrimap_time_water_on_ground = 1
    Wrimap_waterdepth_on_ground = 1
    Wrimap_volume_on_ground = 1
    Wrimap_total_net_inflow_1d2d = 1
    Wrimap_total_net_inflow_lateral = 1
    MapOutputTimeVector: Optional[int] = None
    FullGridOutput = 0
    EulerVelocities = 0
    WaqInterval = 0
    ClassMapFile: Optional[Path] = None
    WaterlevelClasses = 0
    WaterdepthClasses = 0
    VelocityMagnitudeClasses = 0
    VelocityDirectionClassesInterval = 30
    ClassMapInterval = 300
    StatsInterval: Optional[int] = None
    Writebalancefile = 0
    TimingsInterval: Optional[int] = None
    Richardsononoutput = 1


class Geometry(IniBasedModel):

    NetFile: Optional[Path]
    BathymetryFile: Optional[XYZModel] = None
    DryPointsFile: Optional[
        List[Union[XYZModel, PolyFile]]
    ] = None  # TODO This will always try XYZ first
    GridEnclosureFile: Optional[List[Path]] = None
    WaterLevIniFile: Optional[Path] = None
    LandBoundaryFile: Optional[List[Path]] = None
    ThinDamFile: Optional[List[PolyFile]] = None
    FixedWeirFile: Optional[List[PolyFile]] = None
    PillarFile: Optional[List[PolyFile]] = None
    UseCaching: bool = False
    StructureFile: Optional[List[StructureModel]]
    VertplizFile: Optional[PolyFile] = None
    CrossDefFile: Optional[CrossDefModel] = None
    CrossLocFile: Optional[CrossLocModel] = None
    FrictFile: Optional[List[FrictionModel]]
    StorageNodeFile: Optional[Path]
    BranchFile: Optional[Path]
    RoofsFile: Optional[Path] = None
    ProfdefxyzFile: Optional[Path] = None
    IniFieldFile: Optional[Path] = None
    Uniformwidth1D = 0.1
    ManholeFile: Optional[Path] = None
    WaterLevIni = -5
    Bedlevuni = -5
    Bedslope = 0
    BedlevType = 1
    Blmeanbelow = -999
    Blminabove = -999
    PartitionFile: Optional[Path] = None
    AngLat = 0
    AngLon = 0
    Conveyance2D = -1
    Nonlin2D = 0
    Nonlin1D = 0
    Slotw2D = 0
    Slotw1D = 0.001
    Dxmin1D = 1
    Sillheightmin = 0
    Makeorthocenters = 0
    Dcenterinside = 1
    Bamin = 1e-06
    OpenBoundaryTolerance = 3
    RenumberFlowNodes = 1
    Kmx = 0
    Layertype = 1
    Numtopsig = 0
    SigmaGrowthFactor = 1
    AllowBndAtBifurcation = 0
    dxDoubleAt1DEndNodes = 0

    _split_to_list = get_split_string_on_delimeter_validator(
        "FrictFile",
        "StructureFile",
        "DryPointsFile",
        "GridEnclosureFile",
        "LandBoundaryFile",
        "ThinDamFile",
        "FixedWeirFile",
        "PillarFile",
        "StructureFile",
        "FrictFile",
        delimiter=";",
    )


class FMModel(FileModel):
    """FM Model representation."""

    # name: str = "Dummy"
    # network: Optional[Network] = Network()
    general: General
    geometry: Geometry
    numerics: Numerics
    physics: Physics
    wind: Wind
    waves: Waves
    time: Time
    restart: Restart
    external_forcing: ExternalForcing
    trachytopes: Trachytopes
    output: Output

    @classmethod
    def _ext(cls) -> str:
        return ".mdu"

    @classmethod
    def _filename(cls) -> str:
        return "fm"

    @classmethod
    def _get_serializer(cls) -> Callable:
        return DummySerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return Parser.parse
