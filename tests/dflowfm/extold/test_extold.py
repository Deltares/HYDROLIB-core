import copy
from pathlib import Path
from typing import List

import pytest

from hydrolib.core.basemodel import (
    DiskOnlyFileModel,
    ModelSaveSettings,
    SerializerConfig,
)
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.extold.models import (
    HEADER,
    INITIAL_CONDITION_QUANTITIES_VALID_PREFIXES,
    ExtOldFileType,
    ExtOldForcing,
    ExtOldInitialConditionQuantity,
    ExtOldMethod,
    ExtOldModel,
    ExtOldParametersQuantity,
    ExtOldQuantity,
    ExtOldSourcesSinks,
)
from hydrolib.core.dflowfm.extold.parser import Parser
from hydrolib.core.dflowfm.extold.serializer import Serializer
from tests.utils import assert_files_equal, create_temp_file_from_lines, get_temp_file

quantities_with_prefixes = copy.deepcopy(INITIAL_CONDITION_QUANTITIES_VALID_PREFIXES)
quantities_with_prefixes = [
    f"{quantity}-suffix" for quantity in quantities_with_prefixes
]
EXP_HEADER = """
 QUANTITY    : waterlevelbnd, velocitybnd, dischargebnd, tangentialvelocitybnd, normalvelocitybnd  filetype=9         method=2,3
             : outflowbnd, neumannbnd, qhbnd, uxuyadvectionvelocitybnd                             filetype=9         method=2,3
             : salinitybnd                                                                         filetype=9         method=2,3
             : gateloweredgelevel, damlevel, pump                                                  filetype=9         method=2,3
             : frictioncoefficient, horizontaleddyviscositycoefficient, advectiontype              filetype=4,7,10    method=4
             : bedlevel, ibotlevtype                                                               filetype=4,7,10    method=4..9
             : initialwaterlevel                                                                   filetype=4,7,10,12 method=4..9
             : initialtemperature                                                                  filetype=4,7,10,12 method=4..9
             : initialvelocityx, initialvelocityy                                                  filetype=4,7,10,12 method=4..9
             : initialvelocity                                                                     filetype=12        method=4..9
             : initialsalinity, initialsalinitytop: use initialsalinity for depth-uniform, or
             : as bed level value in combination with initialsalinitytop                           filetype=4,7,10    method=4
             : initialverticaltemperatureprofile                                                   filetype=9,10      method=
             : initialverticalsalinityprofile                                                      filetype=9,10      method=
             : windx, windy, windxy, rainfall, atmosphericpressure                                 filetype=1,2,4,6,7,8 method=1,2,3
             : shiptxy, movingstationtxy                                                           filetype=1         method=1
             : discharge_salinity_temperature_sorsin                                               filetype=9         method=1
             : windstresscoefficient                                                               filetype=4,7,10    method=4
             : nudge_salinity_temperature                                                          filetype=11        method=3

 kx = Vectormax = Nr of variables specified on the same time/space frame. Eg. Wind magnitude,direction: kx = 2
 FILETYPE=1  : uniform              kx = 1 value               1 dim array      uni
 FILETYPE=2  : unimagdir            kx = 2 values              1 dim array,     uni mag/dir transf to u,v, in index 1,2
 FILETYPE=3  : svwp                 kx = 3 fields  u,v,p       3 dim array      nointerpolation
 FILETYPE=4  : arcinfo              kx = 1 field               2 dim array      bilin/direct
 FILETYPE=5  : spiderweb            kx = 3 fields              3 dim array      bilin/spw
 FILETYPE=6  : curvi                kx = ?                                      bilin/findnm
 FILETYPE=7  : triangulation        kx = 1 field               1 dim array      triangulation
 FILETYPE=8  : triangulation_magdir kx = 2 fields consisting of Filetype=2      triangulation in (wind) stations

 FILETYPE=9  : polyline             kx = 1 For polyline points i= 1 through N specify boundary signals, either as
                                           timeseries or Fourier components or tidal constituents
                                           Timeseries are in files *_000i.tim, two columns: time (min)  values
                                           Fourier components and or tidal constituents are in files *_000i.cmp, three columns
                                           period (min) or constituent name (e.g. M2), amplitude and phase (deg)
                                           If no file is specified for a node, its value will be interpolated from surrounding nodes
                                           If only one signal file is specified, the boundary gets a uniform signal
                                           For a dischargebnd, only one signal file must be specified

 FILETYPE=10 : inside_polygon       kx = 1 field                                uniform value inside polygon for INITIAL fields
 FILETYPE=11 : ncgrid               kx = 1 field                    2 dim array      triangulation (should have proper standard_name in var, e.g., 'precipitation')
 FILETYPE=12 : ncflow (map file)    kx = 1 or 2 field               1 dim array      triangulation
 FILETYPE=14 : ncwave (com file)    kx = 1 field                    1 dim array      triangulation

 METHOD  =0  : provider just updates, another provider that pointers to this one does the actual interpolation
         =1  : intp space and time (getval) keep  2 meteofields in memory
         =2  : first intp space (update), next intp. time (getval) keep 2 flowfields in memory
         =3  : save weightfactors, intp space and time (getval),   keep 2 pointer- and weight sets in memory.
         =4  : only spatial, inside polygon
         =5  : only spatial, triangulation, (if samples from *.asc file then bilinear)
         =6  : only spatial, averaging
         =7  : only spatial, index triangulation
         =8  : only spatial, smoothing
         =9  : only spatial, internal diffusion
         =10 : only initial vertical profiles

 OPERAND =O  : Override at all points
         =+  : Add to previously specified value
         =*  : Multiply with previously specified value
         =A  : Apply only if no value specified previously (For Initial fields, similar to Quickin preserving best data specified first)
         =X  : MAX with prev. spec.
         =N  : MIN with prev. spec.

 EXTRAPOLATION_METHOD (ONLY WHEN METHOD=3)
         = 0 : No spatial extrapolation.
         = 1 : Do spatial extrapolation outside of source data bounding box.

 MAXSEARCHRADIUS (ONLY WHEN EXTRAPOLATION_METHOD=1)
         = search radius (in m) for model grid points that lie outside of the source data bounding box.

 AVERAGINGTYPE (ONLY WHEN METHOD=6)
         =1  : SIMPLE AVERAGING
         =2  : NEAREST NEIGHBOUR
         =3  : MAX (HIGHEST)
         =4  : MIN (LOWEST)
         =5  : INVERSE WEIGHTED DISTANCE-AVERAGE
         =6  : MINABS
         =7  : KDTREE (LIKE 1, BUT FAST AVERAGING)

 RELATIVESEARCHCELLSIZE : For METHOD=6, the relative search cell size for samples inside cell (default: 1.01)

 PERCENTILEMINMAX : (ONLY WHEN AVERAGINGTYPE=3 or 4) Changes the min/max operator to an average of the
               highest/lowest data points. The value sets the percentage of the total set that is to be included.

 NUMMIN  =   : For METHOD=6, minimum required number of source data points in each target cell.

 VALUE   =   : Offset value for this provider

 FACTOR  =   : Conversion factor for this provider

*************************************************************************************************************
"""


