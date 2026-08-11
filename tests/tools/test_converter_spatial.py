from pathlib import Path
from typing import Dict
from unittest.mock import patch

import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm import Operand
from hydrolib.core.dflowfm.ext.models import Spatial
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldQuantity
from hydrolib.core.dflowfm.inifield import DataFileType, InterpolationMethod
from hydrolib.tools.extforce_convert.converters import (
    ConverterFactory,
    InitialConditionConverter,
    ParametersConverter, SpatialConverter,
)
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter


def _verify_spatial(
    block: Spatial,
    expected_quantity: str,
    expected_datafiletype: str,
    expected_interpolationmethod: str,
    expected_operand: str = "O",
):
    """Assert the basic properties of a converted Spatial block."""
    assert isinstance(block, Spatial)
    assert block.quantity == expected_quantity
    assert block.datafiletype == expected_datafiletype
    assert block.interpolationmethod == expected_interpolationmethod
    assert block.operand == expected_operand


class TestInitialConditionConverter:
    """Unit tests for InitialConditionConverter.convert()."""

    def test_sample_data_file_returns_spatial(self):
        """Converter returns a Spatial object for a sample (triangulation) file."""
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.InitialWaterLevel,
            filename="iniwaterlevel.xyz",
            filetype=7,   # Samples / triangulation
            method="5",   # triangulation
            operand="O",
        )
        result = InitialConditionConverter().convert(forcing, forcing.filename.filepath)

        assert isinstance(result, Spatial)
        assert result.datafiletype == "sample"
        assert result.interpolationmethod == "triangulation"

    def test_polygon_data_file_returns_spatial_with_value(self, polylines_dir: Path):
        """Converter returns Spatial with value and datafiletype=polygon for polygon files."""
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.InitialWaterLevel,
            filename=polylines_dir / "boundary-polyline-no-z-no-label.pli",
            value=0.5,
            filetype=10,  # InsidePolygon
            method="4",   # constant
            operand="O",
        )
        result = InitialConditionConverter().convert(forcing, forcing.filename.filepath)

        assert isinstance(result, Spatial)
        assert result.datafiletype == "polygon"
        assert result.interpolationmethod == "constant"
        assert result.value == pytest.approx(0.5)

    def test_arcinfo_data_file_returns_spatial(self):
        """Converter returns Spatial with datafiletype=arcInfo for arcinfo files."""
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.InitialSalinity,
            filename="inisalinity.xyz",
            filetype=4,   # ArcInfo
            method="5",   # triangulation
            operand="O",
        )
        result = InitialConditionConverter().convert(forcing, forcing.filename.filepath)

        assert isinstance(result, Spatial)
        assert result.datafiletype == "arcInfo"
        assert result.interpolationmethod == "triangulation"

    def test_quantity_is_preserved(self):
        """Converter preserves the original quantity name."""
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.InitialTemperature,
            filename="initemp.xyz",
            filetype=7,
            method="5",
            operand="O",
        )
        result = InitialConditionConverter().convert(forcing, forcing.filename.filepath)

        assert result.quantity == "initialtemperature"

    def test_datafile_path_is_set(self):
        """Converter sets the datafile to the provided new_forcing_path."""
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.InitialWaterLevel,
            filename="iniwaterlevel.xyz",
            filetype=7,
            method="5",
            operand="O",
        )
        new_path = Path("some/relative/iniwaterlevel.xyz")
        result = InitialConditionConverter().convert(forcing, new_path)

        assert result.datafile == DiskOnlyFileModel(new_path)

    @pytest.mark.parametrize(
        "quantity, expected_quantity",
        [
            pytest.param(ExtOldQuantity.InitialWaterLevel, "initialwaterlevel"),
            pytest.param(ExtOldQuantity.InitialSalinity, "initialsalinity"),
            pytest.param(ExtOldQuantity.InitialSalinityTop, "initialsalinitytop"),
            pytest.param(ExtOldQuantity.InitialTemperature, "initialtemperature"),
            pytest.param(ExtOldQuantity.InitialVelocityX, "initialvelocityx"),
            pytest.param(ExtOldQuantity.InitialVelocityY, "initialvelocityy"),
            pytest.param(ExtOldQuantity.InitialVelocity, "initialvelocity"),
            pytest.param(
                ExtOldQuantity.InitialVerticalSalinityProfile,
                "initialverticalsalinityprofile",
            ),
            pytest.param(
                ExtOldQuantity.InitialVerticalTemperatureProfile,
                "initialverticaltemperatureprofile",
            ),
            pytest.param(ExtOldQuantity.BedLevel, "bedlevel"),
        ],
    )
    def test_factory_returns_initial_condition_converter(
        self, quantity, expected_quantity
    ):
        """ConverterFactory routes all initial-condition quantities to InitialConditionConverter."""
        forcing = ExtOldForcing(
            quantity=quantity,
            filename="dummy.xyz",
            filetype=7,
            method="5",
            operand="O",
        )
        converter = ConverterFactory.create_converter(forcing.quantity)

        assert isinstance(converter, InitialConditionConverter)
        result = converter.convert(forcing, forcing.filename.filepath)
        assert isinstance(result, Spatial)
        assert result.quantity == expected_quantity

    def test_operand_is_preserved(self):
        """Converter preserves the OPERAND from the old forcing block."""
        for operand in ("O", "+", "*", "A"):
            forcing = ExtOldForcing(
                quantity=ExtOldQuantity.InitialWaterLevel,
                filename="iniwaterlevel.xyz",
                filetype=7,
                method="5",
                operand=operand,
            )
            result = InitialConditionConverter().convert(
                forcing, forcing.filename.filepath
            )
            assert result.operand == operand

    def test_tracer_fall_velocity_is_forwarded(self):
        """tracerFallVelocity attribute is forwarded to the Spatial block."""
        forcing = ExtOldForcing(
            quantity="initialtracerdtr1",
            filename=DiskOnlyFileModel("fake.fake"),
            filetype=4,
            method="4",
            operand="O",
            TRACERFALLVELOCITY=0.25,
        )
        result = InitialConditionConverter().convert(forcing, forcing.filename.filepath)

        assert isinstance(result, Spatial)
        assert result.tracerfallvelocity == pytest.approx(0.25)


