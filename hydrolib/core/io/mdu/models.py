from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Field

from hydrolib.core.basemodel import (
    DiskOnlyFileModel,
    FileModel,
    ResolveRelativeMode,
    validator_set_default_disk_only_file_model_when_none,
)
from hydrolib.core.io.crosssection.models import CrossDefModel, CrossLocModel
from hydrolib.core.io.ext.models import ExtModel
from hydrolib.core.io.friction.models import FrictionModel
from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.serializer import SerializerConfig, write_ini
from hydrolib.core.io.ini.util import get_split_string_on_delimiter_validator
from hydrolib.core.io.inifield.models import IniFieldModel
from hydrolib.core.io.net.models import NetworkModel
from hydrolib.core.io.obs.models import ObservationPointModel
from hydrolib.core.io.polyfile.models import PolyFile
from hydrolib.core.io.storagenode.models import StorageNodeModel
from hydrolib.core.io.structure.models import StructureModel
from hydrolib.core.io.xyz.models import XYZModel


class AutoStartOption(IntEnum):
    """
    Enum class containing the valid values for the AutoStart
    attribute in the [General][hydrolib.core.io.mdu.models.General] class.
    """

    no = 0
    autostart = 1
    autostartstop = 2


class General(INIGeneral):
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

    comments: Comments = Comments()
    _header: Literal["General"] = "General"
    program: str = Field("D-Flow FM", alias="program")
    version: str = Field("1.2.94.66079M", alias="version")
    filetype: Literal["modelDef"] = Field("modelDef", alias="fileType")
    fileversion: str = Field("1.09", alias="fileVersion")
    autostart: Optional[AutoStartOption] = Field(AutoStartOption.no, alias="autoStart")
    pathsrelativetoparent: bool = Field(False, alias="pathsRelativeToParent")


