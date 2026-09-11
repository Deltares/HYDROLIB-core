import pytest
import shutil

from pathlib import Path
from unittest.mock import MagicMock

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm import Operand
from hydrolib.core.dflowfm.bc.models import ForcingModel, TimeInterpolation
from hydrolib.core.dflowfm.ext.models import ExtModel, Spatial, SpatialError, TargetLayer

from hydrolib.core.dflowfm.extold.models import (
    ExtOldForcing,
    ExtOldInitialConditionQuantity,
    ExtOldMeteoQuantity,
    ExtOldParametersQuantity,
    ExtOldQuantity,
)
from hydrolib.core.dflowfm.inifield import DataFileType, InterpolationMethod
from hydrolib.core.dflowfm.inifield.models import AveragingType
from hydrolib.tools.extforce_convert.converters import (
    FACTOR_QUANTITIES,
    ConverterFactory,
    SpatialConverter,
)
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser


class TestConvertSpatial:
    def test_default(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WindX,
            filename="windtest.amu",
            filetype=4,
            method="2",
            operand="O",
        )

        new_quantity_block = SpatialConverter().convert(forcing, forcing.filename.filepath)
        assert isinstance(new_quantity_block, Spatial)
        assert new_quantity_block.quantity == "windx"
        assert new_quantity_block.operand == Operand.override
        assert new_quantity_block.datafile == DiskOnlyFileModel("windtest.amu")
        assert new_quantity_block.datafiletype == DataFileType.arcinfo
        assert (
            new_quantity_block.interpolationmethod
            == InterpolationMethod.linear_space_time
        )

    @pytest.mark.parametrize(
        "quantity",
        list(
            dict.fromkeys(
                [q.value for q in ExtOldInitialConditionQuantity]
                + [q.value for q in ExtOldParametersQuantity]
                + [q.value for q in ExtOldMeteoQuantity]
            )
        ),
    )
    def test_all_spatial_quantities_use_spatial_converter(self, quantity):
        """All InitialCondition, Parameter, and Meteo quantities are routed to
        SpatialConverter by the factory and produce a Spatial block when converted."""
        forcing = ExtOldForcing(
            quantity=quantity,
            filename="dummy.xyz",
            filetype=7,
            method="5",
            operand="O",
        )

        converter = ConverterFactory.create_converter(forcing.quantity)
        assert isinstance(converter, SpatialConverter)

        result = converter.convert(forcing, forcing.filename.filepath)
        assert isinstance(result, Spatial)

    def test_spatial_datavalue_without_targetmaskfile(self):
        """dataValue without targetMaskFile must be accepted (targetMaskFile is optional)."""
        spatial = Spatial(
            quantity="waterlevel",
            datavalue=0.0,
        )
        assert spatial.datavalue == pytest.approx(0.0)
        assert spatial.targetmaskfile is None
        assert spatial.interpolationmethod == InterpolationMethod.constant


_RAINFALL_EXPECTED = {
    "quantity": "rainfall",
    "datafiletype": DataFileType.arcinfo,
    "datafile_name": "Sobek_Precip.bc",
    "interpolationmethod": InterpolationMethod.linear_space_time,
}

# Mapping of quantity name → expected initial value (VALUE= field) for all 24
# polygon-based initial-condition quantities defined in pt_old.ext.
_PT_OLD_EXT_QUANTITY_VALUES: dict[str, float] = {
    "initialtracerContinuity":  1.0,
    "initialtracerOXY":         7.0,
    "initialtracerAAP":         0.02,
    "initialtracerPOC1":        2.0,
    "initialtracerPON1":        0.5,
    "initialtracerPOP1":        0.02,
    "initialtracerOpal":        1.0,
    "initialtracerNH4":         0.02,
    "initialtracerNO3":         0.5,
    "initialtracerPO4":         0.01,
    "initialtracerSi":          1.0,
    "initialtracerFDIATOMS_E":  0.0,
    "initialtracerFDIATOMS_P":  0.0,
    "initialtracerGREENS_E":    0.0,
    "initialtracerGREENS_N":    0.0,
    "initialtracerGREENS_P":    0.0,
    "initialtracerBLUEGRN_E":   0.0,
    "initialtracerBLUEGRN_N":   0.0,
    "initialtracerBLUEGRN_P":   0.0,
    "initialwaqbotAAPS1":       0.0,
    "initialwaqbotDetCS1":      0.0,
    "initialwaqbotDetNS1":      0.0,
    "initialwaqbotDetPS1":      0.0,
    "initialwaqbotDetSiS1":     0.0,
}

