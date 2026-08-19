"""Characterization tests for the `Spatial` block and its divergences from `Meteo`.

These tests lock the *current* behaviour of `Spatial` (and the shared behaviour of
`Meteo`) before the `_SpatialForcingBase` extraction. Tests that assert *correct*
behaviour are expected to pass and act as a regression net. Tests marked
`xfail(strict=True)` pin the known bugs documented in `spatial-meteo-findings.md`;
they will flip to XPASS (and fail the suite, prompting marker removal) once the
refactor fixes them.

Findings reference:
    * Bug A — `Spatial` rejects legacy operand letters that `Meteo` accepts.
    * Bug B — `Spatial` never resolves a data file to its real model
              (always `DiskOnlyFileModel`), unlike `Meteo`.
    * Bug C — `averagingType` is typed `int` on `Meteo` but `AveragingType` on `Spatial`.
"""

import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm import Operand
from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.ext.models import ExtModel, Meteo, Spatial
from hydrolib.core.dflowfm.inifield import AveragingType, InterpolationMethod
from hydrolib.core.dflowfm.tim.models import TimModel

BC_FIXTURE = Path("tests/data/input/spatial_block/Sobek_Precip.bc")
TIM_FIXTURE = Path("tests/data/input/e02/f006_external_forcing/c063_rain_tim/rainschematic.tim")

BUG_A = "Bug A: Spatial.validate_operand omits legacy_alternatives; fixed in _SpatialForcingBase refactor."
BUG_B = "Bug B: Spatial before-validator ordering strands datafile as DiskOnlyFileModel; fixed in refactor."


def _write_ext(directory: Path, spatial_body: str) -> Path:
    """Write a minimal new-format `.ext` with a single `[Spatial]` block and return its path."""
    content = (
        "[General]\n"
        "fileVersion = 2.01\n"
        "fileType    = extForce\n"
        "\n"
        "[Spatial]\n"
        f"{spatial_body}"
    )
    path = directory / "spatial.ext"
    path.write_text(content)
    return path


# --------------------------------------------------------------------------- #
# Group 1 — [Spatial] file round-trip (parse-from-disk path)
# --------------------------------------------------------------------------- #
class TestSpatialFileRoundTrip:
    """Exercises `_process_section_values` + `choose_file_model`: parsing a
    `[Spatial]` block from an actual `.ext` file (no test does this today)."""

    def test_datavalue_block_roundtrips_from_file(self, tmp_path: Path):
        body = (
            "quantity            = waterlevel\n"
            "dataValue           = 5.0\n"
            "interpolationMethod = constant\n"
            "operand             = override\n"
        )
        ext_path = _write_ext(tmp_path, body)

        model = ExtModel(ext_path)

        assert len(model.spatial) == 1
        block = model.spatial[0]
        assert block.quantity == "waterlevel"
        assert block.datavalue == 5.0
        assert block.interpolationmethod == InterpolationMethod.constant
        assert block.operand == Operand.override

    @pytest.mark.xfail(reason=BUG_B, strict=True)
    def test_bcascii_datafile_parsed_from_file(self, tmp_path: Path):
        shutil.copy(BC_FIXTURE, tmp_path / BC_FIXTURE.name)
        body = (
            "quantity     = rainfall\n"
            f"dataFile     = {BC_FIXTURE.name}\n"
            "dataFileType = bcAscii\n"
            "operand      = override\n"
        )
        ext_path = _write_ext(tmp_path, body)

        block = ExtModel(ext_path).spatial[0]

        assert isinstance(block.datafile, ForcingModel)

    @pytest.mark.xfail(reason=BUG_B, strict=True)
    def test_uniform_datafile_parsed_from_file(self, tmp_path: Path):
        shutil.copy(TIM_FIXTURE, tmp_path / TIM_FIXTURE.name)
        body = (
            "quantity     = rainfall\n"
            f"dataFile     = {TIM_FIXTURE.name}\n"
            "dataFileType = uniform\n"
            "operand      = override\n"
        )
        ext_path = _write_ext(tmp_path, body)

        block = ExtModel(ext_path).spatial[0]

        assert isinstance(block.datafile, TimModel)