class Numerics(INIBasedModel):
    """
    The `[Numerics]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.numerics`.

    All lowercased attributes match with the [Numerics] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        cflmax: Optional[str] = Field("Maximum Courant nr.", alias="cflMax")
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
            "Solver type, 4 = sobekGS + Saadilud (default sequential), 6 = PETSc (default parallel), 7= CG+MILU (parallel).",
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
            "flow width = flow width*FixedWeirContraction.",
            alias="fixedWeirContraction",
        )
        izbndpos: Optional[str] = Field(
            "Position of z boundary, 0=mirroring of closest cell (as in Delft3D-FLOW), 1=on net boundary.",
            alias="izBndPos",
        )
        tlfsmo: Optional[str] = Field(
            "Fourier smoothing time on water level boundaries [s].", alias="tlfSmo"
        )
        slopedrop2d: Optional[str] = Field(
            "Apply droplosses only if local bottom slope > Slopedrop2D, <=0 =no droplosses.",
            alias="slopeDrop2D",
        )
        drop1d: Optional[str] = Field(
            "Limit the downstream water level in the momentum equation to the downstream invert level, BOBdown(ζ∗down = max(BOBdown, ζdown)).",
            alias="drop1D",
        )
        chkadvd: Optional[str] = Field(
            "Check advection terms if depth < chkadvdp.", alias="chkAdvd"
        )
        teta0: Optional[str] = Field(
            "Theta (implicitness) of time integration, 0.5 < Theta < 1.0.",
            alias="teta0",
        )
        qhrelax: Optional[str] = Field("", alias="qhRelax")
        cstbnd: Optional[str] = Field(
            "Delft3D-FLOW type velocity treatment near boundaries for small coastal models (1) or not (0).",
            alias="cstBnd",
        )
        maxitverticalforestersal: Optional[str] = Field(
            "0 : no vertical filter, > 0 = Max nr of Forester filter iterations.",
            alias="maxitVerticalForesterSal",
        )
        maxitverticalforestertem: Optional[str] = Field(
            "0 : no vertical filter for temp, > 0 = Max nr of Forester Forester iterations.",
            alias="maxitVerticalForesterTem",
        )
        turbulencemodel: Optional[str] = Field(
            "0=no, 1 = constant, 2 = algebraic, 3 = k-epsilon, 4 = k-tau.",
            alias="turbulenceModel",
        )
        turbulenceadvection: Optional[str] = Field(
            "0=no, 3 = horizontal explicit vertical implicit.",
            alias="turbulenceAdvection",
        )
        anticreep: Optional[str] = Field(
            "Flag for AntiCreep option (0=off, 1=on).", alias="antiCreep"
        )
        maxwaterleveldiff: Optional[str] = Field(
            "Upper bound [m] on water level changes, (<= 0: no bounds). Run will abort when violated.",
            alias="maxWaterLevelDiff",
        )
        maxvelocitydiff: Optional[str] = Field(
            "Upper bound [m/s] on velocity changes, (<= 0: no bounds). Run will abort when violated.",
            alias="maxVelocityDiff",
        )
        epshu: Optional[str] = Field(
            "Threshold water depth for wetting and drying [m].", alias="epsHu"
        )

    comments: Comments = Comments()

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
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        usevolumetables: Optional[str] = Field(
            "Use volume tables for 1D grid cells (see section 8.16) (1: yes, 0 = no).",
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

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.physics`.

    All lowercased attributes match with the [Physics] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        uniffrictcoef: Optional[str] = Field(
            "Uniform friction coefficient, 0=no friction.", alias="unifFrictCoef"
        )
        uniffricttype: Optional[str] = Field(
            "0=Chezy, 1=Manning, 2=White-Colebrook, 3=White-Colebrook of WAQUA",
            alias="unifFrictType",
        )
        uniffrictcoef1d: Optional[str] = Field(
            "Uniform friction coefficient in 1D links, 0=no friction.",
            alias="unifFrictCoef1D",
        )
        uniffrictcoeflin: Optional[str] = Field(
            "Uniform linear friction coefficient (m/s), 0=no.", alias="unifFrictCoefLin"
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
            "1=Eckart, 2=UNESCO (default).", alias="idensform"
        )
        ag: Optional[str] = Field("Gravitational acceleration [m/s2].", alias="ag")
        tidalforcing: Optional[str] = Field(
            "Tidal forcing (0=no, 1=yes) (only for jsferic == 1).", alias="tidalForcing"
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
            "Include salinity, (0=no, 1=yes).", alias="salinity"
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
            "Background salinity concentration [ppt].", alias="backgroundSalinity"
        )
        temperature: Optional[str] = Field(
            "Include temperature, (0=no, 1=only transport, 5=heat flux model (5) of D3D), 3=excess model of D3D.",
            alias="temperature",
        )
        initialtemperature: Optional[str] = Field(
            "Inital temperature [◦C].", alias="initialTemperature"
        )
        backgroundwatertemperature: Optional[str] = Field(
            "Background temperature concentration [◦C].",
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
        secondaryflow: Optional[str] = Field(
            "Secondary flow (0=no, 1=yes).", alias="secondaryFlow"
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
    betaspiral: float = Field(0.0, alias="betaSpiral")


class Sediment(INIBasedModel):
    class Comments(INIBasedModel.Comments):
        sedimentmodelnr: Optional[str] = Field("", alias="Sedimentmodelnr")
        morfile: Optional[str] = Field("", alias="MorFile")
        sedfile: Optional[str] = Field("", alias="SedFile")

    comments: Comments = Comments()

    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    _header: Literal["Sediment"] = "Sediment"
    sedimentmodelnr: Optional[int] = Field(alias="Sedimentmodelnr")
    morfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="MorFile"
    )
    sedfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="SedFile"
    )


class Wind(INIBasedModel):
    """
    The `[Wind]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.wind`.

    All lowercased attributes match with the [Wind] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        icdtyp: Optional[str] = Field(
            "Wind drag types,1=const, 2=S&B 2 breakpoints, 3=S&B 3 breakpoints, 4=Charnock constant.",
            alias="icdTyp",
        )
        cdbreakpoints: Optional[str] = Field(
            "Wind drag breakpoints, e.g. 0.00063 0.00723.", alias="cdBreakpoints"
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

    comments: Comments = Comments()

    _header: Literal["Wind"] = "Wind"
    icdtyp: int = Field(2, alias="icdTyp")
    cdbreakpoints: List[float] = Field([0.00063, 0.00723], alias="cdBreakpoints")
    windspeedbreakpoints: List[float] = Field(
        [0.0, 100.0], alias="windSpeedBreakpoints"
    )
    rhoair: float = Field(1.205, alias="rhoAir")
    relativewind: float = Field(0.0, alias="relativeWind")
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
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        wavemodelnr: Optional[str] = Field(
            "# Wave model nr, 0=no, 1=fetch/depth limited hurdlestive, 2=youngverhagen, 3 = D-Waves, 4=wave group forcing",
            alias="waveModelNr",
        )
        rouwav: Optional[str] = Field(
            "Necessary to include bed shear-stress enhancement by waves. See also Delft3D-FLOW manual.",
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

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.time`.

    All lowercased attributes match with the [Time] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
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
            "Time interval [s] for updating nodal factors in astronomical boundary conditions [Dd HH:MM:SS.ZZZ].",
            alias="dtNodal",
        )
        dtmax: Optional[str] = Field("Max timestep in seconds [s].", alias="dtMax")
        dtinit: Optional[str] = Field(
            "Initial timestep in seconds [s].", alias="dtInit"
        )
        tstart: Optional[str] = Field(
            "Start time w.r.t. RefDate [TUnit].", alias="tStart"
        )
        tstop: Optional[str] = Field("Stop time w.r.t. RefDate [TUnit].", alias="tStop")
        updateroughnessinterval: Optional[str] = Field(
            "Update interval for time dependent roughness parameters [s].",
            alias="updateRoughnessInterval",
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
    tstart: float = Field(0.0, alias="tStart")
    tstop: float = Field(86400.0, alias="tStop")
    updateroughnessinterval: float = Field(86400.0, alias="updateRoughnessInterval")


class Restart(INIBasedModel):
    """
    The `[Restart]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.restart`.

    All lowercased attributes match with the [Restart] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
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
    restartdatetime: Optional[str] = Field(None, alias="restartDateTime")


class ExternalForcing(INIBasedModel):
    """
    The `[External Forcing]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.external_forcing`.

    All lowercased attributes match with the [External Forcing] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        extforcefile: Optional[str] = Field(
            "Old format for external forcings file *.ext, link with tim/cmp-format boundary conditions specification.",
            alias="extForceFile",
        )
        extforcefilenew: Optional[str] = Field(
            "New format for external forcings file *.ext, link with bcformat boundary conditions specification. See section C.5.2.",
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
    extforcefile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="extForceFile"
    )
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
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        interceptionmodel: Optional[str] = Field(
            "Interception model (0: none, 1: on, via layer thickness). See Section 13.3.",
            alias="interceptionModel",
        )

    comments: Comments = Comments()

    _header: Literal["Hydrology"] = "Hydrology"
    interceptionmodel: bool = Field(False, alias="interceptionModel")


class Trachytopes(INIBasedModel):
    """
    The `[Trachytopes]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.trachytopes`.

    All lowercased attributes match with the [Trachytopes] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
    """

    class Comments(INIBasedModel.Comments):
        trtrou: Optional[str] = Field(
            "Flag for trachytopes (Y=on, N=off).", alias="trtRou"
        )  # TODO bool
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

    comments: Comments = Comments()

    _header: Literal["Trachytopes"] = "Trachytopes"
    trtrou: str = Field("N", alias="trtRou")  # TODO bool
    trtdef: Optional[Path] = Field(None, alias="trtDef")
    trtl: Optional[Path] = Field(None, alias="trtL")
    dttrt: float = Field(60.0, alias="dtTrt")


class Output(INIBasedModel):
    """
    The `[Output]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.output`.

    All lowercased attributes match with the [Output] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
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
            "Space separated list of files, containing information about observation points. See section F.2.2.",
            alias="obsFile",
        )
        crsfile: Optional[str] = Field(
            "Space separated list of files, containing information about observation cross sections. See section F.2.4.",
            alias="crsFile",
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
        wrihis_lateral: Optional[str] = Field(
            "Write lateral datato his file, (1: yes, 0: no).", alias="wrihis_lateral"
        )
        wrihis_velocity: Optional[str] = Field(
            "Write velocity magnitude in observation point to his file, (1: yes, 0: no).",
            alias="wrihis_velocity",
        )
        wrihis_discharge: Optional[str] = Field(
            "Write discharge magnitude in observation point to his file, (1: yes, 0: no).",
            alias="wrihis_discharge",
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
            "Interval [s] between simulation statistics output.", alias="statsInterval"
        )
        timingsinterval: Optional[str] = Field(
            "Timings output interval TimingsInterval.", alias="timingsInterval"
        )
        richardsononoutput: Optional[str] = Field(
            "Write Richardson number, (1: yes, 0: no).", alias="richardsonOnOutput"
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
    outputdir: Optional[Path] = Field(None, alias="outputDir")
    waqoutputdir: Optional[Path] = Field(None, alias="waqOutputDir")
    flowgeomfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="flowGeomFile"
    )
    obsfile: Optional[List[ObservationPointModel]] = Field(None, alias="obsFile")
    crsfile: Optional[List[DiskOnlyFileModel]] = Field(None, alias="crsFile")
    hisfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="hisFile"
    )
    hisinterval: List[float] = Field([300], alias="hisInterval")
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
    statsinterval: List[float] = Field([0.0], alias="statsInterval")
    timingsinterval: List[float] = Field([0.0], alias="timingsInterval")
    richardsononoutput: bool = Field(True, alias="richardsonOnOutput")

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
    )

    def is_intermediate_link(self) -> bool:
        return True


class Geometry(INIBasedModel):
    """
    The `[Geometry]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry`.

    All lowercased attributes match with the [Geometry] input as described in
    [UM Sec.A.1](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.1).
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
            "File <*.ini> containing list of hydraulic structures. See section C.12.",
            alias="structureFile",
        )
        inifieldfile: Optional[str] = Field(
            "Initial and parameter field file <*.ini>. See section D.2.",
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
            "Location of the files with roughness data for 1D. See section C.15.",
            alias="frictFile",
        )
        crossdeffile: Optional[str] = Field(
            "Cross section definitions for all cross section shapes. See section C.16.",
            alias="crossDefFile",
        )
        crosslocfile: Optional[str] = Field(
            "Location definitions of the cross sections on a 1D network. See section C.16.",
            alias="crossLocFile",
        )
        storagenodefile: Optional[str] = Field(
            "File containing the specification of storage nodes and/or manholes to add extra storage to 1D models. See section C.17.",
            alias="storageNodeFile",
        )
        oned2dlinkfile: Optional[str] = Field(
            "File containing the custom parameterization of 1D-2D links. See section C.18.",
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
        uniformwidth1d: Optional[str] = Field("", alias="uniformWidth1D")
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
            "Non-linear 1D volumes, applicable for models with closed cross sections. 1=treat closed sections as partially open by using a Preissmann slot, 2=Nested Newton approach, 3=Partial Nested Newton approach. (For a description of these methods, see (D-Flow FM TRM, 2015, Section 6.9).",
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
            "Number of vertical layers.", alias="layerType"
        )
        numtopsig: Optional[str] = Field(
            "Number of sigma-layers on top of z-layers.", alias="numTopSig"
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
    usecaching: bool = Field(False, alias="useCaching")
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
    )

    def is_intermediate_link(self) -> bool:
        return True


class Calibration(INIBasedModel):
    """
    The `[Calibration]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.calibration`.

    All lowercased attributes match with the [Calibration] input as described in
    [UM Sec.A.3](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.3).
    """

    class Comments(INIBasedModel.Comments):
        usecalibration: Optional[str] = Field(
            "Activate calibration factor friction multiplier (0: no, 1: yes).",
            alias="UseCalibration",
        )
        definitionfile: Optional[str] = Field(
            "File (*.cld) containing calibration definitions. Details in Section C.9.1.",
            alias="DefinitionFile",
        )
        areafile: Optional[str] = Field(
            "File (*.cll) containing area distribution of calibration definitions. Details in Section C.9.2.",
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
    attribute in the [Groundwater][hydrolib.core.io.mdu.models.Groundwater] class.
    """

    NoInfiltration = 0
    InterceptionLayer = 1
    ConstantInfiltrationCapacity = 2
    ModelUnsaturatedSaturated = 3
    Horton = 4


class GroundWater(INIBasedModel):
    """
    The `[Grw]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.grw`.

    All lowercased attributes match with the [Grw] input as described in
    [UM Sec.A.3](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.3).
    """

    class Comments(INIBasedModel.Comments):
        groundwater: Optional[str] = Field("", alias="GroundWater")
        infiltrationmodel: Optional[str] = Field(
            "Infiltration method (0: No infiltration, 1: Interception layer, 2: Constant infiltration capacity, 3: model unsaturated/saturated (with grw), 4: Horton).",
            alias="Infiltrationmodel",
        )
        hinterceptionlayer: Optional[str] = Field("", alias="Hinterceptionlayer")
        unifinfiltrationcapacity: Optional[str] = Field(
            "Uniform maximum infiltration capacity [m/s].",
            alias="UnifInfiltrationCapacity",
        )
        conductivity: Optional[str] = Field("", alias="Conductivity")
        h_aquiferuni: Optional[str] = Field("", alias="h_aquiferuni")
        bgrwuni: Optional[str] = Field("", alias="bgrwuni")
        h_unsatini: Optional[str] = Field("", alias="h_unsatini")
        sgrwini: Optional[str] = Field("", alias="sgrwini")

    comments: Comments = Comments()
    _header: Literal["Grw"] = "Grw"

    groundwater: Optional[bool] = Field(False, alias="GroundWater")
    infiltrationmodel: Optional[InfiltrationMethod] = Field(
        InfiltrationMethod.NoInfiltration, alias="Infiltrationmodel"
    )
    hinterceptionlayer: Optional[float] = Field(None, alias="Hinterceptionlayer")
    unifinfiltrationcapacity: Optional[float] = Field(
        0.0, alias="UnifInfiltrationCapacity"
    )
    conductivity: Optional[float] = Field(0.0, alias="Conductivity")
    h_aquiferuni: Optional[float] = Field(20.0, alias="h_aquiferuni")
    bgrwuni: Optional[float] = Field(None, alias="bgrwuni")
    h_unsatini: Optional[float] = Field(0.2, alias="h_unsatini")
    sgrwini: Optional[float] = Field(None, alias="sgrwini")


class ProcessFluxIntegration(IntEnum):
    """
    Enum class containing the valid values for the ProcessFluxIntegration
    attribute in the [Processes][hydrolib.core.io.mdu.models.Processes] class.
    """

    WAQ = 1
    DFlowFM = 2


class Processes(INIBasedModel):
    """
    The `[Processes]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.processes`.

    All lowercased attributes match with the [Processes] input as described in
    [UM Sec.A.3](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.3).
    """

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
    dtmassbalance: Optional[float] = Field(0.0, alias="DtMassBalance")
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

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.particles`.

    All lowercased attributes match with the [Particles] input as described in
    [UM Sec.A.3](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.3).
    """

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
    attribute in the [Vegetation][hydrolib.core.io.mdu.models.Vegetation] class.
    """

    No = 0
    BaptistDFM = 1


class Vegetation(INIBasedModel):
    """
    The `[Veg]` section in an MDU file.

    This model is typically referenced under [FMModel][hydrolib.core.io.mdu.models.FMModel]`.veg`.

    All lowercased attributes match with the [Veg] input as described in
    [UM Sec.A.3](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.A.3).
    """

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
    [UM Sec.A](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#appendix.A).

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

    def _serialize(self, _: dict) -> None:
        config = SerializerConfig(skip_empty_properties=False)
        write_ini(self._resolved_filepath, self._to_document(), config=config)
