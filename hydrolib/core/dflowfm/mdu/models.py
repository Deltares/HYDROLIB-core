from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic.v1 import Field, validator

from hydrolib.core.base.file_manager import ResolveRelativeMode
from hydrolib.core.base.models import (
    DiskOnlyFileModel,
    FileModel,
    validator_set_default_disk_only_file_model_when_none,
)
from hydrolib.core.dflowfm.crosssection.models import CrossDefModel, CrossLocModel
from hydrolib.core.dflowfm.ext.models import ExtModel
from hydrolib.core.dflowfm.extold.models import ExtOldModel
from hydrolib.core.dflowfm.friction.models import FrictionModel
from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.serializer import INISerializerConfig
from hydrolib.core.dflowfm.ini.util import (
    get_split_string_on_delimiter_validator,
    validate_datetime_string,
)
from hydrolib.core.dflowfm.inifield.models import IniFieldModel
from hydrolib.core.dflowfm.net.models import NetworkModel
from hydrolib.core.dflowfm.obs.models import ObservationPointModel
from hydrolib.core.dflowfm.obscrosssection.models import ObservationCrossSectionModel
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.storagenode.models import StorageNodeModel
from hydrolib.core.dflowfm.structure.models import StructureModel
from hydrolib.core.dflowfm.xyn.models import XYNModel
from hydrolib.core.dflowfm.xyz.models import XYZModel


class AutoStartOption(IntEnum):
    """
    Enum class containing the valid values for the AutoStart
    attribute in the [General][hydrolib.core.dflowfm.mdu.models.General] class.
    """

    no = 0
    autostart = 1
    autostartstop = 2


class General(INIGeneral):
    """The MDU file's `[General]` section with file meta data."""

    class Comments(INIBasedModel.Comments):
        program: Optional[str] = Field("Program.", alias="program")
        version: Optional[str] = Field(
            "Version number of computational kernel", alias="version"
        )
        filetype: Optional[str] = Field("File type. Do not edit this", alias="fileType")
        fileversion: Optional[str] = Field(
            "File version. Do not edit this.", alias="fileVersion"
        )
        autostart: Optional[str] = Field(
            "Autostart simulation after loading MDU or not (0=no, 1=autostart, 2=autostartstop).",
            alias="autoStart",
        )
        pathsrelativetoparent: Optional[str] = Field(
            "Whether or not (1/0) to resolve file names (e.g. inside the *.ext file) relative to their direct parent, instead of to the toplevel MDU working dir",
            alias="pathsRelativeToParent",
        )
        guiversion: Optional[str] = Field(
            "DeltaShell FM suite version.", alias="guiVersion"
        )

    comments: Comments = Comments()
    _header: Literal["General"] = "General"
    program: str = Field("D-Flow FM", alias="program")
    version: str = Field("1.2.94.66079M", alias="version")
    filetype: Literal["modelDef"] = Field("modelDef", alias="fileType")
    fileversion: str = Field("1.09", alias="fileVersion")
    autostart: Optional[AutoStartOption] = Field(AutoStartOption.no, alias="autoStart")
    pathsrelativetoparent: bool = Field(False, alias="pathsRelativeToParent")
    guiversion: Optional[str] = Field(None, alias="guiVersion")


class Numerics(INIBasedModel):
    """
    The `[Numerics]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.numerics`.

    All lowercased attributes match with the [Numerics] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        cflmax: Optional[str] = Field("Maximum Courant nr.", alias="CFLMax")
        epsmaxlev: Optional[str] = Field(
            "Stop criterium for non linear iteration", alias="EpsMaxlev"
        )
        epsmaxlevm: Optional[str] = Field(
            "Stop criterium for Nested Newton loop in non linear iteration",
            alias="EpsMaxlevM",
        )
        advectype: Optional[str] = Field(
            "Adv type, 0=no, 33=Perot q(uio-u) fast, 3=Perot q(uio-u).",
            alias="advecType",
        )
        timesteptype: Optional[str] = Field(
            "0=only transport, 1=transport + velocity update, 2=full implicit step_reduce, 3=step_jacobi, 4=explicit.",
            alias="timeStepType",
        )
        limtyphu: Optional[str] = Field(
            "Limiter type for waterdepth in continuity eq., 0=no, 1=minmod,2=vanLeer,3=Koren,4=Monotone Central.",
            alias="limTypHu",
        )
        limtypmom: Optional[str] = Field(
            "Limiter type for cell center advection velocity, 0=no, 1=minmod,2=vanLeer,4=Monotone Central.",
            alias="limTypMom",
        )
        limtypsa: Optional[str] = Field(
            "Limiter type for salinity transport,           0=no, 1=minmod,2=vanLeer,4=Monotone Central.",
            alias="limTypSa",
        )
        icgsolver: Optional[str] = Field(
            "Solver type, 4 = sobekGS + Saad-ILUD (default sequential), 6 = PETSc (default parallel), 7= CG+MILU (parallel).",
            alias="icgSolver",
        )
        maxdegree: Optional[str] = Field(
            "Maximum degree in Gauss elimination.", alias="maxDegree"
        )
        fixedweirscheme: Optional[str] = Field(
            "6 = semi-subgrid scheme, 8 = Tabellenboek, 9 = Villemonte (default).",
            alias="fixedWeirScheme",
        )
        fixedweircontraction: Optional[str] = Field(
            "flow width = flow width*fixedWeirContraction.",
            alias="fixedWeirContraction",
        )
        izbndpos: Optional[str] = Field(
            "Position of z boundary, 0=mirroring of closest cell (as in Delft3D-FLOW), 1=on net boundary.",
            alias="izBndPos",
        )
        tlfsmo: Optional[str] = Field(
            "Fourier smoothing time on water level boundaries [s].", alias="tlfSmo"
        )
        keepstbndonoutflow: Optional[str] = Field(
            "Keep salinity and temperature signals on boundary also at outflow, 1=yes, 0=no. Default=0: copy inside value on outflow.",
            alias="keepSTBndOnOutflow",
        )
        slopedrop2d: Optional[str] = Field(
            "Apply droplosses only if local bottom slope > Slopedrop2D, <=0 =no droplosses.",
            alias="slopeDrop2D",
        )
        drop1d: Optional[str] = Field(
            "Limit the downstream water level in the momentum equation to the downstream invert level, BOBdown (ζ*down = max(BOBdown, ζdown)).",
            alias="drop1D",
        )
        chkadvd: Optional[str] = Field(
            "Check advection terms if depth < chkadvdp.", alias="chkAdvd"
        )
        teta0: Optional[str] = Field(
            "Theta (implicitness) of time integration, 0.5 < Theta < 1.0.",
            alias="teta0",
        )
        qhrelax: Optional[str] = Field(None, alias="qhRelax")
        cstbnd: Optional[str] = Field(
            "Delft3D-FLOW type velocity treatment near boundaries for small coastal models (1) or not (0).",
            alias="cstBnd",
        )
        maxitverticalforestersal: Optional[str] = Field(
            "Forester iterations for salinity (0: no vertical filter for salinity, > 0: max nr of iterations).",
            alias="maxitVerticalForesterSal",
        )
        maxitverticalforestertem: Optional[str] = Field(
            "Forester iterations for temperature (0: no vertical filter for temperature, > 0: max nr of iterations).",
            alias="maxitVerticalForesterTem",
        )
        turbulencemodel: Optional[str] = Field(
            "0=no, 1 = constant, 2 = algebraic, 3 = k-epsilon, 4 = k-tau.",
            alias="turbulenceModel",
        )
        turbulenceadvection: Optional[str] = Field(
            "Turbulence advection (0=no, 3 = horizontal explicit vertical implicit).",
            alias="turbulenceAdvection",
        )
        anticreep: Optional[str] = Field(
            "Include anti-creep calculation (0: no, 1: yes).", alias="antiCreep"
        )
        baroczlaybed: Optional[str] = Field(
            "Use fix in baroclinic pressure for zlaybed (1: yes, 0: no)",
            alias="barocZLayBed",
        )
        barocponbnd: Optional[str] = Field(
            "Use baroclinic pressure correction on open boundaries (1: yes, 0: no)",
            alias="barocPOnBnd",
        )
        maxwaterleveldiff: Optional[str] = Field(
            "Upper bound [m] on water level changes, (<= 0: no bounds). Run will abort when violated.",
            alias="maxWaterLevelDiff",
        )
        maxvelocitydiff: Optional[str] = Field(
            "Upper bound [m/s] on velocity changes, (<= 0: no bounds). Run will abort when violated.",
            alias="maxVelocityDiff",
        )
        mintimestepbreak: Optional[str] = Field(
            "Smallest allowed timestep (in s), checked on a sliding average of several timesteps. Run will abort when violated.",
            alias="minTimestepBreak",
        )
        epshu: Optional[str] = Field(
            "Threshold water depth for wetting and drying [m].", alias="epsHu"
        )
        fixedweirrelaxationcoef: Optional[str] = Field(
            "Fixed weir relaxation coefficient for computation of energy loss.",
            alias="fixedWeirRelaxationCoef",
        )
        implicitdiffusion2d: Optional[str] = Field(
            "Implicit diffusion in 2D (0: no, 1:yes).", alias="implicitDiffusion2D"
        )
        vertadvtyptem: Optional[str] = Field(
            "Vertical advection type for temperature (0: none, 4: Theta implicit, 6: higher order explicit, no Forester filter).",
            alias="vertAdvTypTem",
        )
        velmagnwarn: Optional[str] = Field(
            "Warning level unitbrackets{m/s} on velocity magnitude (<= 0: no check).",
            alias="velMagnWarn",
        )
        transportautotimestepdiff: Optional[str] = Field(
            "Auto Timestepdiff in Transport, (0 : lim diff, no lim Dt, 1: no lim diff, lim Dt, 2: no lim diff, no lim Dt, 3: implicit (only 2D)).",
            alias="transportAutoTimestepDiff",
        )
        sethorizontalbobsfor1d2d: Optional[str] = Field(
            "Bobs are set to 2D bedlevel, to prevent incorrect storage in sewer system (0: no, 1:yes).",
            alias="setHorizontalBobsFor1D2D",
        )
        diagnostictransport: Optional[str] = Field(
            "No update of transport quantities, also known as diagnostic transport (0: no, 1: yes).",
            alias="diagnosticTransport",
        )
        vertadvtypsal: Optional[str] = Field(
            "Vertical advection type for salinity (0: none, 4: Theta implicit, 6: higher order explicit, no Forester filter).",
            alias="vertAdvTypSal",
        )
        zerozbndinflowadvection: Optional[str] = Field(
            "Switch for advection at open boundary (0: Neumann, 1=zero at inflow, 2=zero at inflow and outflow).",
            alias="zeroZBndInflowAdvection",
        )
        pure1d: Optional[str] = Field(
            "Purely 1D advection (0: original advection using velocity vector, 1: pure 1D using flow volume vol1_f, 2: pure 1D using volume vol1)",
            alias="pure1D",
        )
        testdryingflooding: Optional[str] = Field(
            "Drying flooding algorithm (0: D-Flow FM, 1: Delft3DFLOW, 2: Similar to 0, and volume limitation in the transport solver based on Epshu).",
            alias="testDryingFlooding",
        )
        logsolverconvergence: Optional[str] = Field(
            "Print time step, number of solver iterations and solver residual to diagnostic output (0: no, 1: yes).",
            alias="logSolverConvergence",
        )
        fixedweirscheme1d2d: Optional[str] = Field(
            "Fixed weir scheme for 1d2d links (0: same as fixedweirscheme, 1: lateral iterative fixed weir scheme).",
            alias="fixedWeirScheme1D2D",
        )
        horizontalmomentumfilter: Optional[str] = Field(
            "Filter for reduction of checkerboarding; 0=No, 1=yes.",
            alias="horizontalMomentumFilter",
        )
        maxnonlineariterations: Optional[str] = Field(
            "Maximal iterations in non-linear iteration loop before a time step reduction is applied",
            alias="maxNonLinearIterations",
        )
        maxvelocity: Optional[str] = Field(
            "Upper bound [m/s] on velocity (<= 0: no bounds). Run will abort when violated.",
            alias="maxVelocity",
        )
        waterlevelwarn: Optional[str] = Field(
            "Warning level [m AD] on water level (<= 0: no check).",
            alias="waterLevelWarn",
        )
        tspinupturblogprof: Optional[str] = Field(
            "Spin up time [s] when starting with a parabolic viscosity profile in whole model domain.",
            alias="tSpinUpTurbLogProf",
        )
        fixedweirtopfrictcoef: Optional[Optional[str]] = Field(
            "Uniform friction coefficient of the groyne part of fixed weirs [the unit depends on frictiontype].",
            alias="fixedWeirTopFrictCoef",
        )
        fixedweir1d2d_dx: Optional[str] = Field(
            "Extra delta x for lateral 1d2d fixed weirs.", alias="fixedWeir1D2D_dx"
        )
        junction1d: Optional[str] = Field(
            "Advection at 1D junctions: (0: original 1D advection using velocity vector, 1 = same as along 1D channels using Pure1D=1).",
            alias="junction1D",
        )
        fixedweirtopwidth: Optional[str] = Field(
            "Uniform width of the groyne part of fixed weirs [m].",
            alias="fixedWeirTopWidth",
        )
        vertadvtypmom: Optional[str] = Field(
            "Vertical advection type in momentum equation; 3: Upwind implicit, 6: centerbased upwind explicit.",
            alias="vertAdvTypMom",
        )
        checkerboardmonitor: Optional[str] = Field(
            "Flag for checkerboarding output on history file (only for sigma layers yet); 0=No, 1=yes.",
            alias="checkerboardMonitor",
        )
        velocitywarn: Optional[str] = Field(
            "Warning level [m/s] on normal velocity(<= 0: no check).",
            alias="velocityWarn",
        )
        adveccorrection1d2d: Optional[str] = Field(
            "Advection correction of 1D2D link volume (0: regular advection, 1: link volume au*dx, 2: advection on 1D2D switched off.)",
            alias="advecCorrection1D2D",
        )
        fixedweirtalud: Optional[str] = Field(
            "Uniform talud slope of fixed weirs.", alias="fixedWeirTalud"
        )
        lateral_fixedweir_umin: Optional[str] = Field(
            "Minimal velocity threshold for weir losses in iterative lateral 1d2d weir coupling.",
            alias="lateral_fixedweir_umin",
        )
        jasfer3d: Optional[str] = Field(
            "Corrections for spherical coordinates (0: no, 1: yes).",
            alias="jasfer3D",
        )

    comments: Comments = Comments()

    _header: Literal["Numerics"] = "Numerics"
    cflmax: float = Field(0.7, alias="CFLMax")
    epsmaxlev: float = Field(1e-8, alias="EpsMaxlev")
    epsmaxlevm: float = Field(1e-8, alias="EpsMaxlevM")
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
    keepstbndonoutflow: bool = Field(False, alias="keepSTBndOnOutflow")
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
    baroczlaybed: bool = Field(False, alias="barocZLayBed")
    barocponbnd: bool = Field(False, alias="barocPOnBnd")
    maxwaterleveldiff: float = Field(0.0, alias="maxWaterLevelDiff")
    maxvelocitydiff: float = Field(0.0, alias="maxVelocityDiff")
    mintimestepbreak: float = Field(0.0, alias="minTimestepBreak")
    epshu: float = Field(0.0001, alias="epsHu")
    fixedweirrelaxationcoef: float = Field(0.6, alias="fixedWeirRelaxationCoef")
    implicitdiffusion2d: bool = Field(False, alias="implicitDiffusion2D")
    vertadvtyptem: int = Field(6, alias="vertAdvTypTem")
    velmagnwarn: float = Field(0.0, alias="velMagnWarn")
    transportautotimestepdiff: int = Field(0, alias="transportAutoTimestepDiff")
    sethorizontalbobsfor1d2d: bool = Field(False, alias="setHorizontalBobsFor1D2D")
    diagnostictransport: bool = Field(False, alias="diagnosticTransport")
    vertadvtypsal: int = Field(6, alias="vertAdvTypSal")
    zerozbndinflowadvection: int = Field(0, alias="zeroZBndInflowAdvection")
    pure1d: int = Field(0, alias="pure1D")
    testdryingflooding: int = Field(0, alias="testDryingFlooding")
    logsolverconvergence: bool = Field(False, alias="logSolverConvergence")
    fixedweirscheme1d2d: int = Field(0, alias="fixedWeirScheme1D2D")
    horizontalmomentumfilter: bool = Field(False, alias="horizontalMomentumFilter")
    maxnonlineariterations: int = Field(100, alias="maxNonLinearIterations")
    maxvelocity: float = Field(0.0, alias="maxVelocity")
    waterlevelwarn: float = Field(0.0, alias="waterLevelWarn")
    tspinupturblogprof: float = Field(0.0, alias="tSpinUpTurbLogProf")
    fixedweirtopfrictcoef: Optional[float] = Field(-999, alias="fixedWeirTopFrictCoef")
    fixedweir1d2d_dx: float = Field(50.0, alias="fixedWeir1D2D_dx")
    junction1d: int = Field(0, alias="junction1D")
    fixedweirtopwidth: float = Field(3.0, alias="fixedWeirTopWidth")
    vertadvtypmom: int = Field(6, alias="vertAdvTypMom")
    checkerboardmonitor: bool = Field(False, alias="checkerboardMonitor")
    velocitywarn: float = Field(0.0, alias="velocityWarn")
    adveccorrection1d2d: int = Field(0, alias="advecCorrection1D2D")
    fixedweirtalud: float = Field(4.0, alias="fixedWeirTalud")
    lateral_fixedweir_umin: float = Field(0.0, alias="lateral_fixedweir_umin")
    jasfer3d: bool = Field(False, alias="jasfer3D")


class VolumeTables(INIBasedModel):
    """
    The `[VolumeTables]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.volumetables`.

    All lowercased attributes match with the [VolumeTables] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        usevolumetables: Optional[str] = Field(
            "Use 1D volume tables (0: no, 1: yes).",
            alias="useVolumeTables",
        )
        increment: Optional[str] = Field(
            "The height increment for the volume tables [m].", alias="increment"
        )
        usevolumetablefile: Optional[str] = Field(
            "Read and write the volume table from/to file (1: yes, 0= no).",
            alias="useVolumeTableFile",
        )

    comments: Comments = Comments()

    _header: Literal["VolumeTables"] = "VolumeTables"
    usevolumetables: bool = Field(False, alias="useVolumeTables")
    increment: float = Field(0.2, alias="increment")
    usevolumetablefile: bool = Field(False, alias="useVolumeTableFile")