# --------------------------------------------------------------------------- #
# Group 2 — mirror Meteo vs Spatial (the divergences the shared base must reconcile)
# --------------------------------------------------------------------------- #
class TestMeteoSpatialParity:
    """Same concept, both classes — locks where they agree and pins where they diverge."""

    def test_meteo_bcascii_resolves_to_forcingmodel(self):
        block = Meteo(
            quantity="rainfall",
            forcingFile=str(BC_FIXTURE),
            forcingFileType="bcAscii",
        )
        assert isinstance(block.forcingfile, ForcingModel)

    @pytest.mark.xfail(reason=BUG_B, strict=True)
    def test_spatial_bcascii_resolves_to_forcingmodel(self):
        block = Spatial(
            quantity="rainfall",
            dataFile=str(BC_FIXTURE),
            dataFileType="bcAscii",
        )
        assert isinstance(block.datafile, ForcingModel)

    def test_meteo_accepts_legacy_operand(self):
        block = Meteo(
            quantity="rainfall",
            forcingFile="rainfall.nc",
            forcingFileType="netcdf",
            operand="O",
        )
        assert block.operand == Operand.override

    @pytest.mark.xfail(reason=BUG_A, strict=True)
    def test_spatial_accepts_legacy_operand(self):
        block = Spatial(
            quantity="rainfall",
            dataFile="rainfall.nc",
            dataFileType="netcdf",
            operand="O",
        )
        assert block.operand == Operand.override

    def test_meteo_averagingtype_is_raw_int(self):
        """Characterizes Bug C: Meteo stores averagingType as a raw int."""
        block = Meteo(
            quantity="rainfall",
            forcingFile="rainfall.nc",
            forcingFileType="netcdf",
            averagingType=2,
        )
        assert block.averagingtype == 2
        assert isinstance(block.averagingtype, int)

    def test_spatial_averagingtype_is_enum(self):
        """Characterizes Bug C: Spatial stores averagingType as the enum."""
        block = Spatial(
            quantity="rainfall",
            dataFile="rainfall.nc",
            dataFileType="netcdf",
            averagingType="mean",
        )
        assert block.averagingtype == AveragingType.mean

    def test_extrapolationallowed_defaults_diverge(self):
        """Characterizes the differing defaults: Meteo=None vs Spatial=False."""
        meteo = Meteo(
            quantity="rainfall", forcingFile="rainfall.nc", forcingFileType="netcdf"
        )
        spatial = Spatial(
            quantity="rainfall", dataFile="rainfall.nc", dataFileType="netcdf"
        )
        assert meteo.extrapolationallowed is None
        assert spatial.extrapolationallowed is False


# --------------------------------------------------------------------------- #
# Group 3 — Spatial dataValue / dataFile mutually-exclusive validation
# --------------------------------------------------------------------------- #
class TestSpatialDataValueValidation:
    """Locks the two mutually-exclusive usage paths and the polygon deprecation."""

    def test_datavalue_with_datafile_is_rejected(self):
        with pytest.raises(ValidationError):
            Spatial(
                quantity="waterlevel",
                dataValue=5.0,
                dataFile="rainfall.nc",
                dataFileType="netcdf",
            )

    def test_datavalue_forces_constant_interpolation(self):
        block = Spatial(quantity="waterlevel", dataValue=5.0)
        assert block.interpolationmethod == InterpolationMethod.constant

    def test_datavalue_with_nonconstant_interpolation_is_rejected(self):
        with pytest.raises(ValidationError):
            Spatial(
                quantity="waterlevel",
                dataValue=5.0,
                interpolationMethod="triangulation",
            )

    def test_datafile_without_datafiletype_is_rejected(self):
        with pytest.raises(ValidationError):
            Spatial(quantity="rainfall", dataFile="rainfall.nc")

    def test_neither_datafile_nor_datavalue_is_rejected(self):
        with pytest.raises(ValidationError):
            Spatial(quantity="rainfall")

    def test_polygon_datafiletype_warns_for_regular_quantity(self):
        with pytest.warns(DeprecationWarning):
            Spatial(
                quantity="waterlevel",
                dataFile="area.pol",
                dataFileType="polygon",
            )

    def test_polygon_datafiletype_allowed_for_initialvertical(self, recwarn):
        Spatial(
            quantity="initialverticalsalinityprofile",
            dataFile="profile.pol",
            dataFileType="polygon",
        )
        assert not any(
            issubclass(w.category, DeprecationWarning)
            and "polygon" in str(w.message).lower()
            for w in recwarn
        )