class TestExtOldModel:
    def test_header(self):
        assert HEADER == EXP_HEADER

    def test_initialization(self):
        model = ExtOldModel()

        assert model.comment == HEADER.splitlines()[1:]
        assert len(model.forcing) == 0

    def test_load_model(self):
        file_content = [
            "* This is a comment",
            "* This is a comment",
            "",
            "QUANTITY=internaltidesfrictioncoefficient",
            "FILENAME=surroundingDomain.pol",
            "FILETYPE=11",
            "METHOD=4",
            "OPERAND=+",
            "VALUE=0.0125",
            "",
            "* This is a comment",
            "",
            "QUANTITY=waterlevelbnd",
            "FILENAME=OB_001_orgsize.pli",
            "FILETYPE=9",
            "METHOD=3",
            "* This is a comment",
            "OPERAND=O",
            "* This is a comment",
        ]

        with create_temp_file_from_lines(
            file_content, "test_load_model_two_blocks.ext"
        ) as temp_file:
            model = ExtOldModel(filepath=temp_file)

        # Assert correct comments
        assert len(model.comment) == 3
        exp_comments = [" This is a comment", " This is a comment", ""]
        assert model.comment == exp_comments

        # Assert correct forcings
        assert len(model.forcing) == 2

        forcing_1 = model.forcing[0]
        assert forcing_1.quantity == ExtOldQuantity.InternalTidesFrictionCoefficient
        assert forcing_1.filename.filepath == Path("surroundingDomain.pol")
        assert forcing_1.varname is None
        assert forcing_1.sourcemask.filepath is None
        assert forcing_1.filetype == ExtOldFileType.NetCDFGridData
        assert forcing_1.method == ExtOldMethod.InterpolateSpace
        assert forcing_1.operand == Operand.add
        assert forcing_1.value == pytest.approx(0.0125)
        assert forcing_1.factor is None
        assert forcing_1.ifrctyp is None
        assert forcing_1.averagingtype is None
        assert forcing_1.relativesearchcellsize is None
        assert forcing_1.extrapoltol is None
        assert forcing_1.percentileminmax is None
        assert forcing_1.area is None
        assert forcing_1.nummin is None

        forcing_2 = model.forcing[1]
        assert forcing_2.quantity == ExtOldQuantity.WaterLevelBnd
        assert forcing_2.filename.filepath == Path("OB_001_orgsize.pli")
        assert forcing_2.varname is None
        assert forcing_2.sourcemask.filepath is None
        assert forcing_2.filetype == ExtOldFileType.Polyline
        assert forcing_2.method == ExtOldMethod.InterpolateTimeAndSpaceSaveWeights
        assert forcing_2.operand == Operand.override
        assert forcing_2.value is None
        assert forcing_2.factor is None
        assert forcing_2.ifrctyp is None
        assert forcing_2.averagingtype is None
        assert forcing_2.relativesearchcellsize is None
        assert forcing_2.extrapoltol is None
        assert forcing_2.percentileminmax is None
        assert forcing_2.area is None
        assert forcing_2.nummin is None

    def test_save_model(self):

        exp_file_content = [
            "*This is a comment",
            "*This is a comment",
            "*",
            "QUANTITY=internaltidesfrictioncoefficient",
            "FILENAME=surroundingDomain.pol",
            "FILETYPE=11",
            "METHOD=4",
            "OPERAND=+",
            "VALUE=0.012500",
            "",
            "QUANTITY=waterlevelbnd",
            "FILENAME=OB_001_orgsize.pli",
            "FILETYPE=9",
            "METHOD=3",
            "OPERAND=O",
        ]

        comments = ["This is a comment", "This is a comment", ""]

        forcing_1 = ExtOldForcing(
            quantity=ExtOldQuantity.InternalTidesFrictionCoefficient,
            filename=Path("surroundingDomain.pol"),
            filetype=ExtOldFileType.NetCDFGridData,
            method=ExtOldMethod.InterpolateSpace,
            operand=Operand.add,
            value=0.0125,
        )

        forcing_2 = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename=Path("OB_001_orgsize.pli"),
            filetype=ExtOldFileType.Polyline,
            method=ExtOldMethod.InterpolateTimeAndSpaceSaveWeights,
            operand=Operand.override,
        )

        model = ExtOldModel(comment=comments, forcing=[forcing_1, forcing_2])

        model.serializer_config.float_format = "f"

        with get_temp_file("test_save_model.ext") as file:
            model.save(filepath=file)

            with create_temp_file_from_lines(
                exp_file_content, "test_save_model_expected.ext"
            ) as exp_file:
                assert_files_equal(file, exp_file)


