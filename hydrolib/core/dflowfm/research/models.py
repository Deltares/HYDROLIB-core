from typing import Optional, Literal

from pydantic.v1 import Field

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm import Geometry, FMModel, General, Numerics
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


class ResearchNumerics(Numerics):
    class Comments(Numerics.Comments):
        faclaxturb: Optional[str] = Field(
            "Default: 0=TurKin0 from links, 1.0=from nodes. 0.5=fityfifty.",
            alias="faclaxturb",
        )
        jafaclaxturbtyp: Optional[str] = Field(
            "Vertical distr of facLaxturb, 1=: (sigm<0.5=0.0 sigm>0.75=1.0 linear in between), 2:=1.0 for whole column.",
            alias="jafaclaxturbtyp",
        )
        locsaltmin: Optional[str] = Field(
            "Minimum salinity for case of lock exchange.",
            alias="locsaltmin",
        )
        lincontin: Optional[str] = Field(
            "Default 0; Set to 1 for linearizing d(Hu)/dx; link to AdvecType.",
            alias="lincontin",
        )
        cfexphormom: Optional[str] = Field(
            "Exponent for including (1-CFL) in HO term horizontal mom.",
            alias="cfexphormom",
        )
        jbasqbnddownwindhs: Optional[str] = Field(
            "Water depth scheme at discharge boundaries (0: original hu, 1: downwind hs).",
            alias="jbasqbnddownwindhs",
        )
        coriohhtrsh: Optional[str] = Field(
            "0=default=no safety in hu/hus weightings, only for Newcorio=1.",
            alias="coriohhtrsh"
        )
        limtypw: Optional[str] = Field(
            "Limiter type for wave action transport (0: none, 1: minmod, 2: van Leer, 3: Koren, 4: monotone central).",
            alias="limtypw"
        )
        huweirregular: Optional[str] = Field(
            "For villemonte and Tabellenboek, regular hu below Huweirregular.",
            alias="huweirregular"
        )
        structurelayersactive: Optional[str] = Field(
            "0=structure flow through all layers, 1=structure flow only through open layers.",
            alias="structureLayersActive"
        )
        corioadamsbashfordfac: Optional[str] = Field(
            "0.5	0=No, 0.5d0=AdamsBashford, only for Newcorio=1.",
            alias="corioadamsbashfordfac"
        )
        vertadvtypsal: Optional[str] = Field(
            "Vertical advection type for salinity (0: none, 1: upwind explicit, 2: central explicit, 3: upwind implicit, 4: central implicit, 5: central implicit but upwind for neg. stratif., 6: higher order explicit, no Forester).",
            alias="vertadvtypsal"
        )
        baorgfracmin: Optional[str] = Field(
            "Cell area = max(orgcellarea*Baorgfracmin, cutcell area)",
            alias="baorgfracmin"
        )
        epstke: Optional[str] = Field(
            "TKE=max(TKE, EpsTKE), default=1d-32",
            alias="epstke"
        )
        jadrhodz: Optional[str] = Field(
            "1:central org, 2:centralnew, 3:upw cell, 4:most stratf. cell, 5:least stratf. cell.",
            alias="jadrhodz"
        )
        logprofkepsbndin: Optional[str] = Field(
            "Inflow: 0=0 keps, 1 = log keps inflow, 2 = log keps in and outflow.",
            alias="logprofkepsbndin"
        )
        epshstem: Optional[str] = Field(
            "Only compute heatflx + evap if depth > epshstem.",
            alias="epshstem"
        )
        newcorio: Optional[str] = Field(
            "0=prior to 27-11-2019, 1=no normal forcing on open bnds, plus 12 variants.",
            alias="newcorio"
        )
        diffusiononbnd: Optional[str] = Field(
            "On open boundaries, 0 switches off horizontal diffusion Default = 1.",
            alias="diffusiononbnd"
        )
        barrieradvection: Optional[str] = Field(
            "1 = no correction, 2 = advection correction.",
            alias="barrieradvection"
        )
        rhointerfaces: Optional[str] = Field(
            "Evaluate rho at interfaces, 0=org at centers, 1=at interfaces.",
            alias="rhointerfaces"
        )
        logprofatubndin: Optional[str] = Field(
            "ubnds inflow: 0=uniform U1, 1 = log U1, 2 = user3D.",
            alias="logprofatubndin"
        )
        horadvtypzlayer: Optional[str] = Field(
            "Horizontal advection treatment of z-layers (1: default, 2: sigma-like).",
            alias="horadvtypzlayer"
        )
        chkdifd: Optional[str] = Field(
            "Check diffusion terms if depth < chkdifd, only if jatransportautotimestepdiff==1.",
            alias="chkdifd"
        )
        lateral_fixedweir_umin: Optional[str] = Field(
            "Minimal velocity treshold for weir losses in iterative lateral 1d2d weir coupling.",
            alias="lateral_fixedweir_umin"
        )
        fixedweirfrictscheme: Optional[str] = Field(
            "Fixed weir friction scheme (0: friction based on hu, 1: friction based on subgrid weir friction scheme).",
            alias="fixedWeirFrictScheme"
        )
        icoriolistype: Optional[str] = Field(
            "0=No, 5=default, 3, 4 no weights, 5-10 Kleptsova hu/hs, 25-30 Ham hs/hu, odd: 2D hs/hu, even: hsk/huk.",
            alias="icoriolistype"
        )
        zwsbtol: Optional[str] = Field(
            "Tolerance for zws(kb-1) at bed.",
            alias="zwsbtol"
        )
        cfexphu: Optional[str] = Field(
            "Exp for including (1-CFL) in sethu.",
            alias="cfexphu"
        )
        drop3d: Optional[str] = Field(
            "Apply droplosses in 3D if z upwind below bob + 2/3 hu*drop3D.",
            alias="drop3d"
        )
        zlayercenterbedvel: Optional[str] = Field(
            "Reconstruction of center velocity at half closed bedcells (0=no, 1: copy bed link velocities).",
            alias="zlayercenterbedvel"
        )
        cffacver: Optional[str] = Field(
            "Factor for including (1-CFL) in HO term vertical (0d0: no, 1d0: yes).",
            alias="cffacver"
        )
        eddyviscositybedfacmax: Optional[str] = Field(
            "Limit eddy viscosity at bed.",
            alias="eddyviscositybedfacmax"
        )
        epseps: Optional[str] = Field(
            "EPS=max(EPS, EpsEPS), default=1d-32, (or TAU).",
            alias="epseps"
        )
        lateral_fixedweir_umin_method: Optional[str] = Field(
            "Method for minimal velocity treshold for weir losses in iterative lateral 1d2d weir coupling.",
            alias="lateral_fixedweir_umin_method"
        )
        lateral_fixedweir_minimal_1d2d_embankment: Optional[str] = Field(
            "Minimal crest height of 1D2D SOBEK-DFM embankments.",
            alias="lateral_fixedweir_minimal_1d2d_embankment"
        )
        testfixedweirs: Optional[str] = Field(
            "Test for fixed weir algoritms (0 = Sieben2010, 1 = Sieben2007 ).",
            alias="testFixedWeirs"
        )
        jposhchk: Optional[str] = Field(
            "Check for positive waterdepth (0: no, 1: 0.7dts, just redo, 2: 1.0dts, close all links, 3: 0.7dts, close all links, 4: 1.0dts, reduce au, 5: 0.7dts, reduce au, 6: 1.0dts, close outflowing links, 7: 0.7*dts, close outflowing link.",
            alias="jposhchk"
        )
        cfconhormom: Optional[str] = Field(
            "Constant for including (1-CFL) in HO term horizontal mom.",
            alias="jposhchk"
        )
        cffachormom: Optional[str] = Field(
            "Factor for including (1-CFL) in HO term horizontal mom (0d0: no, 1d0: yes).",
            alias="cffachormom"
        )
        trsh_u1lb: Optional[str] = Field(
            "2D bedfriction in 3D below this threshold (m).",
            alias="trsh_u1lb"
        )
        corioconstant: Optional[str] = Field(
            "0=default, 1=Coriolis constant in sferic models anyway, 2=beta plane, both in cart. and spher. coord.",
            alias="corioconstant"
        )
        jaupwindsrc: Optional[str] = Field(
            "1st-order upwind advection at sources/sinks (1) or higher-order (0).",
            alias="jaupwindsrc"
        )
        locsaltlev: Optional[str] = Field(
            "Salinity level for case of lock exchange.",
            alias="locsaltlev"
        )
        subsuplupdates1: Optional[str] = Field(
            "Update water levels (S1) due to subsidence / uplift.",
            alias="subsuplupdates1"
        )
        linkdriedmx: Optional[str] = Field(
            "Nr of Au reduction steps after having dried.",
            alias="linkdriedmx"
        )
        maxitpresdens: Optional[str] = Field(
            "Max nr of iterations in pressure-density coupling, only used if idensform > 10.",
            alias="maxItPresDens",
        )
        lateral_fixedweir_relax: Optional[str] = Field(
            "Relaxation factor for iterative lateral 1d2d weir coupling algorithm.",
            alias="lateral_fixedweir_relax",
        )
        numlimdt_baorg: Optional[str] = Field(
            "If previous numlimdt > Numlimdt_baorg keep original cell area ba in cutcell.",
            alias="numlimdt_baorg",
        )
        locsaltmax: Optional[str] = Field(
            "Maximum salinity for case of lock exchange.",
            alias="locsaltmax",
        )
        cffachu: Optional[str] = Field(
            "Factor for including (1-CFL) in sethu (0d0: no, 1d0: yes).",
            alias="cffachu",
        )
        jasfer3d: Optional[str] = Field(
            "Corrections for spherical coordinates.",
            alias="jasfer3d",
        )

    comments: Comments = Comments()

    faclaxturb: Optional[float] = Field(None, alias="faclaxturb")
    jafaclaxturbtyp: Optional[int] = Field(None, alias="jafaclaxturbtyp")
    locsaltmin: Optional[float] = Field(None, alias="locsaltmin")
    lincontin: Optional[int] = Field(None, alias="lincontin")
    cfexphormom: Optional[float] = Field(None, alias="cfexphormom")
    jbasqbnddownwindhs: Optional[int] = Field(None, alias="jbasqbnddownwindhs")
    coriohhtrsh: Optional[float] = Field(None, alias="coriohhtrsh")
    limtypw: Optional[int] = Field(None, alias="limtypw")
    huweirregular: Optional[float] = Field(None, alias="huweirregular")
    structurelayersactive: Optional[int] = Field(None, alias="structureLayersActive")
    corioadamsbashfordfac: Optional[float] = Field(None, alias="corioadamsbashfordfac")
    vertadvtypsal: Optional[int] = Field(None, alias="vertadvtypsal")
    baorgfracmin: Optional[float] = Field(None, alias="baorgfracmin")
    epstke: Optional[float] = Field(None, alias="epstke")
    jadrhodz: Optional[int] = Field(None, alias="jadrhodz")
    logprofkepsbndin: Optional[int] = Field(None, alias="logprofkepsbndin")
    epshstem: Optional[float] = Field(None, alias="epshstem")
    newcorio: Optional[bool] = Field(None, alias="newcorio")
    diffusiononbnd: Optional[bool] = Field(None, alias="diffusiononbnd")
    barrieradvection: Optional[int] = Field(None, alias="barrieradvection")
    rhointerfaces: Optional[int] = Field(None, alias="rhointerfaces")
    logprofatubndin: Optional[int] = Field(None, alias="logprofatubndin")
    horadvtypzlayer: Optional[int] = Field(None, alias="horadvtypzlayer")
    chkdifd: Optional[float] = Field(None, alias="chkdifd")
    lateral_fixedweir_umin: Optional[float] = Field(None, alias="lateral_fixedweir_umin")
    fixedweirfrictscheme: Optional[int] = Field(None, alias="fixedWeirFrictScheme")
    icoriolistype: Optional[int] = Field(None, alias="icoriolistype")
    zwsbtol: Optional[float] = Field(None, alias="zwsbtol")
    cfexphu: Optional[float] = Field(None, alias="cfexphu")
    drop3d: Optional[float] = Field(None, alias="drop3d")
    zlayercenterbedvel: Optional[int] = Field(None, alias="zlayercenterbedvel")
    cffacver: Optional[float] = Field(None, alias="cffacver")
    eddyviscositybedfacmax: Optional[float] = Field(None, alias="eddyviscositybedfacmax")
    epseps: Optional[float] = Field(None, alias="epseps")
    lateral_fixedweir_umin_method: Optional[int] = Field(None, alias="lateral_fixedweir_umin_method")
    lateral_fixedweir_minimal_1d2d_embankment: Optional[float] = Field(None, alias="lateral_fixedweir_minimal_1d2d_embankment")
    testfixedweirs: Optional[int] = Field(None, alias="testFixedWeirs")
    jposhchk: Optional[int] = Field(None, alias="jposhchk")
    cfconhormom: Optional[float] = Field(None, alias="cfconhormom")
    cffachormom: Optional[float] = Field(None, alias="cffachormom")
    trsh_u1lb: Optional[float] = Field(None, alias="trsh_u1lb")
    corioconstant: Optional[int] = Field(None, alias="corioconstant")
    jaupwindsrc: Optional[int] = Field(None, alias="jaupwindsrc")
    locsaltlev: Optional[float] = Field(None, alias="locsaltlev")
    subsuplupdates1: Optional[bool] = Field(None, alias="subsuplupdates1")
    linkdriedmx: Optional[int] = Field(None, alias="linkdriedmx")
    maxitpresdens: Optional[int] = Field(None, alias="maxItPresDens")
    lateral_fixedweir_relax: Optional[float] = Field(None, alias="lateral_fixedweir_relax")
    numlimdt_baorg: Optional[int] = Field(None, alias="numlimdt_baorg")
    locsaltmax: Optional[float] = Field(None, alias="locsaltmax")
    cffachu: Optional[float] = Field(None, alias="cffachu")
    jasfer3d: Optional[bool] = Field(None, alias="jasfer3d")


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