# initialvertical* quantities from pt_old.ext (FILETYPE=9, Polyline).
# These keep the old dataFile + dataFileType=polygon approach; no dataValue.
_PT_OLD_EXT_INITIALVERTICAL: dict[str, str] = {
    "initialverticalsalinityprofile": "anticreep01-inisal.pli",
}


@pytest.mark.e2e
class TestSpatialE2E:
    """End-to-end tests for converting the hyd07_z_for_hydromt model.

    The MDU file (pt.mdu) references:
    * pt.ext        – new-format external forcing file (SourceSink blocks)
    * pt_old.ext    – old-format external forcing file with 24 initial-condition
                      quantities (initialtracerXXX / initialwaqbotXXX)

    The converter is expected to convert all 26 old-format quantities to
    ``Spatial`` blocks that are appended to the new ext model.
    """

    @pytest.fixture
    def model_copy(self, tmp_path: Path, input_files_dir: Path) -> Path:
        """Return the path to a temporary copy of the hyd07 model directory.

        Copying avoids any modifications to the original model files during
        the test run.
        """
        src = (
            input_files_dir / "spatial_block"
        )
        dst = tmp_path / src.name
        shutil.copytree(src, dst)
        return dst

    def test_pt_old_ext_quantities_converted_to_spatial(self, model_copy: Path):
        """All 26 quantities in pt_old.ext are converted to Spatial blocks.

        The converter is run via ``from_mdu`` so that both ``pt.ext`` (new-format
        file referenced by ExtForceFileNew) and ``pt_old.ext`` (old-format file
        referenced by ExtForceFile) are picked up from the MDU.

        Assertions
        ----------
        * Total Spatial block count = 26 (1 rainfall + 24 initial conditions +
          1 initialvertical*).
        * Quantity names match pt_old.ext order, preserving casing.
        * Rainfall block: dataFileType=arcInfo, dataFile=Sobek_Precip.bc,
          interpolationMethod=linearSpaceTime, operand=override.
        * InsidePolygon blocks (initialtracerXXX / initialwaqbotXXX): use
          targetMaskFile + dataValue (no dataFile / dataFileType); correct VALUE=
          per quantity; operand=override.
        * initialvertical* blocks (Polyline/FILETYPE=9): use dataFile +
          dataFileType=polygon + interpolationMethod=constant; no dataValue /
          targetMaskFile.
        * No IniField / structure blocks are produced.
        """
        mdu_file = model_copy / "pt.mdu"
        converter = ExternalForcingConverter.from_mdu(mdu_file)
        ext_model, structure_model = converter.update()

        expected_quantities = (
            [_RAINFALL_EXPECTED["quantity"]]
            + list(_PT_OLD_EXT_QUANTITY_VALUES.keys())
            + list(_PT_OLD_EXT_INITIALVERTICAL.keys())
        )

        assert len(ext_model.spatial) == len(expected_quantities), (
            f"Expected {len(expected_quantities)} Spatial blocks, "
            f"got {len(ext_model.spatial)}.  "
            f"Quantities found: {[s.quantity for s in ext_model.spatial]}"
        )

        actual_quantities = [s.quantity for s in ext_model.spatial]
        assert actual_quantities == expected_quantities, (
            f"Quantity names differ.\n"
            f"  expected: {expected_quantities}\n"
            f"  actual  : {actual_quantities}"
        )

        rainfall_block = ext_model.spatial[0]
        assert rainfall_block.quantity == _RAINFALL_EXPECTED["quantity"]
        assert rainfall_block.datafiletype == _RAINFALL_EXPECTED["datafiletype"], (
            f"rainfall: expected datafiletype={_RAINFALL_EXPECTED['datafiletype']}, "
            f"got '{rainfall_block.datafiletype}'."
        )
        assert rainfall_block.datafile.filepath.name == _RAINFALL_EXPECTED["datafile_name"], (
            f"rainfall: expected datafile='{_RAINFALL_EXPECTED['datafile_name']}', "
            f"got '{rainfall_block.datafile.filepath}'."
        )
        assert rainfall_block.interpolationmethod == _RAINFALL_EXPECTED["interpolationmethod"], (
            f"rainfall: expected interpolationmethod="
            f"{_RAINFALL_EXPECTED['interpolationmethod']}, "
            f"got '{rainfall_block.interpolationmethod}'."
        )
        assert rainfall_block.operand == Operand.override
        assert rainfall_block.datavalue is None
        assert rainfall_block.targetmaskfile is None

        n_polygon = len(_PT_OLD_EXT_QUANTITY_VALUES)
        for spatial, (quantity, expected_value) in zip(
            ext_model.spatial[1:1 + n_polygon], _PT_OLD_EXT_QUANTITY_VALUES.items()
        ):
            assert spatial.datafiletype is None, (
                f"Quantity '{spatial.quantity}': expected no datafiletype for polygon "
                f"blocks, got '{spatial.datafiletype}'."
            )
            assert spatial.datafile is None, (
                f"Quantity '{spatial.quantity}': expected no datafile for polygon blocks."
            )
            assert spatial.operand == Operand.override, (
                f"Quantity '{spatial.quantity}': expected operand='override', "
                f"got '{spatial.operand}'."
            )
            assert spatial.datavalue == pytest.approx(expected_value), (
                f"Quantity '{spatial.quantity}': expected datavalue={expected_value}, "
                f"got {spatial.datavalue}."
            )
            assert spatial.targetmaskfile.filepath.name == "pt_initals.pol", (
                f"Quantity '{spatial.quantity}': expected targetmaskfile 'pt_initals.pol', "
                f"got '{spatial.targetmaskfile.filepath}'."
            )

        for spatial, (quantity, expected_filename) in zip(
            ext_model.spatial[1 + n_polygon:], _PT_OLD_EXT_INITIALVERTICAL.items()
        ):
            assert spatial.quantity == quantity, (
                f"Expected quantity '{quantity}', got '{spatial.quantity}'."
            )
            assert spatial.datavalue is None, (
                f"Quantity '{quantity}': expected no dataValue (initialvertical* keeps "
                f"dataFile+dataFileType), got datavalue={spatial.datavalue}."
            )
            assert spatial.targetmaskfile is None, (
                f"Quantity '{quantity}': expected no targetMaskFile, "
                f"got '{spatial.targetmaskfile}'."
            )
            assert spatial.datafiletype == DataFileType.polygon, (
                f"Quantity '{quantity}': expected dataFileType=polygon, "
                f"got '{spatial.datafiletype}'."
            )
            assert spatial.datafile.filepath.name == expected_filename, (
                f"Quantity '{quantity}': expected dataFile='{expected_filename}', "
                f"got '{spatial.datafile.filepath.name}'."
            )
            assert spatial.interpolationmethod == InterpolationMethod.constant, (
                f"Quantity '{quantity}': expected interpolationMethod=constant, "
                f"got '{spatial.interpolationmethod}'."
            )
            assert spatial.operand == Operand.override

        assert len(structure_model.structure) == 0
        assert len(ext_model.meteo) == 0