class TestParametersConverter:
    """Unit tests for ParametersConverter.convert()."""

    def test_sample_data_file_returns_spatial(self):
        """Converter returns a Spatial object for a sample file."""
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.FrictionCoefficient,
            filename="friction.xyz",
            filetype=7,
            method="5",
            operand="O",
        )
        result = ParametersConverter().convert(forcing, forcing.filename.filepath)

        assert isinstance(result, Spatial)
        assert result.datafiletype == "sample"
        assert result.interpolationmethod == "triangulation"

    def test_arcinfo_data_file_returns_spatial(self):
        """Converter returns Spatial with datafiletype=arcInfo for ArcInfo files."""
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.HorizontalEddyViscosityCoefficient,
            filename="viscosity.asc",
            filetype=4,
            method="4",
            operand="O",
        )
        result = ParametersConverter().convert(forcing, forcing.filename.filepath)

        assert isinstance(result, Spatial)
        assert result.datafiletype == "arcInfo"
        assert result.interpolationmethod == "constant"

    def test_bedrock_surface_elevation_quantity_name_is_camelcase(self):
        """bedrockSurfaceElevation uses camelCase naming convention."""
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.BedRockSurfaceElevation,
            filename="subsupl.xyz",
            filetype=7,
            method="5",
            operand="O",
        )
        result = ParametersConverter().convert(forcing, forcing.filename.filepath)

        assert isinstance(result, Spatial)
        assert result.quantity == "bedrockSurfaceElevation"

    def test_datafile_path_is_set(self):
        """Converter sets the datafile to the provided new_forcing_path."""
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.FrictionCoefficient,
            filename="friction.xyz",
            filetype=7,
            method="5",
            operand="O",
        )
        new_path = Path("some/relative/friction.xyz")
        result = ParametersConverter().convert(forcing, new_path)

        assert result.datafile == DiskOnlyFileModel(new_path)

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
            pytest.param(ExtOldQuantity.SecchiDepth, "secchidepth"),
            pytest.param(ExtOldQuantity.StemHeight, "stemheight"),
            pytest.param(ExtOldQuantity.StemDensity, "stemdensity"),
            pytest.param(ExtOldQuantity.StemDiameter, "stemdiameter"),
        ],
    )
    def test_factory_returns_parameters_converter(self, quantity, expected_quantity):
        """ConverterFactory routes all parameter quantities to ParametersConverter."""
        forcing = ExtOldForcing(
            quantity=quantity,
            filename="dummy.xyz",
            filetype=7,
            method="5",
            operand="O",
        )
        converter = ConverterFactory.create_converter(forcing.quantity)

        assert isinstance(converter, ParametersConverter)
        result = converter.convert(forcing, forcing.filename.filepath)
        assert isinstance(result, Spatial)
        assert result.quantity == expected_quantity

    def test_operand_is_preserved(self):
        """Converter preserves the OPERAND from the old forcing block."""
        for operand in ("O", "+", "*", "A"):
            forcing = ExtOldForcing(
                quantity=ExtOldQuantity.FrictionCoefficient,
                filename="friction.xyz",
                filetype=7,
                method="5",
                operand=operand,
            )
            result = ParametersConverter().convert(forcing, forcing.filename.filepath)
            assert result.operand == operand


