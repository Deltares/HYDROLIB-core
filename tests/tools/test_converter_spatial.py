import pytest
import shutil

from pathlib import Path

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm import Operand
from hydrolib.core.dflowfm.ext.models import Spatial, TargetLayer

from hydrolib.core.dflowfm.extold.models import (
    ExtOldForcing,
    ExtOldInitialConditionQuantity,
    ExtOldMeteoQuantity,
    ExtOldParametersQuantity,
    ExtOldQuantity,
)
from hydrolib.core.dflowfm.inifield import DataFileType, InterpolationMethod
from hydrolib.tools.extforce_convert.converters import (
    ConverterFactory,
    SpatialConverter,
)
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter


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

    The converter is expected to convert all 25 old-format quantities to
    ``Spatial`` blocks that are appended to the new ext model.
    """

    @pytest.fixture()
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
        ext_model, inifield_model, structure_model = converter.update()

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

        assert len(inifield_model.initial) == 0
        assert len(inifield_model.parameter) == 0
        assert len(structure_model.structure) == 0
        assert len(ext_model.meteo) == 0


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
