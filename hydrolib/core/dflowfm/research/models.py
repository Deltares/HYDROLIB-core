from typing import List, Literal, Optional

from pydantic.v1 import Field

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm import (
    FMModel,
    General,
    Geometry,
    Numerics,
    Output,
    Physics,
    PolyFile,
    Processes,
    Restart,
    Sediment,
    Time,
    Trachytopes,
    Waves,
    Wind,
)
from hydrolib.core.dflowfm.ini.models import INIBasedModel
from hydrolib.core.dflowfm.ini.util import get_split_string_on_delimiter_validator

DEPRECATED_VARIABLE = "Deprecated variable."
DEPRECATED_KEYWORD = "Deprecated keyword."


class ResearchGeneral(General):
    """An extended [general] section that includes highly experimental research keywords."""

    class Comments(General.Comments):
        research_modelspecific: Optional[str] = Field(
            "Optional 'model specific ID', to enable certain custom runtime function calls (instead of via MDU name).",
            alias="modelspecific",
        )
        research_inputspecific: Optional[str] = Field(
            "Use of hardcoded specific inputs, shall not be used by users (0: no, 1: yes).",
            alias="inputspecific",
        )

    comments: Comments = Comments()

    research_modelspecific: Optional[str] = Field(None, alias="modelspecific")
    research_inputspecific: Optional[bool] = Field(None, alias="inputspecific")


class ResearchGeometry(Geometry):
    """An extended [geometry] section that includes highly experimental research keywords."""

    class Comments(Geometry.Comments):
        research_toplayminthick: Optional[str] = Field(
            "Minimum top layer thickness(m), only for Z-layers.",
            alias="toplayminthick",
        )
        research_helmert: Optional[str] = Field(
            "Use Helmert (0: no, 1: yes).",
            alias="helmert",
        )
        research_waterdepthini1d: Optional[str] = Field(
            "Initial waterdepth in 1D.",
            alias="waterdepthini1d",
        )
        research_zlayeratubybob: Optional[str] = Field(
            "Lowest connected cells governed by bob instead of by bL L/R.",
            alias="zlayeratubybob",
        )
        research_shipdeffile: Optional[str] = Field(
            "File *.shd containing ship definitions.",
            alias="shipdeffile",
        )
        research_stripmesh: Optional[str] = Field(
            "Strip unused nodes and links from the mesh after clipping (1: strip, 0: do not strip).",
            alias="stripmesh",
        )
        research_bedwavelength: Optional[str] = Field(
            "Bed testcases.",
            alias="bedwavelength",
        )
        research_removesmalllinkstrsh: Optional[str] = Field(
            "0.1	0-1, 0= no removes.",
            alias="removesmalllinkstrsh",
        )
        research_createlinks1d2d: Optional[str] = Field(
            "Ruecksichtslos create links between 1D nodes and 2D cells when initializing model (1: yes, 0: no).",
            alias="createlinks1d2d",
        )
        research_bedwaveamplitude: Optional[str] = Field(
            "Bed testcases.",
            alias="bedwaveamplitude",
        )
        research_uniformhu: Optional[str] = Field(
            "Waterdepth in rigid-lid-like solution.",
            alias="uniformhu",
        )
        research_tsigma: Optional[str] = Field(
            "Sigma Adaptation period for Layertype==4 (s).",
            alias="tsigma",
        )
        research_dpuopt: Optional[str] = Field(
            "Bed level interpolation at velocity point in case of tile approach bed level: 1 = max (default); 2 = mean.",
            alias="dpuopt",
        )
        research_ihuzcsig: Optional[str] = Field(
            "If keepzlayeringatbed>=2 : 1,2,3=av,mx,mn of Leftsig,Rightsig,4=uniform'",
            alias="ihuzcsig",
        )
        research_ihuz: Optional[str] = Field(
            "ihuz",
            alias="ihuz",
        )
        research_cosphiutrsh: Optional[str] = Field(
            "0-1, 1= no bad orthos.",
            alias="cosphiutrsh",
        )
        research_cutcelllist: Optional[str] = Field(
            "File with names of cutcell polygons, e.g. cutcellpolygons.lst.",
            alias="cutcelllist",
        )
        research_uniformtyp1d: Optional[str] = Field(
            "Uniform type for channel profiles not specified by profloc.",
            alias="uniformtyp1d",
        )
        research_oned2dinternallinktype: Optional[str] = Field(
            "Link treatment method for type-3 internal links.",
            alias="oned2dinternallinktype",
        )
        research_orgfloorlevtoplaydef: Optional[str] = Field(
            "Keep original definition of Floor level of top layer.",
            alias="orgfloorlevtoplaydef",
        )
        research_pipefile: Optional[str] = Field(
            "File *.pliz containing pipe-based 'culverts'.",
            alias="pipefile",
        )
        research_groundlayerthickness: Optional[str] = Field(
            "Only in pipes: groundlayer thickness (m).",
            alias="groundlayerthickness",
        )
        research_extrbl: Optional[str] = Field(
            "Extrapolation of bed level at boundaries according to the slope: 0 = no extrapolation (default); 1 = extrapolate.",
            alias="extrbl",
        )
        research_keepzlay1bedvol: Optional[str] = Field(
            "Correct volumes when keepzlayeringatbed=1 (0: too large bedcell volumes, 1: correct bedcell volumes).",
            alias="keepzlay1bedvol",
        )
        research_stretchcoef: Optional[str] = Field(
            "Layers thickness percentage",
            alias="stretchcoef",
        )

    comments: Comments = Comments()

    research_toplayminthick: Optional[float] = Field(None, alias="toplayminthick")
    research_helmert: Optional[bool] = Field(None, alias="helmert")
    research_waterdepthini1d: Optional[float] = Field(None, alias="waterdepthini1d")
    research_zlayeratubybob: Optional[int] = Field(None, alias="zlayeratubybob")
    research_shipdeffile: Optional[DiskOnlyFileModel] = Field(None, alias="shipdeffile")
    research_stripmesh: Optional[bool] = Field(None, alias="stripmesh")
    research_bedwavelength: Optional[float] = Field(None, alias="bedwavelength")
    research_removesmalllinkstrsh: Optional[float] = Field(
        None, alias="removesmalllinkstrsh"
    )
    research_createlinks1d2d: Optional[bool] = Field(None, alias="createlinks1d2d")
    research_bedwaveamplitude: Optional[float] = Field(None, alias="bedwaveamplitude")
    research_uniformhu: Optional[float] = Field(None, alias="uniformhu")
    research_tsigma: Optional[float] = Field(None, alias="tsigma")
    research_dpuopt: Optional[int] = Field(None, alias="dpuopt")
    research_ihuzcsig: Optional[int] = Field(None, alias="ihuzcsig")
    research_ihuz: Optional[int] = Field(None, alias="ihuz")
    research_cosphiutrsh: Optional[float] = Field(None, alias="cosphiutrsh")
    research_cutcelllist: Optional[DiskOnlyFileModel] = Field(None, alias="cutcelllist")
    research_uniformtyp1d: Optional[int] = Field(None, alias="uniformtyp1d")
    research_oned2dinternallinktype: Optional[int] = Field(
        None, alias="oned2dinternallinktype"
    )
    research_orgfloorlevtoplaydef: Optional[bool] = Field(
        None, alias="orgfloorlevtoplaydef"
    )
    research_pipefile: Optional[DiskOnlyFileModel] = Field(None, alias="pipefile")
    research_groundlayerthickness: Optional[float] = Field(
        None, alias="groundlayerthickness"
    )
    research_extrbl: Optional[bool] = Field(None, alias="extrbl")
    research_keepzlay1bedvol: Optional[bool] = Field(None, alias="keepzlay1bedvol")
    research_stretchcoef: Optional[str] = Field(None, alias="stretchcoef")


