import numpy as np

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.ext.models import Boundary, Meteo
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.core.dflowfm.inifield.models import InitialField, ParameterField
from hydrolib.tools.ext_old_to_new.converters import (
    BoundaryConditionConverter,
    InitialConditionConverter,
    MeteoConverter,
    ParametersConverter,
    SourceSinkConverter,
)


class TestConvertInitialCondition:
    def test_sample_data_file(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.InitialWaterLevel,
            filename="iniwaterlevel.xyz",
            filetype=7,  # "Polyline"
            method="5",  # "Interpolate space",
            operand="O",
        )

        new_quantity_block = InitialConditionConverter().convert(forcing)
        assert isinstance(new_quantity_block, InitialField)
        assert new_quantity_block.datafiletype == "sample"
        assert new_quantity_block.interpolationmethod == "triangulation"

    def test_polygon_data_file(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.InitialWaterLevel,
            filename="iniwaterlevel.pol",
            value=0.0,
            filetype=10,  # "Polyline"
            method="4",  # "Interpolate space",
            operand="O",
        )
        new_quantity_block = InitialConditionConverter().convert(forcing)
        assert new_quantity_block.datafiletype == "polygon"
        assert new_quantity_block.interpolationmethod == "constant"
        assert np.isclose(new_quantity_block.value, 0.0)


class TestConvertParameters:
    def test_sample_data_file(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.FrictionCoefficient,
            filename="iniwaterlevel.xyz",
            filetype=7,  # "Polyline"
            method="5",  # "Interpolate space",
            operand="O",
        )

        new_quantity_block = ParametersConverter().convert(forcing)
        assert isinstance(new_quantity_block, ParameterField)
        assert new_quantity_block.datafiletype == "sample"
        assert new_quantity_block.interpolationmethod == "triangulation"


class TestConvertMeteo:
    def test_default(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WindX,
            filename="windtest.amu",
            filetype=4,
            method="2",
            operand="O",
        )

        new_quantity_block = MeteoConverter().convert(forcing)
        assert isinstance(new_quantity_block, Meteo)
        assert new_quantity_block.quantity == "windx"
        assert new_quantity_block.operand == "O"
        assert new_quantity_block.forcingfile == DiskOnlyFileModel("windtest.amu")
        assert new_quantity_block.forcingfiletype == "meteoGridEqui"
        assert new_quantity_block.interpolationmethod == "linearSpaceTime"


class TestBoundaryConverter:

    def test_default(self):
        """
        Old quantity block:

        ```
        QUANTITY =waterlevelbnd
        FILENAME =tfl_01.pli
        FILETYPE =9
        METHOD   =3
        OPERAND  =O
        ```
        """
        file_name = "tests/data/input/boundary-conditions/tfl_01.pli"
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WaterLevelBnd,
            filename=file_name,
            filetype=9,  # "Polyline"
            method="3",  # "Interpolate space",
            operand="O",
        )

        new_quantity_block = BoundaryConditionConverter().convert(forcing)
        assert isinstance(new_quantity_block, Boundary)
        assert new_quantity_block.quantity == "waterlevelbnd"
        assert new_quantity_block.forcingfile == ForcingModel()
        assert new_quantity_block.locationfile == DiskOnlyFileModel(file_name)
        assert new_quantity_block.nodeid is None
        assert new_quantity_block.bndwidth1d is None
        assert new_quantity_block.bndbldepth is None


class TestSourceSinkConverter:

    def test_default(self):
        """
        Old quantity block:

        ```
        QUANTITY =waterlevelbnd
        FILENAME =tfl_01.pli
        FILETYPE =9
        METHOD   =3
        OPERAND  =O
        ```
        """
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.DischargeSalinityTemperatureSorSin,
            filename="tests/data/input/source-sink/leftsor.pliz",
            filetype=9,  # "Polyline"
            method="1",  # "Interpolate space",
            operand="O",
            area=1.0,
        )

        # the list of quantites names comes from the external forcing file
        ext_file_other_quantities = [
            "temperaturedelta",
            "salinitydelta",
            "initialtracer_anyname",
        ]

        new_quantity_block = SourceSinkConverter().convert(
            forcing, ext_file_other_quantities
        )
        assert new_quantity_block.initialtracer_anyname == [4.0, 4.0, 4.0, 4.0, 4.0]
        assert new_quantity_block.salinitydelta == [3.0, 3.0, 3.0, 3.0, 3.0]
        assert new_quantity_block.temperaturedelta == [2.0, 2.0, 2.0, 2.0, 2.0]
        assert new_quantity_block.discharge == [1.0, 1.0, 1.0, 1.0, 1.0]
        assert new_quantity_block.zsink == -4.2
        assert new_quantity_block.zsource == -3