class TestMainConverterInitialConditions:
    """End-to-end tests: initial conditions → ext_model.spatial.

    Initial condition quantities (initialwaterlevel, initialsalinity, etc.) from
    old-style .ext files are converted to [Spatial] blocks in the new ext file.
    They do NOT go to inifield_model.initial.
    """

    def test_initial_conditions_only(
        self, old_forcing_file_initial_condition: Dict[str, str]
    ):
        """All initial-condition quantities are converted to Spatial blocks in ext_model.

        - Source file: old-external-forcing-initial-contitions-only.ext
          * initialwaterlevel (arcinfo, constant, polygon value=1.0 dropped)
          * initialwaterlevel (arcinfo, triangulation)
          * initialsalinity   (arcinfo, triangulation)
        - Expected: 3 Spatial entries in ext_model.spatial; inifield_model.initial == 0.
        """
        converter = ExternalForcingConverter(
            old_forcing_file_initial_condition["path"]
        )

        with patch(
            "hydrolib.tools.extforce_convert.main_converter."
            "ExternalForcingConverter._update_mdu_file"
        ):
            ext_model, inifield_model, structure_model = converter.update()

        num_quantities = len(old_forcing_file_initial_condition["quantities"])

        # All initial conditions land in ext_model.spatial (new Spatial block format)
        assert len(ext_model.spatial) == num_quantities
        # inifield_model stays empty – Spatial replaces the old [Initial] block
        assert len(inifield_model.initial) == 0
        assert len(inifield_model.parameter) == 0
        # No other output types
        assert len(ext_model.boundary) == 0
        assert len(ext_model.lateral) == 0
        assert len(ext_model.meteo) == 0
        assert len(ext_model.sourcesink) == 0
        assert len(structure_model.structure) == 0

        # Verify data-file types
        assert [
            ext_model.spatial[i].datafiletype for i in range(num_quantities)
        ] == old_forcing_file_initial_condition["file_type"]

        # Verify data-file paths
        assert [
            str(ext_model.spatial[i].datafile.filepath) for i in range(num_quantities)
        ] == old_forcing_file_initial_condition["file_path"]

    def test_initial_condition_quantities_are_correct(
        self, old_forcing_file_initial_condition: Dict[str, str]
    ):
        """Converted Spatial blocks carry the correct quantity names."""
        converter = ExternalForcingConverter(
            old_forcing_file_initial_condition["path"]
        )

        with patch(
            "hydrolib.tools.extforce_convert.main_converter."
            "ExternalForcingConverter._update_mdu_file"
        ):
            ext_model, _, _ = converter.update()

        assert [
            ext_model.spatial[i].quantity
            for i in range(len(old_forcing_file_initial_condition["quantities"]))
        ] == old_forcing_file_initial_condition["quantities"]

    def test_initial_conditions_operand_is_o(
        self, old_forcing_file_initial_condition: Dict[str, str]
    ):
        """All converted Spatial blocks have operand='O' (as specified in the source file)."""
        converter = ExternalForcingConverter(
            old_forcing_file_initial_condition["path"]
        )

        with patch(
            "hydrolib.tools.extforce_convert.main_converter."
            "ExternalForcingConverter._update_mdu_file"
        ):
            ext_model, _, _ = converter.update()

        for block in ext_model.spatial:
            assert block.operand == "O"