class ResearchNumerics(Numerics):
    """An extended [numerics] section that includes highly experimental research keywords."""

    class Comments(Numerics.Comments):
        research_faclaxturb: Optional[str] = Field(
            "Default: 0=TurKin0 from links, 1.0=from nodes. 0.5=fityfifty.",
            alias="faclaxturb",
        )
        research_jafaclaxturbtyp: Optional[str] = Field(
            "Vertical distr of facLaxturb, 1=: (sigm<0.5=0.0 sigm>0.75=1.0 linear in between), 2:=1.0 for whole column.",
            alias="jafaclaxturbtyp",
        )
        research_locsaltmin: Optional[str] = Field(
            "Minimum salinity for case of lock exchange.",
            alias="locsaltmin",
        )
        research_lincontin: Optional[str] = Field(
            "Default 0; Set to 1 for linearizing d(Hu)/dx; link to AdvecType.",
            alias="lincontin",
        )
        research_cfexphormom: Optional[str] = Field(
            "Exponent for including (1-CFL) in HO term horizontal mom.",
            alias="cfexphormom",
        )
        research_jbasqbnddownwindhs: Optional[str] = Field(
            "Water depth scheme at discharge boundaries (0: original hu, 1: downwind hs).",
            alias="jbasqbnddownwindhs",
        )
        research_coriohhtrsh: Optional[str] = Field(
            "0=default=no safety in hu/hus weightings, only for Newcorio=1.",
            alias="coriohhtrsh",
        )
        research_limtypw: Optional[str] = Field(
            "Limiter type for wave action transport (0: none, 1: minmod, 2: van Leer, 3: Koren, 4: monotone central).",
            alias="limtypw",
        )
        research_huweirregular: Optional[str] = Field(
            "For villemonte and Tabellenboek, regular hu below Huweirregular.",
            alias="huweirregular",
        )
        research_structurelayersactive: Optional[str] = Field(
            "0=structure flow through all layers, 1=structure flow only through open layers.",
            alias="structurelayersactive",
        )
        research_corioadamsbashfordfac: Optional[str] = Field(
            "Adams-Bashford factor in Coriolis term (0: No/explicit, 0.5d0=Adams-Bashford), only for Newcorio=1.",
            alias="corioadamsbashfordfac",
        )
        research_baorgfracmin: Optional[str] = Field(
            "Cell area = max(orgcellarea*Baorgfracmin, cutcell area)",
            alias="baorgfracmin",
        )
        research_epstke: Optional[str] = Field(
            "TKE=max(TKE, EpsTKE), default=1d-32", alias="epstke"
        )
        research_jadrhodz: Optional[str] = Field(
            "1:central org, 2:centralnew, 3:upw cell, 4:most stratf. cell, 5:least stratf. cell.",
            alias="jadrhodz",
        )
        research_logprofkepsbndin: Optional[str] = Field(
            "Inflow: 0=0 keps, 1 = log keps inflow, 2 = log keps in and outflow.",
            alias="logprofkepsbndin",
        )
        research_epshstem: Optional[str] = Field(
            "Only compute heatflx + evap if depth > epshstem.", alias="epshstem"
        )
        research_newcorio: Optional[str] = Field(
            "0=prior to 27-11-2019, 1=no normal forcing on open bnds, plus 12 variants.",
            alias="newcorio",
        )
        research_diffusiononbnd: Optional[str] = Field(
            "On open boundaries, 0 switches off horizontal diffusion Default = 1.",
            alias="diffusiononbnd",
        )
        research_barrieradvection: Optional[str] = Field(
            "1 = no correction, 2 = advection correction.", alias="barrieradvection"
        )
        research_rhointerfaces: Optional[str] = Field(
            "Evaluate rho at interfaces, 0=org at centers, 1=at interfaces.",
            alias="rhointerfaces",
        )
        research_logprofatubndin: Optional[str] = Field(
            "ubnds inflow: 0=uniform U1, 1 = log U1, 2 = user3D.",
            alias="logprofatubndin",
        )
        research_horadvtypzlayer: Optional[str] = Field(
            "Vertical treatment of horizontal advection in z-layers (0: default, 1: N/A, 2: sigma-like).",
            alias="horadvtypzlayer",
        )
        research_chkdifd: Optional[str] = Field(
            "Check diffusion terms if depth < chkdifd, only if jatransportautotimestepdiff==1.",
            alias="chkdifd",
        )
        research_fixedweirfrictscheme: Optional[str] = Field(
            "Fixed weir friction scheme (0: friction based on hu, 1: friction based on subgrid weir friction scheme).",
            alias="fixedweirfrictscheme",
        )
        research_icoriolistype: Optional[str] = Field(
            "0=No, 5=default, 3, 4 no weights, 5-10 Kleptsova hu/hs, 25-30 Ham hs/hu, odd: 2D hs/hu, even: hsk/huk.",
            alias="icoriolistype",
        )
        research_zwsbtol: Optional[str] = Field(
            "Tolerance for zws(kb-1) at bed.", alias="zwsbtol"
        )
        research_cfexphu: Optional[str] = Field(
            "Exp for including (1-CFL) in sethu.", alias="cfexphu"
        )
        research_drop3d: Optional[str] = Field(
            "Waterdepth factor, apply droplosses in 3D if z upwind below bob + 2/3 hu*drop3D.",
            alias="drop3d",
        )
        research_zlayercenterbedvel: Optional[str] = Field(
            "Reconstruction of center velocity at half closed bedcells (0=no, 1: copy bed link velocities).",
            alias="zlayercenterbedvel",
        )
        research_cffacver: Optional[str] = Field(
            "Factor for including (1-CFL) in HO term vertical (0d0: no, 1d0: yes).",
            alias="cffacver",
        )
        research_eddyviscositybedfacmax: Optional[str] = Field(
            "Limit eddy viscosity at bed (factor 0.0-1.0 of first layer above).",
            alias="eddyviscositybedfacmax",
        )
        research_epseps: Optional[str] = Field(
            "EPS=max(EPS, EpsEPS), default=1d-32, (or TAU).", alias="epseps"
        )
        research_lateral_fixedweir_umin_method: Optional[str] = Field(
            "Method for minimal velocity treshold for weir losses in iterative lateral 1d2d weir coupling.",
            alias="lateral_fixedweir_umin_method",
        )
        research_lateral_fixedweir_minimal_1d2d_embankment: Optional[str] = Field(
            "Minimal crest height of 1D2D SOBEK-DFM embankments.",
            alias="lateral_fixedweir_minimal_1d2d_embankment",
        )
        research_testfixedweirs: Optional[str] = Field(
            "Test for fixed weir algoritms (0 = Sieben2010, 1 = Sieben2007 ).",
            alias="testfixedweirs",
        )
        research_jposhchk: Optional[str] = Field(
            "Check for positive waterdepth (0: no, 1: 0.7dts, just redo, 2: 1.0dts, close all links, 3: 0.7dts, close all links, 4: 1.0dts, reduce au, 5: 0.7dts, reduce au, 6: 1.0dts, close outflowing links, 7: 0.7*dts, close outflowing link.",
            alias="jposhchk",
        )
        research_cfconhormom: Optional[str] = Field(
            "Constant for including (1-CFL) in HO term horizontal mom.",
            alias="cfconhormom",
        )
        research_cffachormom: Optional[str] = Field(
            "Factor for including (1-CFL) in HO term horizontal mom (0d0: no, 1d0: yes).",
            alias="cffachormom",
        )
        research_trsh_u1lb: Optional[str] = Field(
            "2D bedfriction in 3D below this threshold (m).", alias="trsh_u1lb"
        )
        research_corioconstant: Optional[str] = Field(
            "0=default, 1=Coriolis constant in sferic models anyway, 2=beta plane, both in cart. and spher. coord.",
            alias="corioconstant",
        )
        research_jaupwindsrc: Optional[str] = Field(
            "1st-order upwind advection at sources/sinks (1) or higher-order (0).",
            alias="jaupwindsrc",
        )
        research_locsaltlev: Optional[str] = Field(
            "Salinity level for case of lock exchange.", alias="locsaltlev"
        )
        research_subsuplupdates1: Optional[str] = Field(
            "Update water levels (S1) due to subsidence / uplift.",
            alias="subsuplupdates1",
        )
        research_linkdriedmx: Optional[str] = Field(
            "Nr of Au reduction steps after having dried.", alias="linkdriedmx"
        )
        research_maxitpresdens: Optional[str] = Field(
            "Max nr of iterations in pressure-density coupling, only used if idensform > 10.",
            alias="maxitpresdens",
        )
        research_lateral_fixedweir_relax: Optional[str] = Field(
            "Relaxation factor for iterative lateral 1d2d weir coupling algorithm.",
            alias="lateral_fixedweir_relax",
        )
        research_numlimdt_baorg: Optional[str] = Field(
            "If previous numlimdt > Numlimdt_baorg keep original cell area ba in cutcell.",
            alias="numlimdt_baorg",
        )
        research_locsaltmax: Optional[str] = Field(
            "Maximum salinity for case of lock exchange.",
            alias="locsaltmax",
        )
        research_cffachu: Optional[str] = Field(
            "Factor for including (1-CFL) in sethu (0d0: no, 1d0: yes).",
            alias="cffachu",
        )
        research_vertadvtypmom3onbnd: Optional[str] = Field(
            "Vert. adv. u1 bnd UpwimpL: 0=follow javau , 1 = on bnd, 2= on and near bnd.",
            alias="vertadvtypmom3onbnd",
        )
        research_noderivedtypes: Optional[str] = Field(
            "0=use der. types. , 1 = less, 2 = lesser, 5 = also dealloc der. types.",
            alias="noderivedtypes",
        )

        research_jarhoxu: Optional[str] = Field(
            "Include density gradient in advection term (0: no(strongly advised), 1: yes, 2: Also in barotropic and baroclinic pressure term, 3,4: Also in vertical advection).",
            alias="jarhoxu",
        )
        research_jaorgsethu: Optional[str] = Field(
            DEPRECATED_VARIABLE,
            alias="jaorgsethu",
        )
        research_cflwavefrac: Optional[str] = Field(
            DEPRECATED_VARIABLE,
            alias="cflwavefrac",
        )
        research_jaembed1d: Optional[str] = Field(
            DEPRECATED_VARIABLE,
            alias="jaembed1d",
        )
        research_maxitverticalforester: Optional[str] = Field(
            "Forester iterations for salinity (0: no vertical filter for salinity, > 0: max nr of iterations).",
            alias="maxitverticalforester",
        )

        research_ilutype: Optional[str] = Field(
            "0: parms-default",
            alias="ilutype",
        )
        research_nlevel: Optional[str] = Field(
            "0d0: parms-default",
            alias="nlevel",
        )
        research_dtol: Optional[str] = Field(
            "0d0: parms-default",
            alias="dtol",
        )

    comments: Comments = Comments()

    research_faclaxturb: Optional[float] = Field(None, alias="faclaxturb")
    research_jafaclaxturbtyp: Optional[int] = Field(None, alias="jafaclaxturbtyp")
    research_locsaltmin: Optional[float] = Field(None, alias="locsaltmin")
    research_lincontin: Optional[int] = Field(None, alias="lincontin")
    research_cfexphormom: Optional[float] = Field(None, alias="cfexphormom")
    research_jbasqbnddownwindhs: Optional[int] = Field(None, alias="jbasqbnddownwindhs")
    research_coriohhtrsh: Optional[float] = Field(None, alias="coriohhtrsh")
    research_limtypw: Optional[int] = Field(None, alias="limtypw")
    research_huweirregular: Optional[float] = Field(None, alias="huweirregular")
    research_structurelayersactive: Optional[int] = Field(
        None, alias="structurelayersactive"
    )
    research_corioadamsbashfordfac: Optional[float] = Field(
        None, alias="corioadamsbashfordfac"
    )
    research_baorgfracmin: Optional[float] = Field(None, alias="baorgfracmin")
    research_epstke: Optional[float] = Field(None, alias="epstke")
    research_jadrhodz: Optional[int] = Field(None, alias="jadrhodz")
    research_logprofkepsbndin: Optional[int] = Field(None, alias="logprofkepsbndin")
    research_epshstem: Optional[float] = Field(None, alias="epshstem")
    research_newcorio: Optional[bool] = Field(None, alias="newcorio")
    research_diffusiononbnd: Optional[bool] = Field(None, alias="diffusiononbnd")
    research_barrieradvection: Optional[int] = Field(None, alias="barrieradvection")
    research_rhointerfaces: Optional[int] = Field(None, alias="rhointerfaces")
    research_logprofatubndin: Optional[int] = Field(None, alias="logprofatubndin")
    research_horadvtypzlayer: Optional[int] = Field(None, alias="horadvtypzlayer")
    research_chkdifd: Optional[float] = Field(None, alias="chkdifd")
    research_fixedweirfrictscheme: Optional[int] = Field(
        None, alias="fixedweirfrictscheme"
    )
    research_icoriolistype: Optional[int] = Field(None, alias="icoriolistype")
    research_zwsbtol: Optional[float] = Field(None, alias="zwsbtol")
    research_cfexphu: Optional[float] = Field(None, alias="cfexphu")
    research_drop3d: Optional[float] = Field(None, alias="drop3d")
    research_zlayercenterbedvel: Optional[bool] = Field(
        None, alias="zlayercenterbedvel"
    )
    research_cffacver: Optional[float] = Field(None, alias="cffacver")
    research_eddyviscositybedfacmax: Optional[float] = Field(
        None, alias="eddyviscositybedfacmax"
    )
    research_epseps: Optional[float] = Field(None, alias="epseps")
    research_lateral_fixedweir_umin_method: Optional[int] = Field(
        None, alias="lateral_fixedweir_umin_method"
    )
    research_lateral_fixedweir_minimal_1d2d_embankment: Optional[float] = Field(
        None, alias="lateral_fixedweir_minimal_1d2d_embankment"
    )
    research_testfixedweirs: Optional[int] = Field(None, alias="testfixedweirs")
    research_jposhchk: Optional[int] = Field(None, alias="jposhchk")
    research_cfconhormom: Optional[float] = Field(None, alias="cfconhormom")
    research_cffachormom: Optional[float] = Field(None, alias="cffachormom")
    research_trsh_u1lb: Optional[float] = Field(None, alias="trsh_u1lb")
    research_corioconstant: Optional[int] = Field(None, alias="corioconstant")
    research_jaupwindsrc: Optional[bool] = Field(None, alias="jaupwindsrc")
    research_locsaltlev: Optional[float] = Field(None, alias="locsaltlev")
    research_subsuplupdates1: Optional[bool] = Field(None, alias="subsuplupdates1")
    research_linkdriedmx: Optional[int] = Field(None, alias="linkdriedmx")
    research_maxitpresdens: Optional[int] = Field(None, alias="maxitpresdens")
    research_lateral_fixedweir_relax: Optional[float] = Field(
        None, alias="lateral_fixedweir_relax"
    )
    research_numlimdt_baorg: Optional[int] = Field(None, alias="numlimdt_baorg")
    research_locsaltmax: Optional[float] = Field(None, alias="locsaltmax")
    research_cffachu: Optional[float] = Field(None, alias="cffachu")
    research_vertadvtypmom3onbnd: Optional[int] = Field(
        None, alias="vertadvtypmom3onbnd"
    )
    research_noderivedtypes: Optional[int] = Field(None, alias="noderivedtypes")
    research_jarhoxu: Optional[int] = Field(None, alias="jarhoxu")
    research_jaorgsethu: Optional[str] = Field(None, alias="jaorgsethu")
    research_cflwavefrac: Optional[str] = Field(None, alias="cflwavefrac")
    research_jaembed1d: Optional[str] = Field(None, alias="jaembed1d")
    research_maxitverticalforester: Optional[str] = Field(
        None, alias="maxitverticalforester"
    )
    research_ilutype: Optional[str] = Field(None, alias="ilutype")
    research_nlevel: Optional[str] = Field(None, alias="nlevel")
    research_dtol: Optional[str] = Field(None, alias="dtol")