class Physics(INIBasedModel):
    """
    The `[Physics]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.physics`.

    All lowercased attributes match with the [Physics] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        uniffrictcoef: Optional[str] = Field(
            "Uniform friction coefficient (0: no friction).", alias="unifFrictCoef"
        )
        uniffricttype: Optional[str] = Field(
            "Uniform friction type (0: Chezy, 1: Manning, 2: White-Colebrook, 3: idem, WAQUA style).",
            alias="unifFrictType",
        )
        uniffrictcoef1d: Optional[str] = Field(
            "Uniform friction coefficient in 1D links (0: no friction).",
            alias="unifFrictCoef1D",
        )
        uniffrictcoeflin: Optional[str] = Field(
            "Uniform linear friction coefficient (0: no friction).",
            alias="unifFrictCoefLin",
        )
        vicouv: Optional[str] = Field(
            "Uniform horizontal eddy viscosity [m2/s].", alias="vicouv"
        )
        dicouv: Optional[str] = Field(
            "Uniform horizontal eddy diffusivity [m2/s].", alias="dicouv"
        )
        vicoww: Optional[str] = Field(
            "Background vertical eddy viscosity [m2/s].", alias="vicoww"
        )
        dicoww: Optional[str] = Field(
            "Background vertical eddy diffusivity [m2/s].", alias="dicoww"
        )
        vicwminb: Optional[str] = Field(
            "Minimum viscosity in production and buoyancy term [m2/s].",
            alias="vicwminb",
        )
        xlozmidov: Optional[str] = Field(
            "Ozmidov length scale [m], default=0.0, no contribution of internal waves to vertical diffusion.",
            alias="xlozmidov",
        )
        smagorinsky: Optional[str] = Field(
            "Add Smagorinsky horizontal turbulence: vicu = vicu + ( (Smagorinsky*dx)**2)*S.",
            alias="smagorinsky",
        )
        elder: Optional[str] = Field(
            "Add Elder contribution: vicu = vicu + Elder*kappa*ustar*H/6); e.g. 1.0.",
            alias="elder",
        )
        irov: Optional[str] = Field(
            "Wall friction, 0=free slip, 1 = partial slip using wall_ks.", alias="irov"
        )
        wall_ks: Optional[str] = Field(
            "Nikuradse roughness [m] for side walls, wall_z0=wall_ks/30.",
            alias="wall_ks",
        )
        rhomean: Optional[str] = Field(
            "Average water density [kg/m3].", alias="rhomean"
        )
        idensform: Optional[str] = Field(
            "Density calulation (0: uniform, 1: Eckart, 2: Unesco, 3=Unesco83, 13=3+pressure).",
            alias="idensform",
        )
        ag: Optional[str] = Field("Gravitational acceleration [m/s2].", alias="ag")
        tidalforcing: Optional[str] = Field(
            "Tidal forcing, if jsferic=1 (0: no, 1: yes).", alias="tidalForcing"
        )
        itcap: Optional[str] = Field(
            "Upper limit on internal tides dissipation (W/m^2)", alias="ITcap"
        )
        doodsonstart: Optional[str] = Field(
            "Doodson start time for tidal forcing [s].", alias="doodsonStart"
        )
        doodsonstop: Optional[str] = Field(
            "Doodson stop time for tidal forcing [s].", alias="doodsonStop"
        )
        doodsoneps: Optional[str] = Field(
            "Doodson tolerance level for tidal forcing [s].", alias="doodsonEps"
        )
        villemontecd1: Optional[str] = Field(
            "Calibration coefficient for Villemonte. Default = 1.0.",
            alias="villemonteCD1",
        )
        villemontecd2: Optional[str] = Field(
            "Calibration coefficient for Villemonte. Default = 10.0.",
            alias="villemonteCD2",
        )
        salinity: Optional[str] = Field(
            "Include salinity, (0: no, 1: yes).", alias="salinity"
        )
        initialsalinity: Optional[str] = Field(
            "Initial salinity concentration [ppt].", alias="initialSalinity"
        )
        sal0abovezlev: Optional[str] = Field(
            "Salinity 0 above level [m].", alias="sal0AboveZLev"
        )
        deltasalinity: Optional[str] = Field(
            "uniform initial salinity [ppt].", alias="deltaSalinity"
        )
        backgroundsalinity: Optional[str] = Field(
            "Background salinity for eqn. of state if salinity not computed [psu].",
            alias="backgroundSalinity",
        )
        temperature: Optional[str] = Field(
            "Include temperature (0: no, 1: only transport, 3: excess model of D3D, 5: composite (ocean) model).",
            alias="temperature",
        )
        initialtemperature: Optional[str] = Field(
            "Initial temperature [◦C].", alias="initialTemperature"
        )
        backgroundwatertemperature: Optional[str] = Field(
            "Background water temperature for eqn. of state if temperature not computed [◦C].",
            alias="backgroundWaterTemperature",
        )
        secchidepth: Optional[str] = Field(
            "Water clarity parameter [m].", alias="secchiDepth"
        )
        stanton: Optional[str] = Field(
            "Coefficient for convective heat flux ( ), if negative, then Cd wind is used.",
            alias="stanton",
        )
        dalton: Optional[str] = Field(
            "Coefficient for evaporative heat flux ( ), if negative, then Cd wind is used.",
            alias="dalton",
        )
        tempmax: Optional[str] = Field(
            "Limit the temperature to max value [°C]", alias="tempMax"
        )
        tempmin: Optional[str] = Field(
            "Limit the temperature to min value [°C]", alias="tempMin"
        )
        salimax: Optional[str] = Field(
            "Limit for salinity to max value [ppt]", alias="saliMax"
        )
        salimin: Optional[str] = Field(
            "Limit for salinity to min value [ppt]", alias="saliMin"
        )
        heat_eachstep: Optional[str] = Field(
            "'1=heat each timestep, 0=heat each usertimestep", alias="heat_eachStep"
        )
        rhoairrhowater: Optional[str] = Field(
            "'windstress rhoa/rhow: 0=Rhoair/Rhomean, 1=Rhoair/rhow(), 2=rhoa0()/rhow(), 3=rhoa10()/Rhow()",
            alias="rhoAirRhoWater",
        )
        nudgetimeuni: Optional[str] = Field(
            "Uniform nudge relaxation time [s]", alias="nudgeTimeUni"
        )
        iniwithnudge: Optional[str] = Field(
            "Initialize salinity and temperature with nudge variables (0: no, 1: yes, 2: only initialize, no nudging)",
            alias="iniWithNudge",
        )
        secondaryflow: Optional[str] = Field(
            "Secondary flow (0: no, 1: yes).", alias="secondaryFlow"
        )
        betaspiral: Optional[str] = Field(
            "Weight factor of the spiral flow intensity on flow dispersion stresses (0d0 = disabled).",
            alias="betaSpiral",
        )

    comments: Comments = Comments()

    _header: Literal["Physics"] = "Physics"
    uniffrictcoef: float = Field(0.023, alias="unifFrictCoef")
    uniffricttype: int = Field(1, alias="unifFrictType")
    uniffrictcoef1d: float = Field(0.023, alias="unifFrictCoef1D")
    uniffrictcoeflin: float = Field(0.0, alias="unifFrictCoefLin")
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
    itcap: Optional[float] = Field(0.0, alias="ITcap")
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
    tempmax: float = Field(-999.0, alias="tempMax")
    tempmin: float = Field(0.0, alias="tempMin")
    salimax: float = Field(-999.0, alias="saliMax")
    salimin: float = Field(0.0, alias="saliMin")
    heat_eachstep: bool = Field(False, alias="heat_eachStep")
    rhoairrhowater: int = Field(0, alias="rhoAirRhoWater")
    nudgetimeuni: float = Field(3600.0, alias="nudgeTimeUni")
    iniwithnudge: int = Field(0, alias="iniWithNudge")
    secondaryflow: bool = Field(False, alias="secondaryFlow")
    betaspiral: float = Field(0.0, alias="betaSpiral")


class Sediment(INIBasedModel):
    class Comments(INIBasedModel.Comments):
        sedimentmodelnr: Optional[str] = Field(
            "Sediment model nr, (0=no, 1=Krone, 2=SvR2007, 3=E-H, 4=MorphologyModule).",
            alias="Sedimentmodelnr",
        )
        morfile: Optional[str] = Field(
            "Morphology settings file (*.mor)", alias="MorFile"
        )
        sedfile: Optional[str] = Field(
            "Sediment characteristics file (*.sed)", alias="SedFile"
        )

    comments: Comments = Comments()

    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    _header: Literal["Sediment"] = "Sediment"
    sedimentmodelnr: Optional[int] = Field(0, alias="Sedimentmodelnr")
    morfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="MorFile"
    )
    sedfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="SedFile"
    )


class Wind(INIBasedModel):
    """
    The `[Wind]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.wind`.

    All lowercased attributes match with the [Wind] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        icdtyp: Optional[str] = Field(
            "Wind drag coefficient type (1: Const, 2: Smith&Banke (2 pts), 3: S&B (3 pts), 4: Charnock 1955, 5: Hwang 2005, 6: Wuest 2005, 7: Hersbach 2010 (2 pts), 8: 4+viscous).",
            alias="iCdTyp",
        )
        cdbreakpoints: Optional[str] = Field(
            "Wind drag breakpoints, e.g. 0.00063 0.00723.", alias="CdBreakpoints"
        )
        windspeedbreakpoints: Optional[str] = Field(
            "Wind speed breakpoints [m/s], e.g. 0.0 100.0.",
            alias="windSpeedBreakpoints",
        )
        rhoair: Optional[str] = Field("Air density [kg/m3].", alias="rhoAir")
        relativewind: Optional[str] = Field(
            "Wind speed [kg/m3] relative to top-layer water speed*relativewind (0d0=no relative wind, 1d0=using full top layer speed).",
            alias="relativeWind",
        )
        windpartialdry: Optional[str] = Field(
            "Reduce windstress on water if link partially dry, only for bedlevtyp=3, 0=no, 1=yes (default).",
            alias="windPartialDry",
        )
        pavbnd: Optional[str] = Field(
            "Average air pressure on open boundaries [N/m2], only applied if value > 0.",
            alias="pavBnd",
        )
        pavini: Optional[str] = Field(
            "Initial air pressure [N/m2], only applied if value > 0.", alias="pavIni"
        )
        computedairdensity: Optional[str] = Field(
            "Compute air density yes/no (), 1/0, default 0.", alias="computedAirdensity"
        )
        stresstowind: Optional[str] = Field(
            "Switch between Wind speed (=0) and wind stress (=1) approach for wind forcing.",
            alias="stressToWind",
        )

    comments: Comments = Comments()

    _header: Literal["Wind"] = "Wind"
    icdtyp: int = Field(2, alias="iCdTyp")
    cdbreakpoints: List[float] = Field([0.00063, 0.00723], alias="CdBreakpoints")
    windspeedbreakpoints: List[float] = Field(
        [0.0, 100.0], alias="windSpeedBreakpoints"
    )
    rhoair: float = Field(1.2, alias="rhoAir")
    relativewind: float = Field(0.0, alias="relativeWind")
    windpartialdry: bool = Field(True, alias="windPartialDry")
    pavbnd: float = Field(0.0, alias="pavBnd")
    pavini: float = Field(0.0, alias="pavIni")
    computedairdensity: bool = Field(False, alias="computedAirdensity")
    stresstowind: bool = Field(False, alias="stressToWind")

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

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.waves`.

    All lowercased attributes match with the [Waves] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        wavemodelnr: Optional[str] = Field(
            "Wave model nr. (0: none, 1: fetch/depth limited hurdlestive, 2: Young-Verhagen, 3: SWAN, 5: uniform, 6: SWAN-NetCDF",
            alias="waveModelNr",
        )
        rouwav: Optional[str] = Field(
            "Friction model for wave induced shear stress: FR84 (default) or: MS90, HT91, GM79, DS88, BK67, CJ85, OY88, VR04.",
            alias="rouWav",
        )
        gammax: Optional[str] = Field(
            "Maximum wave height/water depth ratio", alias="gammaX"
        )

    comments: Comments = Comments()

    _header: Literal["Waves"] = "Waves"
    wavemodelnr: int = Field(3, alias="waveModelNr")
    rouwav: str = Field("FR84", alias="rouWav")
    gammax: float = Field(0.5, alias="gammaX")


class Time(INIBasedModel):
    """
    The `[Time]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.time`.

    All lowercased attributes match with the [Time] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        refdate: Optional[str] = Field("Reference date [yyyymmdd].", alias="refDate")
        tzone: Optional[str] = Field(
            "Data Sources in GMT are interrogated with time in minutes since refdat-Tzone*60 [min].",
            alias="tZone",
        )
        tunit: Optional[str] = Field("Time units in MDU [D, H, M or S].", alias="tUnit")
        dtuser: Optional[str] = Field(
            "User timestep in seconds [s] (interval for external forcing update & his/map output).",
            alias="dtUser",
        )
        dtnodal: Optional[str] = Field(
            "Time interval [s] for updating nodal factors in astronomical boundary conditions.",
            alias="dtNodal",
        )
        dtmax: Optional[str] = Field("Max timestep in seconds [s].", alias="dtMax")
        dtinit: Optional[str] = Field(
            "Initial timestep in seconds [s].", alias="dtInit"
        )
        autotimestep: Optional[str] = Field(
            "0 = no, 1 = 2D (hor. out), 3=3D (hor. out), 5 = 3D (hor. inout + ver. inout), smallest dt",
            alias="autoTimestep",
        )
        autotimestepnostruct: Optional[str] = Field(
            "Exclude structure links (and neighbours) from time step limitation (0 = no, 1 = yes).",
            alias="autoTimestepNoStruct",
        )
        autotimestepnoqout: Optional[str] = Field(
            "Exclude negative qin terms from time step limitation (0 = no, 1 = yes).",
            alias="autoTimestepNoQout",
        )
        tstart: Optional[str] = Field(
            "Start time w.r.t. RefDate [TUnit].", alias="tStart"
        )
        tstop: Optional[str] = Field("Stop time w.r.t. RefDate [TUnit].", alias="tStop")
        startdatetime: Optional[str] = Field(
            "Computation Startdatetime (yyyymmddhhmmss), when specified, overrides tStart",
            alias="startDateTime",
        )
        stopdatetime: Optional[str] = Field(
            "Computation Stopdatetime  (yyyymmddhhmmss), when specified, overrides tStop",
            alias="stopDateTime",
        )
        updateroughnessinterval: Optional[str] = Field(
            "Update interval for time dependent roughness parameters [s].",
            alias="updateRoughnessInterval",
        )
        dtfacmax: Optional[str] = Field(
            "Max timestep increase factor in successive time steps.", alias="Dtfacmax"
        )

    comments: Comments = Comments()

    _header: Literal["Time"] = "Time"
    refdate: int = Field(20200101, alias="refDate")  # TODO Convert to datetime
    tzone: float = Field(0.0, alias="tZone")
    tunit: str = Field("S", alias="tUnit")  # DHMS
    dtuser: float = Field(300.0, alias="dtUser")
    dtnodal: float = Field(21600.0, alias="dtNodal")
    dtmax: float = Field(30.0, alias="dtMax")
    dtinit: float = Field(1.0, alias="dtInit")
    autotimestep: Optional[int] = Field(1, alias="autoTimestep")
    autotimestepnostruct: bool = Field(False, alias="autoTimestepNoStruct")
    autotimestepnoqout: bool = Field(True, alias="autoTimestepNoQout")
    tstart: float = Field(0.0, alias="tStart")
    tstop: float = Field(86400.0, alias="tStop")
    startdatetime: Optional[str] = Field("", alias="startDateTime")
    stopdatetime: Optional[str] = Field("", alias="stopDateTime")
    updateroughnessinterval: float = Field(86400.0, alias="updateRoughnessInterval")
    dtfacmax: float = Field(1.1, alias="Dtfacmax")

    @validator("startdatetime", "stopdatetime")
    def _validate_datetime(cls, value, field):
        return validate_datetime_string(value, field)


class Restart(INIBasedModel):
    """
    The `[Restart]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.restart`.

    All lowercased attributes match with the [Restart] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        restartfile: Optional[str] = Field(
            "Restart file, only from netCDF-file, hence: either *_rst.nc or *_map.nc.",
            alias="restartFile",
        )
        restartdatetime: Optional[str] = Field(
            "Restart time [YYYYMMDDHHMMSS], only relevant in case of restart from *_map.nc.",
            alias="restartDateTime",
        )

    comments: Comments = Comments()

    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    _header: Literal["Restart"] = "Restart"
    restartfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="restartFile"
    )
    restartdatetime: Optional[str] = Field("", alias="restartDateTime")

    @validator("restartdatetime")
    def _validate_datetime(cls, value, field):
        return validate_datetime_string(value, field)


class ExternalForcing(INIBasedModel):
    """
    The `[External Forcing]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.external_forcing`.

    All lowercased attributes match with the [External Forcing] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        extforcefile: Optional[str] = Field(
            "Old format for external forcings file *.ext, link with tim/cmp-format boundary conditions specification.",
            alias="extForceFile",
        )
        extforcefilenew: Optional[str] = Field(
            "New format for external forcings file *.ext, link with bcformat boundary conditions specification.",
            alias="extForceFileNew",
        )
        rainfall: Optional[str] = Field(
            "Include rainfall, (0=no, 1=yes).", alias="rainfall"
        )
        qext: Optional[str] = Field(
            "Include user Qin/out, externally provided, (0=no, 1=yes).", alias="qExt"
        )
        evaporation: Optional[str] = Field(
            "Include evaporation in water balance, (0=no, 1=yes).", alias="evaporation"
        )
        windext: Optional[str] = Field(
            "Include wind, externally provided, (0=no, 1=reserved for EC, 2=yes).",
            alias="windExt",
        )

    comments: Comments = Comments()

    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    _header: Literal["External Forcing"] = "External Forcing"
    extforcefile: Optional[ExtOldModel] = Field(None, alias="extForceFile")
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

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.hydrology`.

    All lowercased attributes match with the [Hydrology] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        interceptionmodel: Optional[str] = Field(
            "Interception model (0: none, 1: on, via layer thickness).",
            alias="interceptionModel",
        )

    comments: Comments = Comments()

    _header: Literal["Hydrology"] = "Hydrology"
    interceptionmodel: bool = Field(False, alias="interceptionModel")