class TestMainConverterParameters:
    """End-to-end tests: parameter quantities → ext_model.spatial.

    Parameter quantities (frictioncoefficient, horizontaleddyviscositycoefficient, etc.)
    from old-style .ext files are converted to [Spatial] blocks in the new ext file.
    They do NOT go to inifield_model.parameter.
    """

    def test_parameters_only(self, old_forcing_file_parameters: Dict[str, str]):
        """All parameter quantities are converted to Spatial blocks in ext_model.

        - Source file: old-external-parameters-only.ext
          * frictioncoefficient                   (sample, triangulation)
          * horizontaleddyviscositycoefficient    (sample, triangulation)
        - Expected: 2 Spatial entries in ext_model.spatial; inifield_model.parameter == 0.
        """
        converter = ExternalForcingConverter(old_forcing_file_parameters["path"])

        with patch(
            "hydrolib.tools.extforce_convert.main_converter."
            "ExternalForcingConverter._update_mdu_file"
        ):
            ext_model, inifield_model, structure_model = converter.update()

        num_quantities = len(old_forcing_file_parameters["quantities"])

        # All parameters land in ext_model.spatial (new Spatial block format)
        assert len(ext_model.spatial) == num_quantities
        # inifield_model stays empty – Spatial replaces the old [Parameter] block
        assert len(inifield_model.parameter) == 0
        assert len(inifield_model.initial) == 0
        # No other output types
        assert len(ext_model.boundary) == 0
        assert len(ext_model.lateral) == 0
        assert len(ext_model.meteo) == 0
        assert len(ext_model.sourcesink) == 0
        assert len(structure_model.structure) == 0

        # Verify data-file types
        assert [
            ext_model.spatial[i].datafiletype for i in range(num_quantities)
        ] == old_forcing_file_parameters["file_type"]

        # Verify data-file paths
        assert [
            str(ext_model.spatial[i].datafile.filepath) for i in range(num_quantities)
        ] == old_forcing_file_parameters["file_path"]

    def test_parameter_quantities_are_correct(
        self, old_forcing_file_parameters: Dict[str, str]
    ):
        """Converted Spatial blocks carry the correct quantity names."""
        converter = ExternalForcingConverter(old_forcing_file_parameters["path"])

        with patch(
            "hydrolib.tools.extforce_convert.main_converter."
            "ExternalForcingConverter._update_mdu_file"
        ):
            ext_model, _, _ = converter.update()

        assert [
            ext_model.spatial[i].quantity
            for i in range(len(old_forcing_file_parameters["quantities"]))
        ] == old_forcing_file_parameters["quantities"]

    def test_parameters_interpolation_method(
        self, old_forcing_file_parameters: Dict[str, str]
    ):
        """Parameters with METHOD=5 are converted with interpolationMethod=triangulation."""
        converter = ExternalForcingConverter(old_forcing_file_parameters["path"])

        with patch(
            "hydrolib.tools.extforce_convert.main_converter."
            "ExternalForcingConverter._update_mdu_file"
        ):
            ext_model, _, _ = converter.update()

        for block in ext_model.spatial:
            assert block.interpolationmethod == "triangulation"