class ResearchPhysics(Physics):
    """An extended [physics] section that includes highly experimental research keywords."""

    class Comments(Physics.Comments):
        research_surftempsmofac: Optional[str] = Field(
            "Hor. Smoothing factor for surface water in heatflx comp. (0.0-1.0), 0=no.",
            alias="surftempsmofac",
        )
        research_selfattractionloading_correct_wl_with_ini: Optional[str] = Field(
            "Correct water level with initial water level in Self attraction and loading (0=no, 1=yes).",
            alias="selfattractionloading_correct_wl_with_ini",
        )
        research_nfentrainmentmomentum: Optional[str] = Field(
            "1: Switch on momentum transfer in NearField related entrainment.",
            alias="nfentrainmentmomentum",
        )
        research_uniffrictcoef1d2d: Optional[str] = Field(
            "Uniform friction coefficient in 1D links (0: no friction).",
            alias="uniffrictcoef1d2d",
        )
        research_equili: Optional[str] = Field(
            "Equilibrium spiral flow intensity (0: no, 1: yes).", alias="equili"
        )
        research_allowcoolingbelowzero: Optional[str] = Field(
            "False	0 = no, 1 = yes.", alias="allowcoolingbelowzero"
        )
        research_soiltempthick: Optional[str] = Field(
            "Use soil temperature buffer if > 0.", alias="soiltempthick"
        )
        research_selfattractionloading: Optional[str] = Field(
            "Use self attraction and loading (0: no, 1: yes, 2: only self attraction).",
            alias="selfattractionloading",
        )
        research_prandtlnumbertemperature: Optional[str] = Field(
            "Turbulent Prandtl number for temperature.",
            alias="prandtlnumbertemperature",
        )
        research_schmidtnumbersalinity: Optional[str] = Field(
            "Turbulent Schmidt number for salinity.",
            alias="schmidtnumbersalinity",
        )
        research_schmidtnumbertracer: Optional[str] = Field(
            "Turbulent Schmidt number for tracer(s).",
            alias="schmidtnumbertracer",
        )
        research_umodlin: Optional[str] = Field(
            "Linear friction umod, for ifrctyp=4,5,6.",
            alias="umodlin",
        )
        research_jadelvappos: Optional[str] = Field(
            "Only positive forced evaporation fluxes(0: no, 1: yes).",
            alias="jadelvappos",
        )
        research_uniffrictcoef1dgrlay: Optional[str] = Field(
            "Uniform ground layer friction coefficient for ocean models (m/s) (0: no friction).",
            alias="uniffrictcoef1dgrlay",
        )
        research_effectspiral: Optional[str] = Field(
            DEPRECATED_KEYWORD,
            alias="effectspiral",
        )

    comments: Comments = Comments()

    research_surftempsmofac: Optional[float] = Field(None, alias="surftempsmofac")
    research_selfattractionloading_correct_wl_with_ini: Optional[bool] = Field(
        None, alias="selfattractionloading_correct_wl_with_ini"
    )
    research_nfentrainmentmomentum: Optional[bool] = Field(
        None, alias="nfentrainmentmomentum"
    )
    research_uniffrictcoef1d2d: Optional[float] = Field(None, alias="uniffrictcoef1d2d")
    research_equili: Optional[bool] = Field(None, alias="equili")
    research_allowcoolingbelowzero: Optional[bool] = Field(
        None, alias="allowcoolingbelowzero"
    )
    research_soiltempthick: Optional[float] = Field(None, alias="soiltempthick")
    research_selfattractionloading: Optional[int] = Field(
        None, alias="selfattractionloading"
    )
    research_prandtlnumbertemperature: Optional[float] = Field(
        None, alias="prandtlnumbertemperature"
    )
    research_schmidtnumbersalinity: Optional[float] = Field(
        None, alias="schmidtnumbersalinity"
    )
    research_schmidtnumbertracer: Optional[float] = Field(
        None, alias="schmidtnumbertracer"
    )
    research_umodlin: Optional[float] = Field(None, alias="umodlin")
    research_jadelvappos: Optional[bool] = Field(None, alias="jadelvappos")
    research_uniffrictcoef1dgrlay: Optional[float] = Field(
        None, alias="uniffrictcoef1dgrlay"
    )
    research_effectspiral: Optional[float] = Field(None, alias="effectspiral")