class TestParser:
    def test_parse_two_blocks_parses_to_the_correct_dictionaries(self):
        file_content = [
            "* This is a comment",
            "* This is a comment",
            "",
            "QUANTITY=internaltidesfrictioncoefficient",
            "FILENAME=surroundingDomain.pol",
            "FILETYPE=11",
            "METHOD=4",
            "OPERAND=+",
            "VALUE=0.0125",
            "",
            "* This is a comment",
            "",
            "QUANTITY=waterlevelbnd",
            "FILENAME=OB_001_orgsize.pli",
            "FILETYPE=9",
            "METHOD=3",
            "* This is a comment",
            "OPERAND=O",
            "* This is a comment",
        ]

        parser = Parser()

        with create_temp_file_from_lines(file_content, "two_blocks.ext") as temp_file:
            data = parser.parse(filepath=temp_file)

        exp_data = {
            "comment": [" This is a comment", " This is a comment", ""],
            "forcing": [
                {
                    "QUANTITY": "internaltidesfrictioncoefficient",
                    "FILENAME": "surroundingDomain.pol",
                    "FILETYPE": "11",
                    "METHOD": "4",
                    "OPERAND": "+",
                    "VALUE": "0.0125",
                },
                {
                    "QUANTITY": "waterlevelbnd",
                    "FILENAME": "OB_001_orgsize.pli",
                    "FILETYPE": "9",
                    "METHOD": "3",
                    "OPERAND": "O",
                },
            ],
        }

        assert data == exp_data

    def test_parse_block_with_incorrect_order_raises_error(self):
        file_lines = [
            "FILENAME=surroundingDomain.pol",
            "QUANTITY=internaltidesfrictioncoefficient",
            "FILETYPE=11",
            "OPERAND=+",
            "VALUE=0.0125",
            "QUANTITY=internaltidesfrictioncoefficient",
        ]

        parser = Parser()

        with create_temp_file_from_lines(
            file_lines, "incorrect_order.ext"
        ) as temp_file:
            with pytest.raises(ValueError) as error:
                parser.parse(filepath=temp_file)

        exp_error = "Line 1: Properties should be in the following order: QUANTITY, FILENAME, FILETYPE, OPERAND, VALUE"
        assert str(error.value) == exp_error