class Trachytopes(INIBasedModel):
    """
    The `[Trachytopes]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.trachytopes`.

    All lowercased attributes match with the [Trachytopes] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        trtrou: Optional[str] = Field(
            "Flag for trachytopes (Y=on, N=off).", alias="trtRou"
        )
        trtdef: Optional[str] = Field(
            "File (*.ttd) including trachytope definitions.", alias="trtDef"
        )
        trtl: Optional[str] = Field(
            "File (*.arl) including distribution of trachytope definitions.",
            alias="trtL",
        )
        dttrt: Optional[str] = Field(
            "Interval for updating of bottom roughness due to trachytopes in seconds [s].",
            alias="dtTrt",
        )
        trtmxr: Optional[str] = Field(
            "Maximum recursion level for composite trachytope definitions",
            alias="trtMxR",
        )

    comments: Comments = Comments()

    _header: Literal["Trachytopes"] = "Trachytopes"
    trtrou: str = Field("N", alias="trtRou")  # TODO bool
    trtdef: Optional[Path] = Field("", alias="trtDef")
    trtl: Optional[Path] = Field("", alias="trtL")
    dttrt: float = Field(60.0, alias="dtTrt")
    trtmxr: Optional[int] = Field(8, alias="trtMxR")


ObsFile = Union[XYNModel, ObservationPointModel]
ObsCrsFile = Union[PolyFile, ObservationCrossSectionModel]


class Output(INIBasedModel):
    """
    The `[Output]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.output`.

    All lowercased attributes match with the [Output] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        wrishp_crs: Optional[str] = Field(
            "Writing cross sections to shape file (0=no, 1=yes).", alias="wrishp_crs"
        )
        wrishp_weir: Optional[str] = Field(
            "Writing weirs to shape file (0=no, 1=yes).", alias="wrishp_weir"
        )
        wrishp_gate: Optional[str] = Field(
            "Writing gates to shape file (0=no, 1=yes).", alias="wrishp_gate"
        )
        wrishp_fxw: Optional[str] = Field(
            "Writing fixed weirs to shape file (0=no, 1=yes).", alias="wrishp_fxw"
        )
        wrishp_thd: Optional[str] = Field(
            "Writing thin dams to shape file (0=no, 1=yes).", alias="wrishp_thd"
        )
        wrishp_obs: Optional[str] = Field(
            "Writing observation points to shape file (0=no, 1=yes).",
            alias="wrishp_obs",
        )
        wrishp_emb: Optional[str] = Field(
            "Writing embankments file (0=no, 1=yes).", alias="wrishp_emb"
        )
        wrishp_dryarea: Optional[str] = Field(
            "Writing dry areas to shape file (0=no, 1=yes).", alias="wrishp_dryArea"
        )
        wrishp_enc: Optional[str] = Field(
            "Writing enclosures to shape file (0=no, 1=yes).", alias="wrishp_enc"
        )
        wrishp_src: Optional[str] = Field(
            "Writing sources and sinks to shape file (0=no, 1=yes).", alias="wrishp_src"
        )
        wrishp_pump: Optional[str] = Field(
            "Writing pumps to shape file (0=no, 1=yes).", alias="wrishp_pump"
        )
        outputdir: Optional[str] = Field(
            "Output directory of map-, his-, rst-, dat- and timingsfiles, default: DFM_OUTPUT_<modelname>. Set to . for no dir/current dir.",
            alias="outputDir",
        )
        waqoutputdir: Optional[str] = Field(
            "Output directory of Water Quality files.", alias="waqOutputDir"
        )
        flowgeomfile: Optional[str] = Field(
            "*_flowgeom.nc Flow geometry file in netCDF format.", alias="flowGeomFile"
        )
        obsfile: Optional[str] = Field(
            "Space separated list of files, containing information about observation points.",
            alias="obsFile",
        )
        crsfile: Optional[str] = Field(
            "Space separated list of files, containing information about observation cross sections.",
            alias="crsFile",
        )
        foufile: Optional[str] = Field(
            "Fourier analysis input file *.fou", alias="fouFile"
        )
        fouupdatestep: Optional[str] = Field(
            "Fourier update step type: 0=every user time step, 1=every computational timestep, 2=same as history output.",
            alias="fouUpdateStep",
        )
        hisfile: Optional[str] = Field(
            "*_his.nc History file in netCDF format.", alias="hisFile"
        )
        hisinterval: Optional[str] = Field(
            "History output, given as 'interval' 'start period' 'end period' [s].",
            alias="hisInterval",
        )
        xlsinterval: Optional[str] = Field(
            "Interval between XLS history [s].", alias="xlsInterval"
        )
        mapfile: Optional[str] = Field(
            "*_map.nc Map file in netCDF format.", alias="mapFile"
        )
        mapinterval: Optional[str] = Field(
            "Map file output, given as 'interval' 'start period' 'end period' [s].",
            alias="mapInterval",
        )
        rstinterval: Optional[str] = Field(
            "Restart file output, given as 'interval' 'start period' 'end period' [s].",
            alias="rstInterval",
        )
        mapformat: Optional[str] = Field(
            "Map file format, 1: netCDF, 2: Tecplot, 3: NetCFD and Tecplot, 4: netCDF UGRID.",
            alias="mapFormat",
        )
        ncformat: Optional[str] = Field(
            "Format for all NetCDF output files (3: classic, 4: NetCDF4+HDF5).",
            alias="ncFormat",
        )
        ncnounlimited: Optional[str] = Field(
            "Write full-length time-dimension instead of unlimited dimension (1: yes, 0: no). (Might require NcFormat=4.)",
            alias="ncNoUnlimited",
        )
        ncnoforcedflush: Optional[str] = Field(
            "Do not force flushing of map-like files every output timestep (1: yes, 0: no).",
            alias="ncNoForcedFlush",
        )
        ncwritelatlon: Optional[str] = Field(
            "Write extra lat-lon coordinates for all projected coordinate variables in each NetCDF file (for CF-compliancy) (1: yes, 0: no).",
            alias="ncWriteLatLon",
        )
        wrihis_balance: Optional[str] = Field(
            "Write mass balance totals to his file, (1: yes, 0: no).",
            alias="wrihis_balance",
        )
        wrihis_sourcesink: Optional[str] = Field(
            "Write sources-sinks statistics to his file, (1: yes, 0: no).",
            alias="wrihis_sourceSink",
        )
        wrihis_structure_gen: Optional[str] = Field(
            "Write general structure parameters to his file, (1: yes, 0: no).",
            alias="wrihis_structure_gen",
        )
        wrihis_structure_dam: Optional[str] = Field(
            "Write dam parameters to his file, (1: yes, 0: no).",
            alias="wrihis_structure_dam",
        )
        wrihis_structure_pump: Optional[str] = Field(
            "Write pump parameters to his file, (1: yes, 0: no).",
            alias="wrihis_structure_pump",
        )
        wrihis_structure_gate: Optional[str] = Field(
            "Write gate parameters to his file, (1: yes, 0: no).",
            alias="wrihis_structure_gate",
        )
        wrihis_structure_weir: Optional[str] = Field(
            "Write weir parameters to his file, (1: yes, 0: no).",
            alias="wrihis_structure_weir",
        )
        wrihis_structure_orifice: Optional[str] = Field(
            "Write orifice parameters to his file, (1: yes, 0: no).",
            alias="wrihis_structure_orifice",
        )
        wrihis_structure_bridge: Optional[str] = Field(
            "Write bridge parameters to his file, (1: yes, 0: no).",
            alias="wrihis_structure_bridge",
        )
        wrihis_structure_culvert: Optional[str] = Field(
            "Write culvert parameters to his file, (1: yes, 0: no).",
            alias="wrihis_structure_culvert",
        )
        wrihis_structure_longculvert: Optional[str] = Field(
            "Write long culvert parameters to his file, (1: yes, 0: no).",
            alias="wrihis_structure_longCulvert",
        )
        wrihis_structure_dambreak: Optional[str] = Field(
            "Write dam break parameters to his file, (1: yes, 0: no).",
            alias="wrihis_structure_damBreak",
        )
        wrihis_structure_uniweir: Optional[str] = Field(
            "Write universal weir parameters to his file, (1: yes, 0: no).",
            alias="wrihis_structure_uniWeir",
        )
        wrihis_structure_compound: Optional[str] = Field(
            "Write compound structure parameters to his file, (1: yes, 0: no).",
            alias="wrihis_structure_compound",
        )
        wrihis_turbulence: Optional[str] = Field(
            "Write k, eps and vicww to his file (1: yes, 0: no)'",
            alias="wrihis_turbulence",
        )
        wrihis_wind: Optional[str] = Field(
            "Write wind velocities to his file (1: yes, 0: no)'", alias="wrihis_wind"
        )
        wrihis_airdensity: Optional[str] = Field(
            "Write air density to his file (1: yes, 0: no)", alias="wrihis_airdensity"
        )
        wrihis_rain: Optional[str] = Field(
            "Write precipitation to his file (1: yes, 0: no)'", alias="wrihis_rain"
        )
        wrihis_infiltration: Optional[str] = Field(
            "Write infiltration to his file (1: yes, 0: no)'",
            alias="wrihis_infiltration",
        )
        wrihis_temperature: Optional[str] = Field(
            "Write temperature to his file (1: yes, 0: no)'", alias="wrihis_temperature"
        )
        wrihis_waves: Optional[str] = Field(
            "Write wave data to his file (1: yes, 0: no)'", alias="wrihis_waves"
        )
        wrihis_heat_fluxes: Optional[str] = Field(
            "Write heat fluxes to his file (1: yes, 0: no)'", alias="wrihis_heat_fluxes"
        )
        wrihis_salinity: Optional[str] = Field(
            "Write salinity to his file (1: yes, 0: no)'", alias="wrihis_salinity"
        )
        wrihis_density: Optional[str] = Field(
            "Write density to his file (1: yes, 0: no)'", alias="wrihis_density"
        )
        wrihis_waterlevel_s1: Optional[str] = Field(
            "Write water level to his file (1: yes, 0: no)'",
            alias="wrihis_waterlevel_s1",
        )
        wrihis_bedlevel: Optional[str] = Field(
            "Write bed level to his file (1: yes, 0: no)'", alias="wrihis_bedlevel"
        )
        wrihis_waterdepth: Optional[str] = Field(
            "Write water depth to his file (1: yes, 0: no)'", alias="wrihis_waterdepth"
        )
        wrihis_velocity_vector: Optional[str] = Field(
            "Write velocity vectors to his file (1: yes, 0: no)'",
            alias="wrihis_velocity_vector",
        )
        wrihis_upward_velocity_component: Optional[str] = Field(
            "Write upward velocity to his file (1: yes, 0: no)'",
            alias="wrihis_upward_velocity_component",
        )
        wrihis_velocity: Optional[str] = Field(
            "Write velocity magnitude in observation point to his file, (1: yes, 0: no).",
            alias="wrihis_velocity",
        )
        wrihis_discharge: Optional[str] = Field(
            "Write discharge magnitude in observation point to his file, (1: yes, 0: no).",
            alias="wrihis_discharge",
        )
        wrihis_sediment: Optional[str] = Field(
            "Write sediment transport to his file (1: yes, 0: no)'",
            alias="wrihis_sediment",
        )
        wrihis_constituents: Optional[str] = Field(
            "Write tracers to his file (1: yes, 0: no)'", alias="wrihis_constituents"
        )
        wrihis_zcor: Optional[str] = Field(
            "Write vertical coordinates to his file (1: yes, 0: no)'",
            alias="wrihis_zcor",
        )
        wrihis_lateral: Optional[str] = Field(
            "Write lateral data to his file, (1: yes, 0: no).", alias="wrihis_lateral"
        )
        wrihis_taucurrent: Optional[str] = Field(
            "Write mean bed shear stress to his file (1: yes, 0: no)'",
            alias="wrihis_taucurrent",
        )
        wrimap_waterlevel_s0: Optional[str] = Field(
            "Write water levels at old time level to map file, (1: yes, 0: no).",
            alias="wrimap_waterLevel_s0",
        )
        wrimap_waterlevel_s1: Optional[str] = Field(
            "Write water levels at new time level to map file, (1: yes, 0: no).",
            alias="wrimap_waterLevel_s1",
        )
        wrimap_evaporation: Optional[str] = Field(
            "Write evaporation to map file, (1: yes, 0: no).",
            alias="wrimap_evaporation",
        )
        wrimap_waterdepth: Optional[str] = Field(
            "Write water depths to map file (1: yes, 0: no).",
            alias="wrimap_waterdepth",
        )
        wrimap_velocity_component_u0: Optional[str] = Field(
            "Write velocities at old time level to map file, (1: yes, 0: no).",
            alias="wrimap_velocity_component_u0",
        )
        wrimap_velocity_component_u1: Optional[str] = Field(
            "Write velocities at new time level to map file, (1: yes, 0: no).",
            alias="wrimap_velocity_component_u1",
        )
        wrimap_velocity_vector: Optional[str] = Field(
            "Write cell-center velocity vectors to map file, (1: yes, 0: no).",
            alias="wrimap_velocity_vector",
        )
        wrimap_velocity_magnitude: Optional[str] = Field(
            "Write cell-center velocity vector magnitude to map file (1: yes, 0: no).",
            alias="wrimap_velocity_magnitude",
        )
        wrimap_upward_velocity_component: Optional[str] = Field(
            "Write upward velocity component to map file, (1: yes, 0: no).",
            alias="wrimap_upward_velocity_component",
        )
        wrimap_density_rho: Optional[str] = Field(
            "Write density to map file, (1: yes, 0: no).", alias="wrimap_density_rho"
        )
        wrimap_horizontal_viscosity_viu: Optional[str] = Field(
            "Write horizontal viscosity to map file, (1: yes, 0: no).",
            alias="wrimap_horizontal_viscosity_viu",
        )
        wrimap_horizontal_diffusivity_diu: Optional[str] = Field(
            "Write horizontal diffusivity to map file, (1: yes, 0: no).",
            alias="wrimap_horizontal_diffusivity_diu",
        )
        wrimap_flow_flux_q1: Optional[str] = Field(
            "Write fluxes to map file, (1: yes, 0: no).", alias="wrimap_flow_flux_q1"
        )
        wrimap_spiral_flow: Optional[str] = Field(
            "Write spiral flow to map file, (1: yes, 0: no).",
            alias="wrimap_spiral_flow",
        )
        wrimap_numlimdt: Optional[str] = Field(
            "Write numlimdt to map file, (1: yes, 0: no).", alias="wrimap_numLimdt"
        )
        wrimap_taucurrent: Optional[str] = Field(
            "Write bottom friction to map file, (1: yes, 0: no).",
            alias="wrimap_tauCurrent",
        )
        wrimap_chezy: Optional[str] = Field(
            "Write chezy values to map file, (1: yes, 0: no).", alias="wrimap_chezy"
        )
        wrimap_turbulence: Optional[str] = Field(
            "Write turbulence to map file, (1: yes, 0: no).", alias="wrimap_turbulence"
        )
        wrimap_rain: Optional[str] = Field(
            "Write rainfall rate to map file, (1: yes, 0: no).", alias="wrimap_rain"
        )
        wrimap_wind: Optional[str] = Field(
            "Write winds to map file, (1: yes, 0: no).", alias="wrimap_wind"
        )
        wrimap_windstress: Optional[str] = Field(
            "Write wind stress to map file (1: yes, 0: no)", alias="wrimap_windstress"
        )
        wrimap_airdensity: Optional[str] = Field(
            "Write air density rates to map file (1: yes, 0: no)",
            alias="wrimap_airdensity",
        )
        wrimap_calibration: Optional[str] = Field(
            "Write roughness calibration factors to map file.",
            alias="wrimap_calibration",
        )
        wrimap_salinity: Optional[str] = Field(
            "Write salinity to map file.", alias="wrimap_salinity"
        )
        wrimap_temperature: Optional[str] = Field(
            "Write temperature to map file.", alias="wrimap_temperature"
        )
        writek_cdwind: Optional[str] = Field(
            "Write wind friction coefficients to tek file (1: yes, 0: no).",
            alias="writek_CdWind",
        )
        wrimap_heat_fluxes: Optional[str] = Field(
            "Write heat fluxes to map file, (1: yes, 0: no).",
            alias="wrimap_heat_fluxes",
        )
        wrimap_wet_waterdepth_threshold: Optional[str] = Field(
            "Waterdepth threshold above which a grid point counts as 'wet'. Defaults to 0.2·Epshu. It is used for Wrimap_time_water_on_ground, Wrimap_waterdepth_on_ground and Wrimap_volume_on_ground.",
            alias="wrimap_wet_waterDepth_threshold",
        )
        wrimap_time_water_on_ground: Optional[str] = Field(
            "Write cumulative time when water is above ground level (only for 1D nodes) to map file, (1: yes, 0: no).",
            alias="wrimap_time_water_on_ground",
        )
        wrimap_freeboard: Optional[str] = Field(
            "Write freeboard (only for 1D nodes) to map file, (1: yes, 0: no).",
            alias="wrimap_freeboard",
        )
        wrimap_waterdepth_on_ground: Optional[str] = Field(
            "Write waterdepth that is above ground level to map file (only for 1D nodes) (1: yes, 0: no).",
            alias="wrimap_waterDepth_on_ground",
        )
        wrimap_volume_on_ground: Optional[str] = Field(
            "Write volume that is above ground level to map file (only for 1D nodes) (1: yes, 0: no).",
            alias="wrimap_volume_on_ground",
        )
        wrimap_total_net_inflow_1d2d: Optional[str] = Field(
            "Write current total 1D2D net inflow (discharge) and cumulative total 1D2D net inflow (volume) to map file (only for 1D nodes) (1:yes, 0:no).",
            alias="wrimap_total_net_inflow_1d2d",
        )
        wrimap_total_net_inflow_lateral: Optional[str] = Field(
            "Write current total lateral net inflow (discharge) and cumulative total lateral net inflow (volume) to map file (only for 1D nodes) (1:yes, 0:no).",
            alias="wrimap_total_net_inflow_lateral",
        )
        wrimap_water_level_gradient: Optional[str] = Field(
            "Write water level gradient to map file (only for 1D links) (1:yes, 0:no).",
            alias="wrimap_water_level_gradient",
        )
        wrimap_tidal_potential: Optional[str] = Field(
            "Write tidal potential to map file (1: yes, 0: no)",
            alias="wrimap_tidal_potential",
        )
        wrimap_sal_potential: Optional[str] = Field(
            "Write self attraction and loading potential to map file (1: yes, 0: no)",
            alias="wrimap_SAL_potential",
        )
        wrimap_internal_tides_dissipation: Optional[str] = Field(
            "Write internal tides dissipation to map file (1: yes, 0: no)",
            alias="wrimap_internal_tides_dissipation",
        )
        wrimap_flow_analysis: Optional[str] = Field(
            "Write flow analysis data to the map file (1:yes, 0:no).",
            alias="wrimap_flow_analysis",
        )
        mapoutputtimevector: Optional[str] = Field(
            "File (.mpt) containing fixed map output times (s) w.r.t. RefDate.",
            alias="mapOutputTimeVector",
        )
        fullgridoutput: Optional[str] = Field(
            "Full grid output mode for layer positions (0: compact, 1: full time-varying grid layer data).",
            alias="fullGridOutput",
        )
        eulervelocities: Optional[str] = Field(
            "Write Eulerian velocities, (1: yes, 0: no).", alias="eulerVelocities"
        )
        classmapfile: Optional[str] = Field(
            "Name of class map file.", alias="classMapFile"
        )
        waterlevelclasses: Optional[str] = Field(
            "Series of values between which water level classes are computed.",
            alias="waterLevelClasses",
        )
        waterdepthclasses: Optional[str] = Field(
            "Series of values between which water depth classes are computed.",
            alias="waterDepthClasses",
        )
        classmapinterval: Optional[str] = Field(
            "Interval [s] between class map file outputs.", alias="classMapInterval"
        )
        waqinterval: Optional[str] = Field(
            "Interval [s] between DELWAQ file outputs.", alias="waqInterval"
        )
        statsinterval: Optional[str] = Field(
            "Interval [s] between screen step outputs in seconds simulation time, if negative in seconds wall clock time.",
            alias="statsInterval",
        )
        timingsinterval: Optional[str] = Field(
            "Timings output interval TimingsInterval.", alias="timingsInterval"
        )
        richardsononoutput: Optional[str] = Field(
            "Write Richardson number, (1: yes, 0: no).", alias="richardsonOnOutput"
        )
        wrimap_every_dt: Optional[str] = Field(
            "Write output to map file every computational timestep, between start and stop time from MapInterval, (1: yes, 0: no).",
            alias="wrimap_every_dt",
        )
        wrimap_input_roughness: Optional[str] = Field(
            "Write chezy input roughness on flow links to map file, (1: yes, 0: no).",
            alias="wrimap_input_roughness",
        )
        wrimap_flowarea_au: Optional[str] = Field(
            "Write flow areas au to map file (1: yes, 0: no).",
            alias="wrimap_flowarea_au",
        )
        wrihis_airdensity: Optional[str] = Field(
            "Write air density to his file (1: yes, 0: no).", alias="wrihis_airdensity"
        )
        wrimap_flow_flux_q1_main: Optional[str] = Field(
            "Write flow flux in main channel to map file (1: yes, 0: no).",
            alias="wrimap_flow_flux_q1_main",
        )
        wrimap_windstress: Optional[str] = Field(
            "Write wind stress to map file (1: yes, 0: no).", alias="wrimap_windstress"
        )
        wrishp_genstruc: Optional[str] = Field(
            "Writing general structures to shape file (0=no, 1=yes).",
            alias="wrishp_genstruc",
        )
        wrimap_qin: Optional[str] = Field(
            "Write sum of all influxes to map file (1: yes, 0: no).", alias="wrimap_qin"
        )
        wrimap_dtcell: Optional[str] = Field(
            "Write time step per cell based on CFL (1: yes, 0: no).",
            alias="wrimap_dtcell",
        )
        wrimap_velocity_vectorq: Optional[str] = Field(
            "Write cell-center velocity vectors (discharge-based) to map file (1: yes, 0: no).",
            alias="wrimap_velocity_vectorq",
        )
        wrimap_bnd: Optional[str] = Field(
            "Write boundary points to map file (1: yes, 0: no).", alias="wrimap_bnd"
        )
        wrishp_dambreak: Optional[str] = Field(
            "Writing dambreaks to shape file (0=no, 1=yes).", alias="wrishp_dambreak"
        )
        wrimap_waterdepth_hu: Optional[str] = Field(
            "Write water depths on u-points to map file (1: yes, 0: no).",
            alias="wrimap_waterdepth_hu",
        )
        ncmapdataprecision: Optional[str] = Field(
            "Precision for NetCDF data in map files (double or single).",
            alias="ncMapDataPrecision",
        )
        nchisdataprecision: Optional[str] = Field(
            "Precision for NetCDF data in his files (double or single).",
            alias="ncHisDataPrecision",
        )
        wrimap_interception: Optional[str] = Field(
            "Write interception to map file (1: yes, 0: no).",
            alias="wrimap_interception",
        )
        wrimap_airdensity: Optional[str] = Field(
            "Write air density to map file, (1:yes, 0:no).", alias="wrimap_airdensity"
        )
        wrimap_volume1: Optional[str] = Field(
            "Write volumes to map file (1: yes, 0: no).", alias="wrimap_volume1"
        )
        wrimap_ancillary_variables: Optional[str] = Field(
            "Write ancillary variables attributes to map file (1: yes, 0: no).",
            alias="wrimap_ancillary_variables",
        )
        wrimap_chezy_on_flow_links: Optional[str] = Field(
            "Write chezy roughness on flow links to map file, (1: yes, 0: no)",
            alias="wrimap_chezy_on_flow_links",
        )
        writepart_domain: Optional[str] = Field(
            "Write partition domain info. for postprocessing (0: no, 1: yes).",
            alias="writepart_domain",
        )
        velocitydirectionclassesinterval: Optional[str] = Field(
            "Class map's step size of class values for velocity direction.",
            alias="VelocityDirectionClassesInterval",
        )
        velocitymagnitudeclasses: Optional[str] = Field(
            "Class map's list of class values for velocity magnitudes.",
            alias="VelocityMagnitudeClasses",
        )

    comments: Comments = Comments()

    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

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
    outputdir: Optional[Path] = Field("", alias="outputDir")
    waqoutputdir: Optional[Path] = Field("", alias="waqOutputDir")
    flowgeomfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="flowGeomFile"
    )
    obsfile: Optional[List[ObsFile]] = Field(None, alias="obsFile")
    crsfile: Optional[List[ObsCrsFile]] = Field(None, alias="crsFile")
    foufile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="fouFile"
    )
    fouupdatestep: int = Field(0, alias="fouUpdateStep")
    hisfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="hisFile"
    )
    hisinterval: List[float] = Field([300.0], alias="hisInterval")
    xlsinterval: List[float] = Field([0.0], alias="xlsInterval")
    mapfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="mapFile"
    )
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
    wrihis_turbulence: bool = Field(True, alias="wrihis_turbulence")
    wrihis_wind: bool = Field(True, alias="wrihis_wind")
    wrihis_airdensity: bool = Field(False, alias="wrihis_airdensity")
    wrihis_rain: bool = Field(True, alias="wrihis_rain")
    wrihis_infiltration: bool = Field(True, alias="wrihis_infiltration")
    wrihis_temperature: bool = Field(True, alias="wrihis_temperature")
    wrihis_waves: bool = Field(True, alias="wrihis_waves")
    wrihis_heat_fluxes: bool = Field(True, alias="wrihis_heat_fluxes")
    wrihis_salinity: bool = Field(True, alias="wrihis_salinity")
    wrihis_density: bool = Field(True, alias="wrihis_density")
    wrihis_waterlevel_s1: bool = Field(True, alias="wrihis_waterlevel_s1")
    wrihis_bedlevel: bool = Field(True, alias="wrihis_bedlevel")
    wrihis_waterdepth: bool = Field(False, alias="wrihis_waterdepth")
    wrihis_velocity_vector: bool = Field(True, alias="wrihis_velocity_vector")
    wrihis_upward_velocity_component: bool = Field(
        False, alias="wrihis_upward_velocity_component"
    )
    wrihis_velocity: bool = Field(False, alias="wrihis_velocity")
    wrihis_discharge: bool = Field(False, alias="wrihis_discharge")
    wrihis_sediment: bool = Field(True, alias="wrihis_sediment")
    wrihis_constituents: bool = Field(True, alias="wrihis_constituents")
    wrihis_zcor: bool = Field(True, alias="wrihis_zcor")
    wrihis_lateral: bool = Field(True, alias="wrihis_lateral")
    wrihis_taucurrent: bool = Field(True, alias="wrihis_taucurrent")

    # Map file
    wrimap_waterlevel_s0: bool = Field(True, alias="wrimap_waterLevel_s0")
    wrimap_waterlevel_s1: bool = Field(True, alias="wrimap_waterLevel_s1")
    wrimap_evaporation: bool = Field(False, alias="wrimap_evaporation")
    wrimap_waterdepth: bool = Field(True, alias="wrimap_waterdepth")
    wrimap_velocity_component_u0: bool = Field(
        True, alias="wrimap_velocity_component_u0"
    )
    wrimap_velocity_component_u1: bool = Field(
        True, alias="wrimap_velocity_component_u1"
    )
    wrimap_velocity_vector: bool = Field(True, alias="wrimap_velocity_vector")
    wrimap_velocity_magnitude: bool = Field(True, alias="wrimap_velocity_magnitude")
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
    wrimap_windstress: bool = Field(False, alias="wrimap_windstress")
    wrimap_airdensity: bool = Field(False, alias="wrimap_airdensity")
    wrimap_calibration: bool = Field(True, alias="wrimap_calibration")
    wrimap_salinity: bool = Field(True, alias="wrimap_salinity")
    wrimap_temperature: bool = Field(True, alias="wrimap_temperature")
    writek_cdwind: bool = Field(False, alias="writek_CdWind")
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
    wrimap_tidal_potential: bool = Field(True, alias="wrimap_tidal_potential")
    wrimap_sal_potential: bool = Field(True, alias="wrimap_SAL_potential")
    wrimap_internal_tides_dissipation: bool = Field(
        True, alias="wrimap_internal_tides_dissipation"
    )
    wrimap_flow_analysis: bool = Field(False, alias="wrimap_flow_analysis")
    mapoutputtimevector: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="mapOutputTimeVector"
    )
    fullgridoutput: bool = Field(False, alias="fullGridOutput")
    eulervelocities: bool = Field(False, alias="eulerVelocities")
    classmapfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="classMapFile"
    )
    waterlevelclasses: List[float] = Field([0.0], alias="waterLevelClasses")
    waterdepthclasses: List[float] = Field([0.0], alias="waterDepthClasses")
    classmapinterval: List[float] = Field([0.0], alias="classMapInterval")
    waqinterval: List[float] = Field([0.0], alias="waqInterval")
    statsinterval: List[float] = Field([-60.0], alias="statsInterval")
    timingsinterval: List[float] = Field([0.0], alias="timingsInterval")
    richardsononoutput: bool = Field(False, alias="richardsonOnOutput")
    wrimap_every_dt: bool = Field(False, alias="wrimap_every_dt")
    wrimap_input_roughness: bool = Field(False, alias="wrimap_input_roughness")
    wrimap_flowarea_au: bool = Field(False, alias="wrimap_flowarea_au")
    wrihis_airdensity: bool = Field(False, alias="wrihis_airdensity")
    wrimap_flow_flux_q1_main: bool = Field(False, alias="wrimap_flow_flux_q1_main")
    wrimap_windstress: bool = Field(False, alias="wrimap_windstress")
    wrishp_genstruc: bool = Field(False, alias="wrishp_genstruc")
    wrimap_qin: bool = Field(False, alias="wrimap_qin")
    wrimap_dtcell: bool = Field(False, alias="wrimap_dtcell")
    wrimap_velocity_vectorq: bool = Field(False, alias="wrimap_velocity_vectorq")
    wrimap_bnd: bool = Field(False, alias="wrimap_bnd")
    wrishp_dambreak: bool = Field(False, alias="wrishp_dambreak")
    wrimap_waterdepth_hu: bool = Field(False, alias="wrimap_waterdepth_hu")
    ncmapdataprecision: Literal["single", "double"] = Field(
        "double", alias="ncMapDataPrecision"
    )
    nchisdataprecision: Literal["single", "double"] = Field(
        "double", alias="ncHisDataPrecision"
    )
    wrimap_interception: bool = Field(False, alias="wrimap_interception")
    wrimap_airdensity: bool = Field(False, alias="wrimap_airdensity")
    wrimap_volume1: bool = Field(False, alias="wrimap_volume1")
    wrimap_ancillary_variables: bool = Field(False, alias="wrimap_ancillary_variables")
    wrimap_chezy_on_flow_links: bool = Field(False, alias="wrimap_chezy_on_flow_links")
    writepart_domain: bool = Field(True, alias="writepart_domain")
    velocitydirectionclassesinterval: float = Field(
        0.0, alias="VelocityDirectionClassesInterval"
    )
    velocitymagnitudeclasses: List[float] = Field(
        [0.0], alias="VelocityMagnitudeClasses"
    )

    _split_to_list = get_split_string_on_delimiter_validator(
        "waterlevelclasses",
        "waterdepthclasses",
        "crsfile",
        "obsfile",
        "hisinterval",
        "xlsinterval",
        "mapinterval",
        "rstinterval",
        "classmapinterval",
        "waqinterval",
        "statsinterval",
        "timingsinterval",
        "velocitymagnitudeclasses",
    )

    def is_intermediate_link(self) -> bool:
        return True


