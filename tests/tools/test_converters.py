from pathlib import Path
from typing import List, Tuple

import numpy as np
import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.core.dflowfm.ext.models import (
    Meteo,
    MeteoForcingFileType,
    MeteoInterpolationMethod,
)
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.core.dflowfm.inifield.models import InitialField, ParameterField
from hydrolib.tools.extforce_convert.converters import (
    InitialConditionConverter,
    MeteoConverter,
    ParametersConverter,
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

    def test_polygon_data_file(self, polylines_dir: Path):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.InitialWaterLevel,
            filename=polylines_dir / "boundary-polyline-no-z-no-label.pli",
            value=0.0,
            filetype=10,
            method="4",
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
        assert new_quantity_block.operand == Operand.override
        assert new_quantity_block.forcingfile == DiskOnlyFileModel("windtest.amu")
        assert new_quantity_block.forcingfiletype == MeteoForcingFileType.arcinfo
        assert (
            new_quantity_block.interpolationmethod
            == MeteoInterpolationMethod.linearSpaceTime
        )