class ResearchSediment(Sediment):
    """An extended [sediment] section that includes highly experimental research keywords."""

    class Comments(Sediment.Comments):
        research_mxgrkrone: Optional[str] = Field(
            "Highest fraction index treated by Krone.", alias="mxgrkrone"
        )
        research_seddenscoupling: Optional[str] = Field(
            "Sed rho coupling (0=no, 1=yes).", alias="seddenscoupling"
        )
        research_implicitfallvelocity: Optional[str] = Field(
            "1=Impl., 0 = Expl.", alias="implicitfallvelocity"
        )
        research_nr_of_sedfractions: Optional[str] = Field(
            "Nr of sediment fractions, (specify the next parameters for each fraction).",
            alias="nr_of_sedfractions",
        )

    comments: Comments = Comments()

    research_mxgrkrone: Optional[int] = Field(None, alias="mxgrkrone")
    research_seddenscoupling: Optional[bool] = Field(None, alias="seddenscoupling")
    research_implicitfallvelocity: Optional[int] = Field(
        None, alias="implicitfallvelocity"
    )
    research_nr_of_sedfractions: Optional[int] = Field(None, alias="nr_of_sedfractions")


class ResearchWind(Wind):
    """An extended [wind] section that includes highly experimental research keywords."""

    class Comments(Wind.Comments):
        research_windhuorzwsbased: Optional[str] = Field(
            "Wind hu or zws based, 0 = hu, 1 = zws.", alias="windhuorzwsbased"
        )
        research_varyingairdensity: Optional[str] = Field(
            "Compute air density yes/no (), 1/0, default 0.", alias="varyingairdensity"
        )
        research_wind_eachstep: Optional[str] = Field(
            "1=wind (and air pressure) each computational timestep, 0=wind (and air pressure) each usertimestep.",
            alias="wind_eachstep",
        )
        research_gapres: Optional[str] = Field(
            DEPRECATED_KEYWORD,
            alias="gapres",
        )

    comments: Comments = Comments()

    research_windhuorzwsbased: Optional[int] = Field(None, alias="windhuorzwsbased")
    research_varyingairdensity: Optional[bool] = Field(None, alias="varyingairdensity")
    research_wind_eachstep: Optional[int] = Field(None, alias="wind_eachstep")
    research_gapres: Optional[str] = Field(None, alias="gapres")