_FACTOR_QUANTITY_CASES = [
    pytest.param(
        "windspeedfactor",
        "windxy",
        id="windspeedfactor->windxy",
    ),
    pytest.param(
        "solarradiationfactor",
        "solarradiation",
        id="solarradiationfactor->solarradiation",
    ),
]


class TestFactorQuantityConversion:
    """
    Tests that factor quantities (windspeedfactor, solarradiationfactor) are correctly
    converted to [Spatial] blocks with operand=multiply and the base meteorological quantity.
    """

    @pytest.mark.parametrize("factor_quantity, expected_base_quantity", _FACTOR_QUANTITY_CASES)
    def test_factor_quantity_in_factor_quantity_base(
        self, factor_quantity: str, expected_base_quantity: str
    ):
        """All supported factor quantities have an entry in FACTOR_QUANTITIES."""
        assert factor_quantity in FACTOR_QUANTITIES

    @pytest.mark.parametrize("factor_quantity, expected_base_quantity", _FACTOR_QUANTITY_CASES)
    def test_polygon_factor_quantity_converts_to_spatial_with_multiply(
        self, factor_quantity: str, expected_base_quantity: str
    ):
        """A polygon-based factor quantity converts to a Spatial block with targetMaskFile,
        dataValue, and operand=multiply, using the base quantity (not the factor quantity name).
        """
        forcing = ExtOldForcing(
            quantity=factor_quantity,
            filename=DiskOnlyFileModel("mask.pol"),
            filetype=10,
            method=4,
            value=0.8,
            operand=Operand.override,
        )

        new_block = SpatialConverter().convert(
            forcing, forcing.filename.filepath
        )

        assert isinstance(new_block, Spatial)
        assert new_block.quantity == expected_base_quantity
        assert new_block.operand == Operand.multiply
        assert new_block.datavalue == pytest.approx(0.8)
        assert new_block.targetmaskfile is not None
        assert new_block.interpolationmethod == InterpolationMethod.constant
        assert new_block.datafile is None

    @pytest.mark.parametrize("factor_quantity, expected_base_quantity", _FACTOR_QUANTITY_CASES)
    def test_factor_quantity_operand_is_always_multiply_regardless_of_original(
        self, factor_quantity: str, expected_base_quantity: str
    ):
        """The operand is always set to multiply for factor quantities, no matter the original."""
        for original_operand in list(Operand):
            forcing = ExtOldForcing(
                quantity=factor_quantity,
                filename=DiskOnlyFileModel("mask.pol"),
                filetype=10,
                method=4,
                value=1.0,
                operand=original_operand,
            )

            new_block = SpatialConverter().convert(forcing, forcing.filename.filepath)

            assert new_block.operand == Operand.multiply, (
                f"Expected multiply for operand={original_operand!r}, "
                f"got {new_block.operand!r}"
            )


