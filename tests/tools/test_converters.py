from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from hydrolib.core.basemodel import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.ext.models import Boundary, Meteo
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.core.dflowfm.inifield.models import InitialField, ParameterField
from hydrolib.core.dflowfm.polyfile.models import PolyFile
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


class TestParseTimFileForSourceSink:
    def test_list_of_ext_quantities_tim_column_mismatch(self):
        """
        The test case is based on the following assumptions:
        - The tim file has 4 columns (plus the time column), but the list of ext quantities has only 3 quantities.
        """
        tim_file = Path("tests/data/input/source-sink/leftsor.tim")
        ext_file_quantity_list = ["discharge", "temperature", "salinity"]
        converter = SourceSinkConverter()
        with pytest.raises(ValueError):
            converter.parse_tim_model(tim_file, ext_file_quantity_list)


class TestSourceSinkConverter:

    def test_get_z_sources_sinks_single_value(self):
        """
        The test case is based on the following assumptions:
        - The polyline has only 3 columns, so the zsink and zsource will have only one value which is in the third column.
        ```
        zsink = -4.2
        zsource = -3
        ```

        - The polyline file has the following structure:
        ```
        L1
             2 3
              63.35 12.95 -4.20
              45.20 6.35 -3.00
        ```
        """
        polyfile = PolyFile("tests/data/input/source-sink/leftsor.pliz")

        z_source, z_sink = SourceSinkConverter().get_z_sources_sinks(polyfile)
        assert z_source == [-3]
        assert z_sink == [-4.2]

    def test_get_z_sources_sinks_multiple_values(self):
        """
        The test case is based on the following assumptions:
        - The polyline has only four or five columns, so the zsink and zsource will have two values which is in the
        third and forth columns' values, and if there is a fifth column it will be ignored.
        ```
        zsink = [-4.2, -5.35]
        zsource = [-3, -2.90]
        ```

        - The polyline file has the following structure:
        ```
        L1
             2 3
              63.35 12.95 -4.20 -5.35
              ...

              ...
              45.20 6.35 -3.00 -2.90
        ```
        when there is a fifth column:
        ```
        L1
             2 3
              63.35 12.95 -4.20 -5.35 0
              ...

              ...
              45.20 6.35 -3.00 -2.90 0
        ```
        """
        polyfile = PolyFile("tests/data/input/source-sink/leftsor-5-columns.pliz")

        z_source, z_sink = SourceSinkConverter().get_z_sources_sinks(polyfile)
        assert z_source == [-3, -2.90]
        assert z_sink == [-4.2, -5.35]

    def test_default(self):
        """
        The test case is based on the following assumptions:
        - temperature, salinity, and initialtracer_anyname are other quantities in the ext file.
        - The ext file has the following structure:
        ```
        QUANTITY=initialtemperature
        FILENAME=right.pol
        FILETYPE=10
        METHOD=4
        OPERAND=O
        VALUE=11.

        QUANTITY=initialsalinity
        FILENAME=right.pol
        FILETYPE=10
        METHOD=4
        OPERAND=O
        VALUE=11.

        QUANTITY=initialtracer_anyname
        FILENAME=leftsor.pliz
        FILETYPE=9
        METHOD=1
        OPERAND=O

        QUANTITY=discharge_salinity_temperature_sorsin
        FILENAME=leftsor.pliz
        FILETYPE=9
        METHOD=1
        OPERAND=O
        AREA=1.0
        ```

        - The time file has the following structure:
        ```
        0.0 1.0 2.0 3.0 4.0
        100 1.0 2.0 3.0 4.0
        200 1.0 2.0 3.0 4.0
        300 1.0 2.0 3.0 4.0
        400 1.0 2.0 3.0 4.0
        ```

        - The polyline has only 3 columns, so the zsink and zsource will have only one value which is in the third column.
        ```
        zsink = -4.2
        zsource = -3
        ```

        - The polyline file has the following structure:
        ```
        L1
             2 3
              63.350456 12.950216 -4.200000
              45.200344 6.350155 -3.000
        ```

        """
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.DischargeSalinityTemperatureSorSin,
            filename="tests/data/input/source-sink/leftsor.pliz",
            filetype=9,
            method="1",
            operand="O",
            area=1.0,
        )

        ext_file_other_quantities = [
            "salinity",
            "temperature",
            "initialtracer_anyname",
        ]

        new_quantity_block = SourceSinkConverter().convert(
            forcing, ext_file_other_quantities
        )
        assert new_quantity_block.initialtracer_anyname == [4.0, 4.0, 4.0, 4.0, 4.0]
        assert new_quantity_block.salinitydelta == [3.0, 3.0, 3.0, 3.0, 3.0]
        assert new_quantity_block.temperaturedelta == [2.0, 2.0, 2.0, 2.0, 2.0]
        assert new_quantity_block.discharge == [1.0, 1.0, 1.0, 1.0, 1.0]
        assert new_quantity_block.zsink == [-4.2]
        assert new_quantity_block.zsource == [-3]

    def test_4_5_columns_polyline(self):
        """
        The test case is based on the assumptions of the default test plus the following changes:

        - The polyline has only four or five columns, so the zsink and zsource will have two values which is in the
        third and forth columns' values, and if there is a fifth column it will be ignored.
        ```
        zsink = [-4.2, -5.35]
        zsource = [-3, -2.90]
        ```

        - The polyline file has the following structure:
        ```
        L1
             2 3
              63.35 12.95 -4.20 -5.35
              ...

              ...
              45.20 6.35 -3.00 -2.90
        ```
        when there is a fifth column:
        ```
        L1
             2 3
              63.35 12.95 -4.20 -5.35 0
              ...

              ...
              45.20 6.35 -3.00 -2.90 0
        ```

        """
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.DischargeSalinityTemperatureSorSin,
            filename="tests/data/input/source-sink/leftsor-5-columns.pliz",
            filetype=9,
            method="1",
            operand="O",
            area=1.0,
        )

        ext_file_other_quantities = [
            "salinity",
            "temperature",
            "initialtracer_anyname",
        ]
        tim_file = Path("tests/data/input/source-sink/leftsor.tim")
        with patch("pathlib.Path.with_suffix", return_value=tim_file):
            new_quantity_block = SourceSinkConverter().convert(
                forcing, ext_file_other_quantities
            )
        assert new_quantity_block.initialtracer_anyname == [4.0, 4.0, 4.0, 4.0, 4.0]
        assert new_quantity_block.salinitydelta == [3.0, 3.0, 3.0, 3.0, 3.0]
        assert new_quantity_block.temperaturedelta == [2.0, 2.0, 2.0, 2.0, 2.0]
        assert new_quantity_block.discharge == [1.0, 1.0, 1.0, 1.0, 1.0]
        assert new_quantity_block.zsink == [-4.2, -5.35]
        assert new_quantity_block.zsource == [-3, -2.90]