class TestSerializer:
    def test_serialize(self):
        exp_file_content = [
            "*This is a comment",
            "*This is a comment",
            "*",
            "QUANTITY=internaltidesfrictioncoefficient",
            "FILENAME=surroundingDomain.pol",
            "FILETYPE=11",
            "METHOD=4",
            "OPERAND=+",
            "VALUE=0.012500",
            "",
            "QUANTITY=waterlevelbnd",
            "FILENAME=OB_001_orgsize.pli",
            "FILETYPE=9",
            "METHOD=3",
            "OPERAND=O",
        ]

        comments = ["This is a comment", "This is a comment", ""]

        forcing_1 = {
            "quantity": "internaltidesfrictioncoefficient",
            "filename": DiskOnlyFileModel(Path("surroundingDomain.pol")),
            "filetype": 11,
            "method": 4,
            "operand": "+",
            "value": 0.0125,
        }

        forcing_2 = {
            "quantity": "waterlevelbnd",
            "filename": DiskOnlyFileModel(Path("OB_001_orgsize.pli")),
            "filetype": 9,
            "method": 3,
            "operand": "O",
        }

        forcing_data = {"comment": comments, "forcing": [forcing_1, forcing_2]}

        serializer_config = SerializerConfig(float_format="f")
        save_settings = ModelSaveSettings()

        with get_temp_file("test_serialize.ext") as file:
            Serializer.serialize(file, forcing_data, serializer_config, save_settings)

            with create_temp_file_from_lines(
                exp_file_content, "test_serialize_expected.ext"
            ) as exp_file:
                assert_files_equal(file, exp_file)


class TestOldInitialConditionQuantity:

    def test_ext_old_initial_condition_quantity(self, initial_condition_quantities):
        """
        Test the number of initial condition quantities in the ExtOldInitialConditionQuantity enum.
        """
        assert len(ExtOldInitialConditionQuantity) == len(initial_condition_quantities)
        assert all(
            quantity.value in initial_condition_quantities
            for quantity in ExtOldInitialConditionQuantity.__members__.values()
        )

    def test_the_missing_method(self):
        """
        Test the missing method in the ExtOldInitialConditionQuantity enum with a ValueError.
        """
        with pytest.raises(ValueError):
            ExtOldInitialConditionQuantity("missing_method")

    @pytest.mark.parametrize("qunatity_name", quantities_with_prefixes)
    def test_the_missing_method_with_tracers(self, qunatity_name):
        """
        Test the missing method in the ExtOldInitialConditionQuantity enum with a quantity that starts the quantities in the .
        """
        quantity = ExtOldInitialConditionQuantity(qunatity_name)
        assert quantity.value == qunatity_name


def test_ext_old_parameter_quantity(parameter_quantities: List[str]):
    """
    Test the number of parameter quantities in the ExtOldParametersQuantity enum.
    """
    assert len(ExtOldParametersQuantity) == len(parameter_quantities)
    assert all(
        quantity.value in parameter_quantities
        for quantity in ExtOldParametersQuantity.__members__.values()
    )


def test_ext_old_source_sinks():
    """
    Test the number of source/sinks in the ExtOldSourceSink enum.
    """
    assert len(ExtOldSourcesSinks) == 1
    assert all(
        quantity.value in ["discharge_salinity_temperature_sorsin"]
        for quantity in ExtOldSourcesSinks.__members__.values()
    )