class ResearchWaves(Waves):
    """An extended [waves] section that includes highly experimental research keywords."""

    class Comments(Waves.Comments):
        research_waveswartdelwaq: Optional[str] = Field(
            "If WaveSwartDelwaq == 1 .and. Tiwaq > 0 then increase tauwave to Delwaq with 0.5rhofwuorbuorb.",
            alias="waveswartdelwaq",
        )
        research_hwavuni: Optional[str] = Field(
            "Root mean square wave height (m).", alias="hwavuni"
        )
        research_tifetchcomp: Optional[str] = Field(
            "Time interval fetch comp (s) in wavemodel 1, 2.", alias="tifetchcomp"
        )
        research_phiwavuni: Optional[str] = Field(
            "Root mean square wave direction, (deg), math convention.",
            alias="phiwavuni",
        )
        research_threedwavestreaming: Optional[str] = Field(
            "Influence of wave streaming. 0: no, 1: added to adve.",
            alias="threedwavestreaming",
        )
        research_threedwaveboundarylayer: Optional[str] = Field(
            "Boundary layer formulation. 1: Sana.", alias="threedwaveboundarylayer"
        )
        research_twavuni: Optional[str] = Field(
            "Root mean square wave period (s).", alias="twavuni"
        )
        research_uorbfac: Optional[str] = Field(
            "Orbital velocities: 0=D3D style; 1=Guza style.", alias="uorbfac"
        )
        research_threedstokesprofile: Optional[str] = Field(
            "Stokes profile. 0: no, 1:uniform over depth, 2: 2nd order Stokes theory; 3: 2, with vertical stokes gradient in adve.",
            alias="threedstokesprofile",
        )
        research_jamapsigwav: Optional[str] = Field(
            "1: sign wave height on map output; 0: hrms wave height on map output. Default=0 (legacy behaviour).",
            alias="jamapsigwav",
        )
        research_hminlw: Optional[str] = Field(
            "Cut-off depth for application of wave forces in momentum balance.",
            alias="hminlw",
        )
        research_jahissigwav: Optional[str] = Field(
            "Sign wave height on his output; 0: hrms wave height on his output. Default=1.",
            alias="jahissigwav",
        )
        research_wavenikuradse: Optional[str] = Field(
            DEPRECATED_KEYWORD,
            alias="wavenikuradse",
        )

    comments: Comments = Comments()

    research_waveswartdelwaq: Optional[bool] = Field(None, alias="waveswartdelwaq")
    research_hwavuni: Optional[float] = Field(None, alias="hwavuni")
    research_tifetchcomp: Optional[float] = Field(None, alias="tifetchcomp")
    research_phiwavuni: Optional[float] = Field(None, alias="phiwavuni")
    research_threedwavestreaming: Optional[int] = Field(
        None, alias="threedwavestreaming"
    )
    research_threedwaveboundarylayer: Optional[int] = Field(
        None, alias="threedwaveboundarylayer"
    )
    research_twavuni: Optional[float] = Field(None, alias="twavuni")
    research_uorbfac: Optional[int] = Field(None, alias="uorbfac")
    research_threedstokesprofile: Optional[int] = Field(
        None, alias="threedstokesprofile"
    )
    research_jamapsigwav: Optional[int] = Field(None, alias="jamapsigwav")
    research_hminlw: Optional[float] = Field(None, alias="hminlw")
    research_jahissigwav: Optional[int] = Field(None, alias="jahissigwav")
    research_wavenikuradse: Optional[str] = Field(None, alias="wavenikuradse")


