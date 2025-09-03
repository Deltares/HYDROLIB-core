from pathlib import Path
from types import MethodType
import numpy as np
import pytest

from hydrolib.core.dflowfm.inifield.models import DataFileType, InterpolationMethod

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.core.dflowfm.inifield.models import InitialField, ParameterField, IniFieldModel
from hydrolib.tools.extforce_convert.converters import (
    ConverterFactory,
    InitialConditionConverter,
    ParametersConverter,
)
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.utils import (
    create_initial_cond_and_parameter_input_dict,
)
from tests.utils import compare_two_files, ignore_version_lines

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

    @pytest.mark.e2e
    @pytest.mark.parametrize(
        "quantity, expected_quantity",
        [
            pytest.param(ExtOldQuantity.BedLevel, "bedlevel"),
            pytest.param(ExtOldQuantity.InitialWaterLevel, "initialwaterlevel"),
            pytest.param(ExtOldQuantity.InitialSalinity, "initialsalinity"),
            pytest.param(ExtOldQuantity.InitialSalinityTop, "initialsalinitytop"),
            pytest.param(
                ExtOldQuantity.InitialVerticalSalinityProfile,
                "initialverticalsalinityprofile",
            ),
            pytest.param(ExtOldQuantity.InitialTemperature, "initialtemperature"),
            pytest.param(
                ExtOldQuantity.InitialVerticalTemperatureProfile,
                "initialverticaltemperatureprofile",
            ),
            pytest.param(ExtOldQuantity.InitialVelocityX, "initialvelocityx"),
            pytest.param(ExtOldQuantity.InitialVelocityY, "initialvelocityy"),
            pytest.param(ExtOldQuantity.InitialVelocity, "initialvelocity"),
        ],
    )
    def test_initial_condition_quantity(self, quantity, expected_quantity):
        """Test conversion of initial condition quantity.

        The test checks that the quantity resolves to the correct converter and that the
        quantity is converted correctly.
        """
        forcing = ExtOldForcing(
            quantity=quantity,
            filename="iniwaterlevel.xyz",
            filetype=7,
            method="5",
            operand="O",
        )

        new_forcing_dict = create_initial_cond_and_parameter_input_dict(forcing)
        assert new_forcing_dict["quantity"] == expected_quantity
        converter = ConverterFactory.create_converter(forcing.quantity)
        assert isinstance(converter, InitialConditionConverter)
        new_quantity_block = converter.convert(forcing)
        assert isinstance(new_quantity_block, InitialField)
        assert new_quantity_block.quantity == expected_quantity


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

        The test only check that the name of the quantity is converted correctly.
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

    @pytest.mark.e2e
    @pytest.mark.parametrize(
        "quantity, expected_quantity",
        [
            pytest.param(ExtOldQuantity.FrictionCoefficient, "frictioncoefficient"),
            pytest.param(
                ExtOldQuantity.HorizontalEddyViscosityCoefficient,
                "horizontaleddyviscositycoefficient",
            ),
            pytest.param(
                ExtOldQuantity.HorizontalEddyDiffusivityCoefficient,
                "horizontaleddydiffusivitycoefficient",
            ),
            pytest.param(ExtOldQuantity.AdvectionType, "advectiontype"),
            pytest.param(
                ExtOldQuantity.BedRockSurfaceElevation, "bedrockSurfaceElevation"
            ),
            pytest.param(ExtOldQuantity.WaveDirection, "wavedirection"),
            pytest.param(ExtOldQuantity.XWaveForce, "xwaveforce"),
            pytest.param(ExtOldQuantity.YWaveForce, "ywaveforce"),
            pytest.param(ExtOldQuantity.WavePeriod, "waveperiod"),
            pytest.param(ExtOldQuantity.WaveSignificantHeight, "wavesignificantheight"),
            pytest.param(
                ExtOldQuantity.InternalTidesFrictionCoefficient,
                "internaltidesfrictioncoefficient",
            ),
            pytest.param(ExtOldQuantity.SecchiDepth, "secchidepth"),
            pytest.param(ExtOldQuantity.SeaIceAreaFraction, "sea_ice_area_fraction"),
            pytest.param(ExtOldQuantity.StemHeight, "stemheight"),
            pytest.param(ExtOldQuantity.StemDensity, "stemdensity"),
            pytest.param(ExtOldQuantity.StemDiameter, "stemdiameter"),
            pytest.param(ExtOldQuantity.NudgeRate, "nudgerate"),
            pytest.param(ExtOldQuantity.NudgeTime, "nudgetime"),
        ],
    )
    def test_parameter_quantity(self, quantity, expected_quantity):
        """Test conversion of parameter quantity.

        The test checks that the quantity resolves to the correct converter and that the
        quantity is converted correctly.
        """
        forcing = ExtOldForcing(
            quantity=quantity,
            filename="iniwaterlevel.xyz",
            filetype=7,
            method="5",
            operand="O",
        )

        new_forcing_dict = create_initial_cond_and_parameter_input_dict(forcing)
        assert new_forcing_dict["quantity"] == expected_quantity
        converter = ConverterFactory.create_converter(forcing.quantity)
        assert isinstance(converter, ParametersConverter)
        new_quantity_block = converter.convert(forcing)
        assert isinstance(new_quantity_block, ParameterField)
        assert new_quantity_block.quantity == expected_quantity

class TestInifieldConverter:
    def test_save_inifield(self, tmp_path: Path):
        """
        the test mocks the converter and only instantiates the InifieldModel.
        """
        path = tmp_path / "delete-me.ini"
        data = {
            'quantity': 'initialwaterlevel',
            'datafile': DiskOnlyFileModel(filepath='iniwaterlevel.xyz'),
            'datafiletype': DataFileType.sample,
            'interpolationmethod': InterpolationMethod.triangulation,
            'operand': 'O'
        }
        ini_field = InitialField(**data)

        converter = object.__new__(ExternalForcingConverter)
        converter._save_inifield_model = MethodType(ExternalForcingConverter._save_inifield_model, converter)

        inifield_model = IniFieldModel(initial=[ini_field])
        inifield_model.filepath = path

        converter._inifield_model = inifield_model

        converter._save_inifield_model(backup=True, recursive=True)
        reference = "tests/data/reference/ini/inifield-with-one-initial.ini"
        diff = compare_two_files(
            reference,
            path,
            ignore_line=ignore_version_lines,
            )
        assert diff == []
        path.unlink()