class TestMainConverterMixedSpatial:
    """End-to-end tests: files that mix initial conditions and parameters.

    The mixed old-external-forcing-initial-contitions-only.ext contains only
    initial conditions. This class extends coverage by checking that when both
    types appear the counts are correct.

    The old-external-forcing.ext file that could be used for a fully mixed test
    contains filetype=3 quantities that are no longer supported. Therefore, a
    parametrized approach is used here to test each converter in isolation.
    """

    @pytest.mark.parametrize(
        "quantity, filename, filetype, method, expected_quantity, expected_datafiletype",
        [
            pytest.param(
                ExtOldQuantity.InitialWaterLevel,
                "iniwaterlevel.xyz",
                7,
                "5",
                "initialwaterlevel",
                "sample",
                id="initial_condition_sample",
            ),
            pytest.param(
                ExtOldQuantity.InitialSalinity,
                "inisalinity.xyz",
                7,
                "5",
                "initialsalinity",
                "sample",
                id="initial_salinity_sample",
            ),
            pytest.param(
                ExtOldQuantity.FrictionCoefficient,
                "friction.xyz",
                7,
                "5",
                "frictioncoefficient",
                "sample",
                id="friction_coeff_sample",
            ),
            pytest.param(
                ExtOldQuantity.HorizontalEddyViscosityCoefficient,
                "viscosity.xyz",
                7,
                "5",
                "horizontaleddyviscositycoefficient",
                "sample",
                id="eddy_viscosity_sample",
            ),
        ],
    )
    def test_single_spatial_quantity_end_to_end(
        self,
        tmp_path: Path,
        quantity,
        filename,
        filetype,
        method,
        expected_quantity,
        expected_datafiletype,
    ):
        """A single initial-condition or parameter quantity produces exactly one Spatial block."""
        ext_content = (
            f"QUANTITY={quantity}\n"
            f"FILENAME={filename}\n"
            f"FILETYPE={filetype}\n"
            f"METHOD={method}\n"
            "OPERAND=O\n"
        )
        ext_file = tmp_path / "test.ext"
        ext_file.write_text(ext_content)

        converter = ExternalForcingConverter(ext_file)

        with patch(
            "hydrolib.tools.extforce_convert.main_converter."
            "ExternalForcingConverter._update_mdu_file"
        ):
            ext_model, inifield_model, structure_model = converter.update()

        assert len(ext_model.spatial) == 1
        assert len(inifield_model.initial) == 0
        assert len(inifield_model.parameter) == 0
        assert ext_model.spatial[0].quantity == expected_quantity
        assert ext_model.spatial[0].datafiletype == expected_datafiletype

    def test_two_initial_and_two_parameters_produce_four_spatial_blocks(
        self, tmp_path: Path
    ):
        """Two initial conditions + two parameters → four Spatial blocks, none in inifield."""
        ext_content = (
            "QUANTITY=initialwaterlevel\n"
            "FILENAME=iniwaterlevel.xyz\n"
            "FILETYPE=7\n"
            "METHOD=5\n"
            "OPERAND=O\n"
            "\n"
            "QUANTITY=initialsalinity\n"
            "FILENAME=inisalinity.xyz\n"
            "FILETYPE=7\n"
            "METHOD=5\n"
            "OPERAND=O\n"
            "\n"
            "QUANTITY=frictioncoefficient\n"
            "FILENAME=friction.xyz\n"
            "FILETYPE=7\n"
            "METHOD=5\n"
            "OPERAND=O\n"
            "\n"
            "QUANTITY=horizontaleddyviscositycoefficient\n"
            "FILENAME=viscosity.xyz\n"
            "FILETYPE=7\n"
            "METHOD=5\n"
            "OPERAND=O\n"
        )
        ext_file = tmp_path / "mixed.ext"
        ext_file.write_text(ext_content)

        converter = ExternalForcingConverter(ext_file)

        with patch(
            "hydrolib.tools.extforce_convert.main_converter."
            "ExternalForcingConverter._update_mdu_file"
        ):
            ext_model, inifield_model, structure_model = converter.update()

        assert len(ext_model.spatial) == 4
        assert len(inifield_model.initial) == 0
        assert len(inifield_model.parameter) == 0
        assert len(ext_model.boundary) == 0
        assert len(ext_model.meteo) == 0
        assert len(ext_model.lateral) == 0
        assert len(ext_model.sourcesink) == 0
        assert len(structure_model.structure) == 0

        quantities = [b.quantity for b in ext_model.spatial]
        assert "initialwaterlevel" in quantities
        assert "initialsalinity" in quantities
        assert "frictioncoefficient" in quantities
        assert "horizontaleddyviscositycoefficient" in quantities


class TestConvertSpatial:
    def test_default(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WindX,
            filename="windtest.amu",
            filetype=4,
            method="2",
            operand="O",
        )

        new_quantity_block = SpatialConverter().convert(forcing)
        assert isinstance(new_quantity_block, Spatial)
        assert new_quantity_block.quantity == "windx"
        assert new_quantity_block.operand == Operand.override
        assert new_quantity_block.datafile == DiskOnlyFileModel("windtest.amu")
        assert new_quantity_block.datafiletype == DataFileType.arcinfo
        assert (
            new_quantity_block.interpolationmethod
            == InterpolationMethod.linear_space_time
        )

    def test_nudge_salinity_temperature_uses_spatial_converter(self):
        """Test that nudge_salinity_temperature is converted to a Meteo block in the ext file."""
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.NudgeSalinityTemperature,
            filename="nudge_salinity_temperature.nc",
            filetype=11,
            method="3",
            operand="O",
        )

        converter = ConverterFactory.create_converter(forcing.quantity)
        assert isinstance(converter, SpatialConverter)

        new_quantity_block = converter.convert(forcing)
        assert isinstance(new_quantity_block, Spatial)
        assert new_quantity_block.quantity == "nudgeSalinityTemperature"
        assert new_quantity_block.datafiletype == DataFileType.netcdf