class ResearchTime(Time):
    """An extended [time] section that includes highly experimental research keywords."""

    class Comments(Time.Comments):
        research_timestepanalysis: Optional[str] = Field(
            "Write time steps analysis file *.steps (0: no, 1: yes).",
            alias="timestepanalysis",
        )
        research_autotimestepvisc: Optional[str] = Field(
            "0 = no, 1 = yes (Time limitation based on explicit diffusive term).",
            alias="autotimestepvisc",
        )
        research_tstarttlfsmo: Optional[str] = Field(
            "Start time of smoothing of boundary conditions (Tlfsmo) w.r.t. RefDate (in TUnit).",
            alias="tstarttlfsmo",
        )

    comments: Comments = Comments()

    research_timestepanalysis: Optional[bool] = Field(None, alias="timestepanalysis")
    research_autotimestepvisc: Optional[bool] = Field(None, alias="autotimestepvisc")
    research_tstarttlfsmo: Optional[float] = Field(None, alias="tstarttlfsmo")


class ResearchRestart(Restart):
    """An extended [restart] section that includes highly experimental research keywords."""

    class Comments(Restart.Comments):
        research_rstignorebl: Optional[str] = Field(
            "Flag indicating whether bed level from restart should be ignored (0=no (default), 1=yes).",
            alias="rstignorebl",
        )

    comments: Comments = Comments()

    research_rstignorebl: Optional[bool] = Field(None, alias="rstignorebl")


