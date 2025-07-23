from pathlib import Path

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
from hydrolib.tools.extforce_convert.utils import (
    create_initial_cond_and_parameter_input_dict,
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

    @pytest.mark.unit
    def test_tracer_fall_velocity(self):
        """Test conversion of tracerfallvelocity forcing.
        The test check that the tracerfallvelocity is converted correctly

        - The test uses a file type = 4 in order not to add a real file.
        - The test checks the returned value from the `create_initial_cond_and_parameter_input_dict` function,
        and checks the returned value from the `InitialConditionConverter.convert` method.
        """
        # just choose any file type that is associated with DiskOnlyFileModel (3-8) in order not to add a real file
        forcing = ExtOldForcing(
            quantity="initialtracerdtr1",
            filename=DiskOnlyFileModel("fake-file.fake"),
            filetype=4,
            method="4",
            operand="O",
            TRACERFALLVELOCITY=0.1,
        )

        new_focing_dict = create_initial_cond_and_parameter_input_dict(forcing)
        assert "tracerfallvelocity" in new_focing_dict.keys()

        new_quantity_block = InitialConditionConverter().convert(forcing)
        assert isinstance(new_quantity_block, InitialField)
        assert new_quantity_block.tracerfallvelocity == pytest.approx(0.1)


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

    def test_bed_rock_surface_elevation(self):
        """Test conversion of bedrock surface elevation forcing.

        The Test only check that the name of the quantity is converted correctly.
        - all the the underscores in the old name are removed.
        - the naming convention is changed to camelCase.
        old: "bedrock_surface_elevation"
        new: "bedrockSurfaceElevation"
        """
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.BedRockSurfaceElevation,
            filename="subsupl.tim",
            filetype=7,
            method="1",
            operand="O",
        )

        new_focing_dict = create_initial_cond_and_parameter_input_dict(forcing)
        assert new_focing_dict["quantity"] == "bedrockSurfaceElevation"

        new_quantity_block = ParametersConverter().convert(forcing)
        assert isinstance(new_quantity_block, ParameterField)
        assert new_quantity_block.quantity == "bedrockSurfaceElevation"


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