class Geometry(INIBasedModel):
    """
    The `[Geometry]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry`.

    All lowercased attributes match with the [Geometry] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        netfile: Optional[str] = Field("The net file <*_net.nc>", alias="netFile")
        bathymetryfile: Optional[str] = Field(
            "Removed since March 2022. See [geometry] keyword BedLevelFile.",
            alias="bathymetryFile",
        )
        drypointsfile: Optional[str] = Field(
            "Dry points file <*.xyz>, third column dummy z values, or polygon file <*.pol>.",
            alias="dryPointsFile",
        )
        structurefile: Optional[str] = Field(
            "File <*.ini> containing list of hydraulic structures.",
            alias="structureFile",
        )
        inifieldfile: Optional[str] = Field(
            "Initial and parameter field file <*.ini>.",
            alias="iniFieldFile",
        )
        waterlevinifile: Optional[str] = Field(
            "Initial water levels sample file <*.xyz>.", alias="waterLevIniFile"
        )
        landboundaryfile: Optional[str] = Field(
            "Only for plotting.", alias="landBoundaryFile"
        )
        thindamfile: Optional[str] = Field(
            "<*_thd.pli>, Polyline(s) for tracing thin dams.", alias="thinDamFile"
        )
        fixedweirfile: Optional[str] = Field(
            "<*_fxw.pliz>, Polyline(s) x, y, z, z = fixed weir top levels (formerly fixed weir).",
            alias="fixedWeirFile",
        )
        pillarfile: Optional[str] = Field(
            "<*_pillar.pliz>, Polyline file containing four colums with x, y, diameter and Cd coefficient for bridge pillars.",
            alias="pillarFile",
        )
        usecaching: Optional[str] = Field(
            "Use caching for geometrical/network-related items (0: no, 1: yes) (section C.19).",
            alias="useCaching",
        )
        vertplizfile: Optional[str] = Field(
            "<*_vlay.pliz>), = pliz with x, y, Z, first Z = nr of layers, second Z = laytyp.",
            alias="vertPlizFile",
        )
        frictfile: Optional[str] = Field(
            "Location of the files with roughness data for 1D.",
            alias="frictFile",
        )
        crossdeffile: Optional[str] = Field(
            "Cross section definitions for all cross section shapes.",
            alias="crossDefFile",
        )
        crosslocfile: Optional[str] = Field(
            "Location definitions of the cross sections on a 1D network.",
            alias="crossLocFile",
        )
        storagenodefile: Optional[str] = Field(
            "File containing the specification of storage nodes and/or manholes to add extra storage to 1D models.",
            alias="storageNodeFile",
        )
        oned2dlinkfile: Optional[str] = Field(
            "File containing the custom parameterization of 1D-2D links.",
            alias="1d2dLinkFile",
        )
        proflocfile: Optional[str] = Field(
            "<*_proflocation.xyz>) x, y, z, z = profile refnumber.", alias="profLocFile"
        )
        profdeffile: Optional[str] = Field(
            "<*_profdefinition.def>) definition for all profile nrs.",
            alias="profDefFile",
        )
        profdefxyzfile: Optional[str] = Field(
            "<*_profdefinition.def>) definition for all profile nrs.",
            alias="profDefXyzFile",
        )
        manholefile: Optional[str] = Field(
            "File containing manholes (e.g. <*.dat>).", alias="manholeFile"
        )
        partitionfile: Optional[str] = Field(
            "<*_part.pol>, polyline(s) x, y.", alias="partitionFile"
        )
        uniformwidth1d: Optional[str] = Field(
            "Uniform width for channel profiles not specified by profloc",
            alias="uniformWidth1D",
        )
        dxwuimin2d: Optional[str] = Field(
            "Smallest fraction dx/wu , set dx > Dxwuimin2D*wu",
            alias="dxWuiMin2D",
        )
        waterlevini: Optional[str] = Field("Initial water level.", alias="waterLevIni")
        bedlevuni: Optional[str] = Field(
            "Uniform bed level [m], (only if bedlevtype>=3), used at missing z values in netfile.",
            alias="bedLevUni",
        )
        bedslope: Optional[str] = Field(
            "Bed slope inclination, sets zk = bedlevuni + x*bedslope ans sets zbndz = xbndz*bedslope.",
            alias="bedSlope",
        )
        bedlevtype: Optional[str] = Field(
            "1: at cell center (tiles xz,yz,bl,bob=max(bl)), 2: at face (tiles xu,yu,blu,bob=blu), 3: at face (using mean node values), 4: at face (using min node values), 5: at face (using max node values), 6: with bl based on node values.",
            alias="bedLevType",
        )
        blmeanbelow: Optional[str] = Field(
            "if not -999d0, below this level [m] the cell centre bedlevel is the mean of surrouding netnodes.",
            alias="blMeanBelow",
        )
        blminabove: Optional[str] = Field(
            "if not -999d0, above this level [m] the cell centre bedlevel is the min of surrouding netnodes.",
            alias="blMinAbove",
        )
        anglat: Optional[str] = Field(
            "Angle of latitude S-N [deg], 0=no Coriolis.", alias="angLat"
        )
        anglon: Optional[str] = Field(
            "Angle of longitude E-W [deg], 0=Greenwich Mean Time.", alias="angLon"
        )
        conveyance2d: Optional[str] = Field(
            "-1:R=HU, 0:R=H, 1:R=A/P, 2:K=analytic-1D conv, 3:K=analytic-2D conv.",
            alias="conveyance2D",
        )
        nonlin1d: Optional[str] = Field(
            "Non-linear 1D volumes, applicable for models with closed cross sections. 1=treat closed sections as partially open by using a Preissmann slot, 2=Nested Newton approach, 3=Partial Nested Newton approach.",
            alias="nonlin1D",
        )
        nonlin2d: Optional[str] = Field(
            "Non-linear 2D volumes, only i.c.m. ibedlevtype = 3 and Conveyance2D>=1.",
            alias="nonlin2D",
        )
        sillheightmin: Optional[str] = Field(
            "Fixed weir only active if both ground heights are larger than this value [m].",
            alias="sillHeightMin",
        )
        makeorthocenters: Optional[str] = Field(
            "(1: yes, 0: no) switch from circumcentres to orthocentres in geominit.",
            alias="makeOrthoCenters",
        )
        dcenterinside: Optional[str] = Field(
            "limit cell center; 1.0:in cell <-> 0.0:on c/g.", alias="dCenterInside"
        )
        bamin: Optional[str] = Field(
            "Minimum grid cell area [m2], i.c.m. cutcells.", alias="baMin"
        )
        openboundarytolerance: Optional[str] = Field(
            "Search tolerance factor between boundary polyline and grid cells. [Unit: in cell size units (i.e., not meters)].",
            alias="openBoundaryTolerance",
        )
        renumberflownodes: Optional[str] = Field(
            "Renumber the flow nodes (1: yes, 0: no).", alias="renumberFlowNodes"
        )
        kmx: Optional[str] = Field("Number of vertical layers.", alias="kmx")
        layertype: Optional[str] = Field(
            "1= sigma-layers, 2 = z-layers, 3 = use VertplizFile.", alias="layerType"
        )
        numtopsig: Optional[str] = Field(
            "Number of sigma-layers on top of z-layers.", alias="numTopSig"
        )
        numtopsiguniform: Optional[str] = Field(
            "Spatially constant number of sigma layers above z-layers in a z-sigma model (1: yes, 0: no, spatially varying)",
            alias="numTopSigUniform",
        )
        dztop: Optional[str] = Field(
            "Z-layer thickness of layers above level Dztopuniabovez", alias="dzTop"
        )
        floorlevtoplay: Optional[str] = Field(
            "Floor level of top layer", alias="floorLevTopLay"
        )
        dztopuniabovez: Optional[str] = Field(
            "Above this level layers will have uniform dzTop, below we use sigmaGrowthFactor",
            alias="dzTopUniAboveZ",
        )
        keepzlayeringatbed: Optional[str] = Field(
            "0:possibly very thin layer at bed, 1:bedlayerthickness == zlayerthickness, 2=equal thickness first two layers",
            alias="keepZLayeringAtBed",
        )
        sigmagrowthfactor: Optional[str] = Field(
            "layer thickness growth factor from bed up.", alias="sigmaGrowthFactor"
        )
        dxdoubleat1dendnodes: Optional[str] = Field(
            "Whether a 1D grid cell at the end of a network has to be extended with 0.5Δx.",
            alias="dxDoubleAt1DEndNodes",
        )
        changevelocityatstructures: Optional[str] = Field(
            "Ignore structure dimensions for the velocity at hydraulic structures, when calculating the surrounding cell centered flow velocities.",
            alias="changeVelocityAtStructures",
        )
        changestructuredimensions: Optional[str] = Field(
            "Change the structure dimensions in case these are inconsistent with the channel dimensions.",
            alias="changeStructureDimensions",
        )
        gridenclosurefile: Optional[str] = Field(
            "Enclosure file <*.pol> to clip outer parts from the grid.",
            alias="gridEnclosureFile",
        )
        allowbndatbifurcation: Optional[str] = Field(
            "Allow 1d boundary node when connectin branch leads to bifurcation (1: yes, 0: no).",
            alias="allowBndAtBifurcation",
        )
        slotw1d: Optional[str] = Field("Minimum slotwidth 1D [m].", alias="slotw1D")
        slotw2d: Optional[str] = Field("Minimum slotwidth 2D [m].", alias="slotw2D")
        uniformheight1droofgutterpipes: Optional[str] = Field(
            "Uniform height for roof gutter pipes [m].",
            alias="uniformHeight1DRoofGutterPipes",
        )
        dxmin1d: Optional[str] = Field("Minimum 1D link length [m].", alias="dxmin1D")
        uniformtyp1dstreetinlets: Optional[str] = Field(
            "Uniform cross section type for street inlets (1: circle, 2: rectangle, -2: closed rectangle).",
            alias="uniformTyp1DStreetInlets",
        )
        stretchtype: Optional[str] = Field(
            "Stretching type for non-uniform layers, 1=user defined, 2=exponential, otherwise=uniform.",
            alias="stretchType",
        )
        zlaybot: Optional[str] = Field(
            "if specified, first z-layer starts from zlaybot [ ], if not, it starts from the lowest bed point.",
            alias="zlayBot",
        )
        zlaytop: Optional[str] = Field(
            "if specified, highest z-layer ends at zlaytop [ ], if not, it ends at the initial water level.",
            alias="zlayTop",
        )
        uniformheight1d: Optional[str] = Field(
            "Uniform height for 1D profiles and 1d2d internal links [m].",
            alias="uniformHeight1D",
        )
        roofsfile: Optional[str] = Field(
            "Polyline file <*_roof.pliz>, containing roofgutter heights x, y, z level.",
            alias="roofsFile",
        )
        gulliesfile: Optional[str] = Field(
            "Polyline file <*_gul.pliz>, containing lowest bed level along talweg x, y, z level.",
            alias="gulliesFile",
        )
        uniformwidth1dstreetinlets: Optional[str] = Field(
            "Uniform width for street inlets [m].", alias="uniformWidth1DStreetInlets"
        )
        uniformheight1dstreetinlets: Optional[str] = Field(
            "Uniform height for street inlets [m]", alias="uniformHeight1DStreetInlets"
        )
        uniformtyp1droofgutterpipes: Optional[str] = Field(
            "Uniform cross section type for type roof gutter pipes (1: circle, 2: rectangle, -2: closed rectangle).",
            alias="uniformTyp1DRoofGutterPipes",
        )
        uniformwidth1droofgutterpipes: Optional[str] = Field(
            "Uniform width for roof gutter pipes [m].",
            alias="uniformWidth1DRoofGutterPipes",
        )

    comments: Comments = Comments()

    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    _header: Literal["Geometry"] = "Geometry"
    netfile: Optional[NetworkModel] = Field(
        default_factory=NetworkModel, alias="netFile"
    )
    bathymetryfile: Optional[XYZModel] = Field(None, alias="bathymetryFile")
    drypointsfile: Optional[List[Union[XYZModel, PolyFile]]] = Field(
        None, alias="dryPointsFile"
    )  # TODO Fix, this will always try XYZ first, alias="]")
    structurefile: Optional[List[StructureModel]] = Field(
        None, alias="structureFile", delimiter=";"
    )
    inifieldfile: Optional[IniFieldModel] = Field(None, alias="iniFieldFile")
    waterlevinifile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="waterLevIniFile"
    )
    landboundaryfile: Optional[List[DiskOnlyFileModel]] = Field(
        None, alias="landBoundaryFile"
    )
    thindamfile: Optional[List[PolyFile]] = Field(None, alias="thinDamFile")
    fixedweirfile: Optional[List[PolyFile]] = Field(None, alias="fixedWeirFile")
    pillarfile: Optional[List[PolyFile]] = Field(None, alias="pillarFile")
    usecaching: bool = Field(True, alias="useCaching")
    vertplizfile: Optional[PolyFile] = Field(None, alias="vertPlizFile")
    frictfile: Optional[List[FrictionModel]] = Field(
        None, alias="frictFile", delimiter=";"
    )
    crossdeffile: Optional[CrossDefModel] = Field(None, alias="crossDefFile")
    crosslocfile: Optional[CrossLocModel] = Field(None, alias="crossLocFile")
    storagenodefile: Optional[StorageNodeModel] = Field(None, alias="storageNodeFile")
    oned2dlinkfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="1d2dLinkFile"
    )
    proflocfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="profLocFile"
    )
    profdeffile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="profDefFile"
    )
    profdefxyzfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="profDefXyzFile"
    )
    manholefile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="manholeFile"
    )
    partitionfile: Optional[PolyFile] = Field(None, alias="partitionFile")
    uniformwidth1d: float = Field(2.0, alias="uniformWidth1D")
    dxwuimin2d: float = Field(0.0, alias="dxWuiMin2D")
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
    numtopsiguniform: bool = Field(True, alias="numTopSigUniform")
    sigmagrowthfactor: float = Field(1.0, alias="sigmaGrowthFactor")
    dztop: Optional[float] = Field(-999, alias="dzTop")
    floorlevtoplay: Optional[float] = Field(-999, alias="floorLevTopLay")
    dztopuniabovez: Optional[float] = Field(-999, alias="dzTopUniAboveZ")
    keepzlayeringatbed: int = Field(2, alias="keepZLayeringAtBed")
    dxdoubleat1dendnodes: bool = Field(True, alias="dxDoubleAt1DEndNodes")
    changevelocityatstructures: bool = Field(False, alias="changeVelocityAtStructures")
    changestructuredimensions: bool = Field(True, alias="changeStructureDimensions")
    gridenclosurefile: Optional[PolyFile] = Field(None, alias="gridEnclosureFile")
    allowbndatbifurcation: bool = Field(False, alias="allowBndAtBifurcation")
    slotw1d: float = Field(0.001, alias="slotw1D")
    slotw2d: float = Field(0.001, alias="slotw2D")
    uniformheight1droofgutterpipes: float = Field(
        0.1, alias="uniformHeight1DRoofGutterPipes"
    )
    dxmin1d: float = Field(0.001, alias="dxmin1D")
    uniformtyp1dstreetinlets: int = Field(-2, alias="uniformTyp1DStreetInlets")
    stretchtype: int = Field(-1, alias="stretchType")
    zlaybot: float = Field(-999.0, alias="zlayBot")
    zlaytop: float = Field(-999.0, alias="zlayTop")
    uniformheight1d: float = Field(3.0, alias="uniformHeight1D")
    roofsfile: Optional[PolyFile] = Field(None, alias="roofsFile")
    gulliesfile: Optional[PolyFile] = Field(None, alias="gulliesFile")
    uniformwidth1dstreetinlets: float = Field(0.2, alias="uniformWidth1DStreetInlets")
    uniformheight1dstreetinlets: float = Field(0.1, alias="uniformHeight1DStreetInlets")
    uniformtyp1droofgutterpipes: int = Field(-2, alias="uniformTyp1DRoofGutterPipes")
    uniformwidth1droofgutterpipes: float = Field(
        0.1, alias="uniformWidth1DRoofGutterPipes"
    )

    _split_to_list = get_split_string_on_delimiter_validator(
        "frictfile",
        "structurefile",
        "drypointsfile",
        "landboundaryfile",
        "thindamfile",
        "fixedweirfile",
        "pillarfile",
    )

    def is_intermediate_link(self) -> bool:
        return True


class Calibration(INIBasedModel):
    """
    The `[Calibration]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.calibration`.

    All lowercased attributes match with the [Calibration] input as described in
    [UM Sec.A.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.3).
    """

    class Comments(INIBasedModel.Comments):
        usecalibration: Optional[str] = Field(
            "Activate calibration factor friction multiplier (0: no, 1: yes).",
            alias="UseCalibration",
        )
        definitionfile: Optional[str] = Field(
            "File (*.cld) containing calibration definitions.",
            alias="DefinitionFile",
        )
        areafile: Optional[str] = Field(
            "File (*.cll) containing area distribution of calibration definitions.",
            alias="AreaFile",
        )

    comments: Comments = Comments()

    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    _header: Literal["Calibration"] = "Calibration"
    usecalibration: bool = Field(False, alias="UseCalibration")
    definitionfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="DefinitionFile"
    )
    areafile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="AreaFile"
    )


class InfiltrationMethod(IntEnum):
    """
    Enum class containing the valid values for the Infiltrationmodel
    attribute in the [GroundWater][hydrolib.core.dflowfm.mdu.models.GroundWater] class.
    """

    NoInfiltration = 0
    InterceptionLayer = 1
    ConstantInfiltrationCapacity = 2
    ModelUnsaturatedSaturated = 3
    Horton = 4


class GroundWater(INIBasedModel):
    """
    The `[Grw]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.grw`.

    All lowercased attributes match with the [Grw] input as described in
    [UM Sec.A.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.3).
    """

    class Comments(INIBasedModel.Comments):
        groundwater: Optional[str] = Field(
            "0=No (horizontal) groundwater flow, 1=With groundwater flow",
            alias="GroundWater",
        )
        infiltrationmodel: Optional[str] = Field(
            "Infiltration method (0: No infiltration, 1: Interception layer, 2: Constant infiltration capacity, 3: model unsaturated/saturated (with grw), 4: Horton).",
            alias="Infiltrationmodel",
        )
        hinterceptionlayer: Optional[str] = Field(
            "Intercept this amount of rain (m)", alias="Hinterceptionlayer"
        )
        unifinfiltrationcapacity: Optional[str] = Field(
            "Uniform maximum infiltration capacity [m/s].",
            alias="UnifInfiltrationCapacity",
        )
        conductivity: Optional[str] = Field(
            "Non-dimensionless K conductivity   saturated (m/s), Q = K*A*i (m3/s)",
            alias="Conductivity",
        )
        h_aquiferuni: Optional[str] = Field(
            "bgrw = bl - h_aquiferuni (m), if negative, bgrw = bgrwuni.",
            alias="h_aquiferuni",
        )
        bgrwuni: Optional[str] = Field(
            "uniform level of impervious layer, only used if h_aquiferuni is negative.",
            alias="bgrwuni",
        )
        h_unsatini: Optional[str] = Field(
            "initial level groundwater is bedlevel - h_unsatini (m), if negative, sgrw = sgrwini.",
            alias="h_unsatini",
        )
        sgrwini: Optional[str] = Field(
            "Initial groundwater level, if h_unsatini < 0.", alias="sgrwini"
        )

    comments: Comments = Comments()
    _header: Literal["Grw"] = "Grw"

    groundwater: Optional[bool] = Field(False, alias="GroundWater")
    infiltrationmodel: Optional[InfiltrationMethod] = Field(
        InfiltrationMethod.NoInfiltration, alias="Infiltrationmodel"
    )
    hinterceptionlayer: Optional[float] = Field(0.0, alias="Hinterceptionlayer")
    unifinfiltrationcapacity: Optional[float] = Field(
        0.0, alias="UnifInfiltrationCapacity"
    )
    conductivity: Optional[float] = Field(0.0, alias="Conductivity")
    h_aquiferuni: Optional[float] = Field(20.0, alias="h_aquiferuni")
    bgrwuni: Optional[float] = Field(-999, alias="bgrwuni")
    h_unsatini: Optional[float] = Field(0.2, alias="h_unsatini")
    sgrwini: Optional[float] = Field(-999, alias="sgrwini")


class ProcessFluxIntegration(IntEnum):
    """
    Enum class containing the valid values for the ProcessFluxIntegration
    attribute in the [Processes][hydrolib.core.dflowfm.mdu.models.Processes] class.
    """

    WAQ = 1
    DFlowFM = 2


class Processes(INIBasedModel):
    """
    The `[Processes]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.processes`.

    All lowercased attributes match with the [Processes] input as described in
    [UM Sec.A.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.3).
    """

    class Comments(INIBasedModel.Comments):
        substancefile: Optional[str] = Field(
            "Substance file name.", alias="SubstanceFile"
        )
        additionalhistoryoutputfile: Optional[str] = Field(
            "Extra history output filename.",
            alias="AdditionalHistoryOutputFile",
        )
        statisticsfile: Optional[str] = Field(
            "Statistics definition file.",
            alias="StatisticsFile",
        )
        thetavertical: Optional[str] = Field(
            "Theta value for vertical transport of water quality substances [-].",
            alias="ThetaVertical",
        )
        dtprocesses: Optional[str] = Field(
            "Waq processes time step [s]. Must be a multiple of DtUser. If DtProcesses is negative, water quality processes are calculated with every hydrodynamic time step.",
            alias="DtProcesses",
        )
        processfluxintegration: Optional[str] = Field(
            "Process fluxes integration option (1: WAQ, 2: D-Flow FM).",
            alias="ProcessFluxIntegration",
        )
        wriwaqbot3doutput: Optional[str] = Field(
            "Write 3D water quality bottom variables (0: no, 1: yes).",
            alias="Wriwaqbot3Doutput",
        )
        volumedrythreshold: Optional[str] = Field(
            "Volume [m3] below which segments are marked as dry.",
            alias="VolumeDryThreshold",
        )
        depthdrythreshold: Optional[str] = Field(
            "Water depth [m] below which segments are marked as dry.",
            alias="DepthDryThreshold",
        )

    comments: Comments = Comments()

    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    _header: Literal["Processes"] = "Processes"

    substancefile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="SubstanceFile"
    )
    additionalhistoryoutputfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None),
        alias="AdditionalHistoryOutputFile",
    )
    statisticsfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="StatisticsFile"
    )
    thetavertical: Optional[float] = Field(0.0, alias="ThetaVertical")
    dtprocesses: Optional[float] = Field(0.0, alias="DtProcesses")
    processfluxintegration: Optional[ProcessFluxIntegration] = Field(
        ProcessFluxIntegration.WAQ, alias="ProcessFluxIntegration"
    )
    wriwaqbot3doutput: Optional[bool] = Field(False, alias="Wriwaqbot3Doutput")
    volumedrythreshold: Optional[float] = Field(1e-3, alias="VolumeDryThreshold")
    depthdrythreshold: Optional[float] = Field(1e-3, alias="DepthDryThreshold")


class ParticlesThreeDType(IntEnum):
    """
    Enum class containing the valid values for the 3Dtype
    attribute in the `Particles` class.
    """

    DepthAveraged = 0
    FreeSurface = 1


class Particles(INIBasedModel):
    """
    The `[Particles]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.particles`.

    All lowercased attributes match with the [Particles] input as described in
    [UM Sec.A.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.3).
    """

    class Comments(INIBasedModel.Comments):
        particlesfile: Optional[str] = Field(
            "Initial particle locations file (*.xyz).", alias="ParticlesFile"
        )
        particlesreleasefile: Optional[str] = Field(
            "Particles release file (*.tim, 4 column).", alias="ParticlesReleaseFile"
        )
        addtracer: Optional[str] = Field(
            "Add tracer or not (0: no, 1: yes).", alias="AddTracer"
        )
        starttime: Optional[str] = Field("Start time (if > 0) [s]", alias="StartTime")
        timestep: Optional[str] = Field(
            "Time step (if > 0) or every computational time step [s].", alias="TimeStep"
        )
        threedtype: Optional[str] = Field(
            "3D velocity type (0: depth averaged velocities, 1: free surface/top layer velocities).",
            alias="3Dtype",
        )

    comments: Comments = Comments()
    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    _header: Literal["Particles"] = "Particles"

    particlesfile: Optional[XYZModel] = Field(None, alias="ParticlesFile")
    particlesreleasefile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="ParticlesReleaseFile"
    )
    addtracer: Optional[bool] = Field(False, alias="AddTracer")
    starttime: Optional[float] = Field(0.0, alias="StartTime")
    timestep: Optional[float] = Field(0.0, alias="TimeStep")
    threedtype: Optional[ParticlesThreeDType] = Field(
        ParticlesThreeDType.DepthAveraged, alias="3Dtype"
    )


class VegetationModelNr(IntEnum):
    """
    Enum class containing the valid values for the VegetationModelNr
    attribute in the [Vegetation][hydrolib.core.dflowfm.mdu.models.Vegetation] class.
    """

    No = 0
    BaptistDFM = 1


class Vegetation(INIBasedModel):
    """
    The `[Veg]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.veg`.

    All lowercased attributes match with the [Veg] input as described in
    [UM Sec.A.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.A.3).
    """

    class Comments(INIBasedModel.Comments):
        vegetationmodelnr: Optional[str] = Field(
            "Vegetation model nr, (0: no, 1: Baptist DFM).", alias="Vegetationmodelnr"
        )
        clveg: Optional[str] = Field("Stem distance factor [-].", alias="Clveg")
        cdveg: Optional[str] = Field("Stem Cd coefficient [-].", alias="Cdveg")
        cbveg: Optional[str] = Field("Stem stiffness coefficient [-].", alias="Cbveg")
        rhoveg: Optional[str] = Field(
            "Stem Rho, if > 0, bouyant stick procedure [kg/m3].", alias="Rhoveg"
        )
        stemheightstd: Optional[str] = Field(
            "Stem height standard deviation fraction, e.g. 0.1 [-].",
            alias="Stemheightstd",
        )
        densvegminbap: Optional[str] = Field(
            "Minimum vegetation density in Baptist formula. Only in 2D. [1/m2].",
            alias="Densvegminbap",
        )

    comments: Comments = Comments()
    _header: Literal["Veg"] = "Veg"

    vegetationmodelnr: Optional[VegetationModelNr] = Field(
        VegetationModelNr.No, alias="Vegetationmodelnr"
    )
    clveg: Optional[float] = Field(0.8, alias="Clveg")
    cdveg: Optional[float] = Field(0.7, alias="Cdveg")
    cbveg: Optional[float] = Field(0.0, alias="Cbveg")
    rhoveg: Optional[float] = Field(0.0, alias="Rhoveg")
    stemheightstd: Optional[float] = Field(0.0, alias="Stemheightstd")
    densvegminbap: Optional[float] = Field(0.0, alias="Densvegminbap")


class FMModel(INIModel):
    """
    The overall FM model that contains the contents of the toplevel MDU file.

    All lowercased attributes match with the supported "[section]"s as described in
    [UM Sec.A](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#appendix.A).

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
    calibration: Optional[Calibration] = Field(None)
    grw: Optional[GroundWater] = Field(None)
    processes: Optional[Processes] = Field(None)
    particles: Optional[Particles] = Field(None)
    veg: Optional[Vegetation] = Field(None)

    serializer_config: INISerializerConfig = INISerializerConfig(
        skip_empty_properties=False
    )

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

    @classmethod
    def _get_relative_mode_from_data(cls, data: Dict[str, Any]) -> ResolveRelativeMode:
        """Gets the ResolveRelativeMode of this FileModel based on the provided data.

        The ResolveRelativeMode of the FMModel is determined by the
        'pathsRelativeToParent' property of the 'General' category.

        Args:
            data (Dict[str, Any]):
                The unvalidated/parsed data which is fed to the pydantic base model,
                used to determine the ResolveRelativeMode.

        Returns:
            ResolveRelativeMode: The ResolveRelativeMode of this FileModel
        """
        if not (general := data.get("general", None)):
            return ResolveRelativeMode.ToParent
        if not (relative_to_parent := general.get("pathsrelativetoparent", None)):
            return ResolveRelativeMode.ToParent

        if relative_to_parent == "0":
            return ResolveRelativeMode.ToAnchor
        else:
            return ResolveRelativeMode.ToParent