class ResearchTrachytopes(Trachytopes):
    """An extended [trachytopes] section that includes highly experimental research keywords."""

    class Comments(Trachytopes.Comments):
        research_trtmth: Optional[str] = Field(
            "Area averaging method, (1=Nikuradse k based, 2=Chezy C based (parallel and serial)).",
            alias="trtmth",
        )
        research_trtmnh: Optional[str] = Field(
            "Minimum water depth for roughness computations.", alias="trtmnh"
        )
        research_trtcll: Optional[str] = Field(
            "Calibration factor file for roughness from trachytopes (see also [calibration] block).",
            alias="trtcll",
        )

    comments: Comments = Comments()

    research_trtmth: Optional[int] = Field(None, alias="trtmth")
    research_trtmnh: Optional[float] = Field(None, alias="trtmnh")
    research_trtcll: Optional[DiskOnlyFileModel] = Field(None, alias="trtcll")


class ResearchOutput(Output):
    """An extended [output] section that includes highly experimental research keywords."""

    class Comments(Output.Comments):
        research_mbalumpsourcesinks: Optional[str] = Field(
            "Lump MBA source/sink mass balance terms (1: yes, 0: no).",
            alias="mbalumpsourcesinks",
        )
        research_wrimap_nearfield: Optional[str] = Field(
            "Write near field parameters (1: yes, 0: no).", alias="wrimap_nearfield"
        )

        research_writedfminterpretedvalues: Optional[str] = Field(
            "Write DFMinterpretedvalues (1: yes, 0: no).",
            alias="writedfminterpretedvalues",
        )
        research_deleteobspointsoutsidegrid: Optional[str] = Field(
            "0 - do not delete, 1 - delete.", alias="deleteobspointsoutsidegrid"
        )
        research_mbalumpboundaries: Optional[str] = Field(
            "Lump MBA boundary mass balance terms (1: yes, 0: no).",
            alias="mbalumpboundaries",
        )
        research_waqhoraggr: Optional[str] = Field(
            "DELWAQ output horizontal aggregation file (*.dwq).", alias="waqhoraggr"
        )
        research_writedetailedtimers: Optional[str] = Field(
            "Write detailed timers output file (1: yes, 0: no).",
            alias="writedetailedtimers",
        )
        research_metadatafile: Optional[str] = Field(
            "Metadata NetCDF file with user-defined global dataset attributes (*_meta.nc).",
            alias="metadatafile",
        )
        research_mbainterval: Optional[str] = Field(
            "Mass balance area output interval (s).", alias="mbainterval"
        )
        research_wrirst_bnd: Optional[str] = Field(
            "Write waterlevel", alias="wrirst_bnd"
        )
        research_generateuuid: Optional[str] = Field(
            "Generate UUID as unique dataset identifier and include in output NetCDF files.",
            alias="generateuuid",
        )
        research_timesplitinterval: Optional[str] = Field(
            "Time splitting interval, after which a new output file is started. value+unit, e.g. '1 M', valid units: Y,M,D,h,m,s.",
            alias="timesplitinterval",
        )
        research_rugfile: Optional[str] = Field(
            "Polyline file *_rug.pli defining runup gauges.", alias="rugfile"
        )
        research_mbawritecsv: Optional[str] = Field(
            "Write mass balance area output to a csv-file (1: yes, 0: no).",
            alias="mbawritecsv",
        )
        research_mbalumpfromtomba: Optional[str] = Field(
            "Lump MBA from/to other areas mass balance terms (1: yes, 0: no).",
            alias="mbalumpfromtomba",
        )
        research_mbalumpprocesses: Optional[str] = Field(
            "Lump MBA processes mass balance terms (1: yes, 0: no).",
            alias="mbalumpprocesses",
        )
        research_waqvertaggr: Optional[str] = Field(
            "DELWAQ output vertical aggregation file (*.vag).", alias="waqvertaggr"
        )
        research_mbawritenetcdf: Optional[str] = Field(
            "Write mass balance area output to a netCDF-file (1: yes, 0: no).",
            alias="mbawritenetcdf",
        )
        research_mbawritetxt: Optional[str] = Field(
            "Write mass balance area output to a txt-file (1: yes, 0: no).",
            alias="mbawritetxt",
        )
        research_nccompression: Optional[str] = Field(
            "Whether or not (1/0) to apply compression to NetCDF output files - NOTE: only works when NcFormat = 4.",
            alias="nccompression",
        )
        research_wrimap_ice: Optional[str] = Field(
            "Write output to map file for ice cover, 0=no (default), 1=yes.",
            alias="wrimap_ice",
        )
        research_wrimap_trachytopes: Optional[str] = Field(
            "Write trachytope roughnesses to map file (1: yes, 0: no).",
            alias="wrimap_trachytopes",
        )
        research_s1incinterval: Optional[str] = Field(
            DEPRECATED_KEYWORD,
            alias="s1incinterval",
        )
        research_waqfilebase: Optional[str] = Field(
            DEPRECATED_KEYWORD,
            alias="waqfilebase",
        )
        research_snapshotdir: Optional[str] = Field(
            DEPRECATED_KEYWORD,
            alias="snapshotdir",
        )
        research_heatfluxesonoutput: Optional[str] = Field(
            DEPRECATED_KEYWORD,
            alias="heatfluxesonoutput",
        )

    comments: Comments = Comments()

    research_mbalumpsourcesinks: Optional[bool] = Field(
        None, alias="mbalumpsourcesinks"
    )
    research_wrimap_nearfield: Optional[bool] = Field(None, alias="wrimap_nearfield")
    research_writedfminterpretedvalues: Optional[bool] = Field(
        None, alias="writedfminterpretedvalues"
    )
    research_deleteobspointsoutsidegrid: Optional[bool] = Field(
        None, alias="deleteobspointsoutsidegrid"
    )
    research_mbalumpboundaries: Optional[bool] = Field(None, alias="mbalumpboundaries")
    research_waqhoraggr: Optional[DiskOnlyFileModel] = Field(None, alias="waqhoraggr")
    research_writedetailedtimers: Optional[bool] = Field(
        None, alias="writedetailedtimers"
    )
    research_metadatafile: Optional[DiskOnlyFileModel] = Field(
        None, alias="metadatafile"
    )
    research_mbainterval: Optional[float] = Field(None, alias="mbainterval")
    research_wrirst_bnd: Optional[bool] = Field(None, alias="wrirst_bnd")
    research_generateuuid: Optional[bool] = Field(None, alias="generateuuid")
    research_timesplitinterval: Optional[str] = Field(None, alias="timesplitinterval")
    research_rugfile: Optional[PolyFile] = Field(None, alias="rugfile")
    research_mbawritecsv: Optional[bool] = Field(None, alias="mbawritecsv")
    research_mbalumpfromtomba: Optional[bool] = Field(None, alias="mbalumpfromtomba")
    research_mbalumpprocesses: Optional[bool] = Field(None, alias="mbalumpprocesses")
    research_waqvertaggr: Optional[DiskOnlyFileModel] = Field(None, alias="waqvertaggr")
    research_mbawritenetcdf: Optional[bool] = Field(None, alias="mbawritenetcdf")
    research_mbawritetxt: Optional[bool] = Field(None, alias="mbawritetxt")
    research_nccompression: Optional[bool] = Field(None, alias="nccompression")
    research_wrimap_ice: Optional[bool] = Field(None, alias="wrimap_ice")
    research_wrimap_trachytopes: Optional[bool] = Field(
        None, alias="wrimap_trachytopes"
    )
    research_s1incinterval: Optional[str] = Field(None, alias="s1incinterval")
    research_waqfilebase: Optional[str] = Field(None, alias="waqfilebase")
    research_snapshotdir: Optional[str] = Field(None, alias="snapshotdir")
    research_heatfluxesonoutput: Optional[str] = Field(None, alias="heatfluxesonoutput")