class TestSpatialUniformTimToBc:
    """A FILETYPE=1 (uniform time series `.tim`) spatial/parameter quantity must be
    converted to a `.bc` file. The old `dataFileType=uniform` (`.tim`) is deprecated in
    favour of `dataFileType=bcAscii` (`.bc`) per the D-Flow FM User Manual; the `.tim` is
    attached to the `[Spatial]` block as a `ForcingModel` dataFile so a recursive save
    writes the `.bc`. METHOD=0 maps the time series to `timeInterpolation=block-From`
    (GitHub #1197: the issue's waqfunctionTemp/FILETYPE=1/METHOD=0 block)."""

    @pytest.fixture
    def mdu_parser_mock(self) -> MagicMock:
        mock = MagicMock(spec=MDUParser)
        mock.temperature_salinity_data = {
            "refdate": "minutes since 2001-01-01 00:00:00"
        }
        return mock

    def test_waqfunction_method_zero_converts_tim_to_bc(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        tim_file = tmp_path / "temperature.tim"
        tim_file.write_text("0.0 1.0\n100.0 2.0\n")
        forcing = ExtOldForcing(
            quantity="waqfunctionTemp",
            filename=tim_file,
            filetype=1,
            method=0,
            operand="O",
        )

        converter = SpatialConverter(mdu_parser=mdu_parser_mock, root_dir=tmp_path)
        block = converter.convert(forcing, forcing.filename.filepath)

        # The [Spatial] block references a .bc file (bcAscii), not the raw .tim.
        assert isinstance(block, Spatial)
        assert block.quantity == "waqfunctionTemp"
        assert block.datafiletype == DataFileType.bcascii
        assert block.interpolationmethod == InterpolationMethod.linear_space_time
        assert isinstance(block.datafile, ForcingModel)
        assert block.datafile.filepath.suffix == ".bc"
        assert block.datafile.filepath.stem == "temperature"

        # The produced .bc forcing carries block-From time interpolation (METHOD=0).
        forcing_block = block.datafile.forcing[0]
        assert forcing_block.name == "global"
        assert forcing_block.timeinterpolation == TimeInterpolation.block_from
        quantities = [qup.quantity for qup in forcing_block.quantityunitpair]
        assert quantities == ["time", "waqfunctionTemp"]
        assert forcing_block.datablock == [[0.0, 1.0], [100.0, 2.0]]

        # The .tim is registered for cleanup.
        assert tim_file in converter.legacy_files

    def test_filetype_one_non_zero_method_keeps_linear_time_interpolation(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        """The .tim -> .bc conversion is not METHOD=0 specific; a non-zero method keeps
        the default linear time interpolation but still becomes a bcAscii .bc file."""
        tim_file = tmp_path / "param.tim"
        tim_file.write_text("0.0 1.0\n100.0 2.0\n")
        forcing = ExtOldForcing(
            quantity="waqfunctionTemp",
            filename=tim_file,
            filetype=1,
            method=1,
            operand="O",
        )

        converter = SpatialConverter(mdu_parser=mdu_parser_mock, root_dir=tmp_path)
        block = converter.convert(forcing, forcing.filename.filepath)

        assert block.datafiletype == DataFileType.bcascii
        assert isinstance(block.datafile, ForcingModel)
        assert (
            block.datafile.forcing[0].timeinterpolation == TimeInterpolation.linear
        )

    def test_multi_column_tim_raises_clear_error(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        """A uniform (FILETYPE=1) spatial quantity is single-column by definition; a
        multi-column .tim has no mapping to one [Spatial] block and must raise a clear
        SpatialError (not a cryptic TimModel validation error)."""
        tim_file = tmp_path / "multi.tim"
        tim_file.write_text("0.0 1.0 5.0\n100.0 2.0 6.0\n")  # time + TWO data columns
        forcing = ExtOldForcing(
            quantity="waqfunctionTemp",
            filename=tim_file,
            filetype=1,
            method=0,
            operand="O",
        )

        converter = SpatialConverter(mdu_parser=mdu_parser_mock, root_dir=tmp_path)
        with pytest.raises(SpatialError, match="single data column"):
            converter.convert(forcing, forcing.filename.filepath)

    def test_empty_tim_raises_clear_error(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        """An empty `.tim` should raise a clear SpatialError about missing data rows."""
        tim_file = tmp_path / "empty.tim"
        tim_file.write_text("")
        forcing = ExtOldForcing(
            quantity="waqfunctionTemp",
            filename=tim_file,
            filetype=1,
            method=0,
            operand="O",
        )

        converter = SpatialConverter(mdu_parser=mdu_parser_mock, root_dir=tmp_path)
        with pytest.raises(SpatialError, match="contains no data rows"):
            converter.convert(forcing, forcing.filename.filepath)

    def test_recursive_save_writes_the_bc_file(
        self, tmp_path: Path, mdu_parser_mock: MagicMock
    ):
        """Saving the ext model recursively writes the produced temperature.bc alongside
        the external forcings file (the ForcingModel is a child of the [Spatial] block)."""
        tim_file = tmp_path / "temperature.tim"
        tim_file.write_text("0.0 1.0\n100.0 2.0\n")
        forcing = ExtOldForcing(
            quantity="waqfunctionTemp",
            filename=tim_file,
            filetype=1,
            method=0,
            operand="O",
        )

        converter = SpatialConverter(mdu_parser=mdu_parser_mock, root_dir=tmp_path)
        block = converter.convert(forcing, forcing.filename.filepath)

        ext_model = ExtModel()
        ext_model.filepath = tmp_path / "new.ext"
        ext_model.spatial = [block]
        ext_model.save(recurse=True)

        assert (tmp_path / "temperature.bc").exists()
        bc_text = (tmp_path / "temperature.bc").read_text()
        assert "block-From" in bc_text


@pytest.mark.e2e
class TestSpatialUniformTimToBcE2E:
    """Full end-to-end conversion (no mocks) of a real model whose old external forcings
    file provides a WAQ temporal parameter as a uniform time series (FILETYPE=1, a .tim).

    The model (spatial_uniform_tim/) contains:
    * model.mdu           - MDU with ExtForceFile, a [time] RefDate and empty [physics]
    * waq_temporal.ext    - old-format file: waqfunctionTemp / temperature.tim / FILETYPE=1 / METHOD=0
    * temperature.tim     - the uniform time series data file

    The converter (driven via from_mdu, using the real MDUParser) must turn this into a
    [Spatial] block referencing a converted temperature.bc (dataFileType=bcAscii,
    interpolationMethod=linearSpaceTime), and the produced .bc must carry
    timeInterpolation=block-From (GitHub #1197, D-Flow FM manual uniform->bcAscii).
    """

    @pytest.fixture
    def model_copy(self, tmp_path: Path, input_files_dir: Path) -> Path:
        """Copy the model to a temp dir so the conversion does not mutate the originals."""
        src = input_files_dir / "spatial_uniform_tim"
        dst = tmp_path / src.name
        shutil.copytree(src, dst)
        return dst

    def test_uniform_tim_quantity_converts_to_bc_spatial_block(self, model_copy: Path):
        mdu_file = model_copy / "model.mdu"
        converter = ExternalForcingConverter.from_mdu(mdu_file)
        ext_model, structure_model = converter.update()

        # A single [Spatial] block, referencing a .bc (bcAscii), not the raw .tim.
        assert len(ext_model.spatial) == 1
        block = ext_model.spatial[0]
        assert block.quantity == "waqfunctionTemp"
        assert block.datafiletype == DataFileType.bcascii
        assert block.interpolationmethod == InterpolationMethod.linear_space_time
        assert isinstance(block.datafile, ForcingModel)
        assert block.datafile.filepath.name == "temperature.bc"

        # The produced .bc forcing holds block-From (METHOD=0) with the model's refdate.
        forcing_block = block.datafile.forcing[0]
        assert forcing_block.name == "global"
        assert forcing_block.timeinterpolation == TimeInterpolation.block_from
        assert [qup.quantity for qup in forcing_block.quantityunitpair] == [
            "time",
            "waqfunctionTemp",
        ]
        assert forcing_block.quantityunitpair[0].unit == "MINUTES SINCE 2001-01-01 00:00:00"
        assert forcing_block.datablock == [[0.0, 1.0], [100.0, 2.0]]

        assert len(structure_model.structure) == 0
        assert len(ext_model.meteo) == 0

    def test_saved_files_written_to_disk(self, model_copy: Path):
        """Saving writes temperature.bc next to the new ext file, and the new ext file
        references it as a bcAscii dataFile. The old .tim is cleaned up as a legacy file."""
        mdu_file = model_copy / "model.mdu"
        converter = ExternalForcingConverter.from_mdu(mdu_file)
        converter.update()
        converter.save(backup=False)

        bc_file = model_copy / "temperature.bc"
        assert bc_file.exists()
        bc_text = bc_file.read_text()
        assert "block-From" in bc_text
        assert "waqfunctionTemp" in bc_text

        new_ext_text = (model_copy / "waq_temporal_new.ext").read_text()
        assert "dataFileType" in new_ext_text
        assert "bcAscii" in new_ext_text
        assert "temperature.bc" in new_ext_text

        # The .tim is registered as a legacy file and removed on clean().
        tim_file = model_copy / "temperature.tim"
        assert tim_file in converter.legacy_files
        converter.clean()
        assert not tim_file.exists()


class TestSpatialExtrapolationConversion:
    """The old external-forcing EXTRAPOLATION_METHOD (0/1) must be carried into the
    new Spatial block as extrapolationAllowed (bool). Regression test: the converter
    previously read a non-existent `forcing.extrapolation` attribute and wrote the
    wrong key, so the setting was silently dropped."""

    @pytest.mark.parametrize(
        "extrapolation_method, expected",
        [(1, True), (0, False), (None, False)],
    )
    def test_extrapolation_method_maps_to_extrapolationallowed(
        self, extrapolation_method, expected
    ):
        kwargs = dict(
            quantity=ExtOldQuantity.WindX,
            filename="wind.nc",
            filetype=11,
            method="3",
            operand="O",
        )
        if extrapolation_method is not None:
            kwargs["extrapolation_method"] = extrapolation_method
        forcing = ExtOldForcing(**kwargs)

        block = SpatialConverter().convert(forcing, forcing.filename.filepath)

        assert block.extrapolationallowed is expected


class TestSpatialTargetLayerConversion:
    """The old external-forcing LAYER value maps to the new Spatial targetLayer:
    -1 -> bottom, 0 -> all, a positive integer stays unchanged
    (UNST-9273, GitHub #1166 / #1167)."""

    @pytest.mark.parametrize(
        "layer, expected",
        [(-1, TargetLayer.bottom), (0, TargetLayer.all), (5, 5)],
    )
    def test_layer_maps_to_targetlayer(self, layer, expected):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WindX,
            filename="wind.nc",
            filetype=11,
            method="3",
            operand="O",
            layer=layer,
        )

        block = SpatialConverter().convert(forcing, forcing.filename.filepath)

        assert block.targetlayer == expected

    def test_no_layer_leaves_targetlayer_unset(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WindX,
            filename="wind.nc",
            filetype=11,
            method="3",
            operand="O",
        )

        block = SpatialConverter().convert(forcing, forcing.filename.filepath)

        assert block.targetlayer is None


class TestSpatialVariableNameConversion:
    """The old VARNAME maps to the new Spatial dataVariableName
    (VARNAME -> forcingVariableName -> dataVariableName, UNST-9273 + manual)."""

    def test_varname_maps_to_datavariablename(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WindX,
            filename="wind.nc",
            filetype=11,
            method="3",
            operand="O",
            varname="wind_u",
        )

        block = SpatialConverter().convert(forcing, forcing.filename.filepath)

        assert block.datavariablename == "wind_u"

    def test_no_varname_leaves_datavariablename_unset(self):
        forcing = ExtOldForcing(
            quantity=ExtOldQuantity.WindX,
            filename="wind.nc",
            filetype=11,
            method="3",
            operand="O",
        )
        converter = ConverterFactory.create_converter(forcing.quantity)
        result = converter.convert(forcing, Path("fake-file.asc"))
        assert isinstance(result, Spatial)

        block = SpatialConverter().convert(forcing, forcing.filename.filepath)

        assert block.datavariablename is None


class TestWaqSpatialConversion:
    """Tests verifying that WAQ quantities are converted to [Spatial] blocks."""

    @pytest.mark.parametrize(
        "quantity",
        [
            "waqparameter",
            "waqfunctionTau",
            "waqfunctionradsurfave",
            "waqsegmentnumber1",
            "waqsegmentfunctionVel",
        ],
    )
    def test_waq_parameter_quantities_use_spatial_converter(self, quantity):
        """ConverterFactory must route WAQ parameter quantities to SpatialConverter."""
        converter = ConverterFactory.create_converter(quantity)
        assert isinstance(converter, SpatialConverter)

    @pytest.mark.parametrize(
        "quantity",
        [
            "initialwaqbotSomething",
            "initialwaqbot",
        ],
    )
    def test_initialwaqbot_uses_spatial_converter(self, quantity):
        """ConverterFactory must route initialwaqbot quantities to SpatialConverter."""
        converter = ConverterFactory.create_converter(quantity)
        assert isinstance(converter, SpatialConverter)

    @pytest.mark.parametrize(
        "quantity",
        [
            "waqfunctionTau",
            "waqsegmentnumber1",
            "waqparameterSomething",
            "initialwaqbotSomething"
        ],
    )
    def test_waq_prefix_quantities_produce_spatial_block(self, quantity):
        """Converter must return a Spatial object for WAQ prefix-based quantities."""
        forcing = ExtOldForcing(
            quantity=quantity,
            filename=DiskOnlyFileModel("fake-file.asc"),
            filetype=4,
            method=4,
            operand="O",
        )
        converter = ConverterFactory.create_converter(forcing.quantity)
        result = converter.convert(forcing, Path("fake-file.asc"))
        assert isinstance(result, Spatial)
        assert result.quantity == quantity


_SPATIAL_BLOCKS = [
    # initial conditions
    ("initialtracerOXY", True, "Estruary.pol", 10.0, None, InterpolationMethod.constant, None),
    ("initialtracerCBOD5", True, "Estruary.pol", 3.0, None, InterpolationMethod.constant, None),
    # WAQ non-polygon parameters
    ("waqparameterSalinity", False, "salinity.xyz", None, DataFileType.sample, InterpolationMethod.averaging, AveragingType.nearestnb),
    ("waqparameterTemp", False, "temperature.asc", None, DataFileType.arcinfo, InterpolationMethod.triangulation, None),
    # WAQ polygon parameters
    ("waqparameterSOD", True, "Estruary.pol", 1.0, None, InterpolationMethod.constant, None),
    ("waqsegmentfunctionSOD", True, "Estruary.pol", 1.5, None, InterpolationMethod.constant, None),
    ("waqsegmentnumberSOD", True, "Estruary.pol", 3.0, None, InterpolationMethod.constant, None),
    ("waqfunctionSOD", True, "Estruary.pol", 4.5, None, InterpolationMethod.constant, None),
]

# Number of boundary blocks
_BOUNDARY_BLOCKS_COUNT = 2


@pytest.mark.e2e
class TestWaqQuantitiesConversion:
    """End-to-end tests for converting the waq_quantities test model.

    The MDU file (westernscheldt.mdu) references:
        - initialtracerOXY, initialtracerCBOD5  (polygon / InsidePolygon)
        - waqparameterSalinity                  (samples, METHOD=6 / averaging)
        - waqparameterTemp                       (arcInfo, METHOD=5 / triangulation)
        - waqparameterSOD                        (polygon)
        - waqsegmentfunctionSOD                  (polygon)
        - waqsegmentnumberSOD                    (polygon)
        - waqfunctionSOD                         (polygon)

    """

    @pytest.fixture
    def converted(self, tmp_path: Path, input_files_dir: Path):
        """Copy the waq_quantities model to a temp dir and run the converter."""
        src = input_files_dir / "waq_quantities"
        dst = tmp_path / src.name
        shutil.copytree(src, dst)
        mdu_file = dst / "westernscheldt.mdu"
        converter = ExternalForcingConverter.from_mdu(mdu_file)
        return converter.update()


    @pytest.mark.parametrize(
        "idx, quantity, is_polygon, file_name, datavalue, datafiletype, interpolationmethod, averagingtype",
        [(i,) + block for i, block in enumerate(_SPATIAL_BLOCKS)],
        ids=[block[0] for block in _SPATIAL_BLOCKS],
    )
    def test_spatial_block(
        self, converted, idx: int,
        quantity, is_polygon, file_name, datavalue, datafiletype, interpolationmethod, averagingtype,
    ):
        """Each old-format forcing block is converted to the correct Spatial block."""
        ext_model, _ = converted
        spatial = ext_model.spatial[idx]

        assert spatial.quantity == quantity
        assert spatial.operand == Operand.override
        assert spatial.interpolationmethod == interpolationmethod

        if is_polygon:
            assert spatial.targetmaskfile.filepath.name == file_name, (
                f"{quantity}: expected targetmaskfile='{file_name}', "
                f"got '{spatial.targetmaskfile.filepath}'"
            )
            assert spatial.datavalue == pytest.approx(datavalue), (
                f"{quantity}: expected datavalue={datavalue}, "
                f"got {spatial.datavalue}"
            )
            assert spatial.datafile is None, (
                f"{quantity}: polygon block must have no datafile"
            )
            assert spatial.datafiletype is None, (
                f"{quantity}: polygon block must have no datafiletype"
            )
        else:
            assert spatial.datafile.filepath.name == file_name, (
                f"{quantity}: expected datafile='{file_name}', "
                f"got '{spatial.datafile.filepath}'"
            )
            assert spatial.datafiletype == datafiletype, (
                f"{quantity}: expected datafiletype={datafiletype}, "
                f"got '{spatial.datafiletype}'"
            )
            assert spatial.targetmaskfile is None, (
                f"{quantity}: file-based block must have no targetmaskfile"
            )
            assert spatial.datavalue is None, (
                f"{quantity}: file-based block must have no datavalue"
            )

        if averagingtype is not None:
            assert spatial.averagingtype == averagingtype, (
                f"{quantity}: expected averagingtype={averagingtype}, "
                f"got '{spatial.averagingtype}'"
            )


    def test_structural_properties(self, converted):
        """Count, ordering, preserved boundaries, no inifield/structure blocks."""
        ext_model, structure_model = converted

        expected_quantities = [block[0] for block in _SPATIAL_BLOCKS]
        actual_quantities = [s.quantity for s in ext_model.spatial]

        assert len(ext_model.spatial) == len(_SPATIAL_BLOCKS), (
            f"Expected {len(_SPATIAL_BLOCKS)} Spatial blocks, got {len(ext_model.spatial)}. "
            f"Actual quantities: {actual_quantities}"
        )
        assert actual_quantities == expected_quantities, (
            f"Quantity order differs.\n"
            f"  expected: {expected_quantities}\n"
            f"  actual  : {actual_quantities}"
        )
        assert len(ext_model.boundary) == _BOUNDARY_BLOCKS_COUNT, (
            f"Expected {_BOUNDARY_BLOCKS_COUNT} boundary blocks, got {len(ext_model.boundary)}"
        )

        assert len(structure_model.structure) == 0
        assert len(ext_model.meteo) == 0