class ResearchProcesses(Processes):
    """An extended [processes] section that includes highly experimental research keywords."""

    class Comments(Processes.Comments):
        research_substancedensitycoupling: Optional[str] = Field(
            "Substance rho coupling (0=no, 1=yes).", alias="substancedensitycoupling"
        )

    comments: Comments = Comments()

    research_substancedensitycoupling: Optional[bool] = Field(
        None, alias="substancedensitycoupling"
    )


class ResearchSedtrails(INIBasedModel):
    """The `[Sedtrails]` section in an MDU file."""

    class Comments(INIBasedModel.Comments):
        research_sedtrailsgrid: Optional[str] = Field(
            "Grid file for sedtrails output locations on corners.",
            alias="sedtrailsgrid",
        )
        research_sedtrailsanalysis: Optional[str] = Field(
            "Sedtrails analysis. Should be all, transport, flowvelocity or soulsby.",
            alias="sedtrailsanalysis",
        )
        research_sedtrailsinterval: Optional[str] = Field(
            "Sedtrails output times (s), interval, starttime, stoptime (s), if starttime, stoptime are left blank, use whole simulation period.",
            alias="sedtrailsinterval",
        )
        research_sedtrailsoutputfile: Optional[str] = Field(
            "Sedtrails time-avgd output file.", alias="sedtrailsoutputfile"
        )

    comments: Comments = Comments()
    _header: Literal["sedtrails"] = "sedtrails"

    research_sedtrailsgrid: Optional[DiskOnlyFileModel] = Field(
        None, alias="sedtrailsgrid"
    )
    research_sedtrailsanalysis: Optional[
        Literal["all", "transport", "flowvelocity", "soulsby"]
    ] = Field(None, alias="sedtrailsanalysis")
    research_sedtrailsinterval: Optional[List[float]] = Field(
        None, alias="sedtrailsinterval"
    )
    research_sedtrailsoutputfile: Optional[DiskOnlyFileModel] = Field(
        None, alias="sedtrailsoutputfile"
    )

    _split_to_list = get_split_string_on_delimiter_validator(
        "research_sedtrailsinterval",
    )


class ResearchFMModel(FMModel):
    """
    An extended FMModel that includes highly experimental research sections and keywords.
    """

    general: ResearchGeneral = Field(default_factory=ResearchGeneral)
    geometry: ResearchGeometry = Field(default_factory=ResearchGeometry)
    numerics: ResearchNumerics = Field(default_factory=ResearchNumerics)
    physics: ResearchPhysics = Field(default_factory=ResearchPhysics)
    sediment: ResearchSediment = Field(default_factory=ResearchSediment)
    wind: ResearchWind = Field(default_factory=ResearchWind)
    waves: Optional[ResearchWaves] = Field(None)
    time: ResearchTime = Field(default_factory=ResearchTime)
    restart: ResearchRestart = Field(default_factory=ResearchRestart)
    trachytopes: ResearchTrachytopes = Field(default_factory=ResearchTrachytopes)
    output: ResearchOutput = Field(default_factory=ResearchOutput)
    processes: Optional[ResearchProcesses] = Field(None)
    sedtrails: Optional[ResearchSedtrails] = Field(None)
