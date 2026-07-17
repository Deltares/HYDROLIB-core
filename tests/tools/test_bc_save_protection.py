"""Regression tests: existing .bc files must survive ExternalForcingConverter.save(recursive=True).

When an existing new-format .ext file is supplied as ``ext_file`` at construction time,
``ExternalForcingConverter.__init__`` loads it with ``recurse=True``, which parses every
referenced .bc file into a ``ForcingModel``.  ``mark_existing_forcing_models_as_skip_save_models``
then replaces those objects with ``SkipSaveForcingModel`` instances whose ``_save`` is a no-op,
so a subsequent ``converter.save(recursive=True)`` leaves the pre-existing .bc files on disk
completely untouched.

These tests lock in that behaviour for:
* ``[Boundary]`` blocks (forcingFile field)
* ``[Lateral]`` blocks (discharge field pointing to a .bc file)
* ``[SourceSink]`` blocks (discharge field)
* ``[SourceSink]`` blocks with dynamic ``tracer<name>Delta`` / ``sedFrac<name>Delta`` fields
  stored in ``model_extra`` (the path that regressed silently).
* ``[Meteo]`` blocks (forcingFile with forcingFileType = bcAscii)
"""

from pathlib import Path
from typing import Dict

import pytest

from hydrolib.core.dflowfm.bc.models import ForcingModel, SkipSaveForcingModel
from hydrolib.core.dflowfm.ext.models import (
    ExtModel,
    Lateral,
    Meteo,
    MeteoForcingFileType,
    SourceSink,
)
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.utils import (
    mark_existing_forcing_models_as_skip_save_models,
)

# ---------------------------------------------------------------------------
# Minimal valid .bc file content (constant forcing, no time column needed)
# ---------------------------------------------------------------------------

_BC_BOUNDARY = """\
[General]
    fileVersion           = 1.01
    fileType              = boundConds

[forcing]
    name                  = bnd_01
    function              = constant
    time-interpolation    = linear
    quantity              = waterlevelbnd
    unit                  = m
    1.5
"""

_BC_SOURCESINK = """\
[General]
    fileVersion           = 1.01
    fileType              = boundConds

[forcing]
    name                  = src01_discharge
    function              = constant
    time-interpolation    = linear
    quantity              = sourcesink_discharge
    unit                  = m3/s
    10.0
"""

_BC_TRACER_DELTA = """\
[General]
    fileVersion           = 1.01
    fileType              = boundConds

[forcing]
    name                  = src01_tracermydelta
    function              = constant
    time-interpolation    = linear
    quantity              = initialtracer_my
    unit                  = -
    0.5
"""

_BC_LATERAL = """\
[General]
    fileVersion           = 1.01
    fileType              = boundConds

[forcing]
    name                  = lat01
    function              = constant
    time-interpolation    = linear
    quantity              = lateral_discharge
    unit                  = m3 s-1
    5.0
"""

_BC_METEO = """\
[forcing]
    name                  = global
    function              = timeseries
    time-interpolation    = linear
    quantity              = time
    unit                  = minutes since 2015-01-01 00:00:00
    quantity              = rainfall_rate
    unit                  = mm day-1
    0.0   0.0
    60.0  10.0
"""


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def bc_dir(tmp_path: Path) -> Path:
    """Populate *tmp_path* with a self-consistent converter fixture.

    Layout
    ------
    old_forcing.ext     – old-style ext (windx meteo; MeteoConverter needs no mdu_parser)
    existing_new.ext    – already-converted new-style ext referencing the .bc files below
    boundary.bc         – referenced by [Boundary].forcingFile
    sourcesink.bc       – referenced by [SourceSink].discharge
    tracer_delta.bc     – referenced by [SourceSink].tracerMyDelta (dynamic delta field)
    lateral.bc          – referenced by [Lateral].discharge
    meteo.bc            – referenced by [Meteo].forcingFile (forcingFileType = bcAscii)
    """
    # Old-format ext – single windx meteo block; requires no mdu_parser during save.
    (tmp_path / "old_forcing.ext").write_text(
        "QUANTITY=windx\n"
        "FILENAME=wind.amu\n"
        "FILETYPE=4\n"
        "METHOD=2\n"
        "OPERAND=O\n"
    )

    # Pre-existing .bc files that must NOT be rewritten.
    (tmp_path / "boundary.bc").write_text(_BC_BOUNDARY)
    (tmp_path / "sourcesink.bc").write_text(_BC_SOURCESINK)
    (tmp_path / "tracer_delta.bc").write_text(_BC_TRACER_DELTA)
    (tmp_path / "lateral.bc").write_text(_BC_LATERAL)
    (tmp_path / "meteo.bc").write_text(_BC_METEO)

    # New-format ext that already exists and references the .bc files above.
    # tracerMyDelta is a dynamic delta field that ends up in SourceSink.model_extra.
    (tmp_path / "existing_new.ext").write_text(
        "[General]\n"
        "fileType     = extForce\n"
        "fileVersion  = 2.02\n"
        "\n"
        "[Boundary]\n"
        "quantity     = waterlevelbnd\n"
        "nodeId       = bnd_01\n"
        "forcingFile  = boundary.bc\n"
        "\n"
        "[Lateral]\n"
        "id               = lat01\n"
        "name             = lat01\n"
        "nodeId           = n01\n"
        "discharge        = lateral.bc\n"
        "\n"
        "[SourceSink]\n"
        "id               = src01\n"
        "name             = src01\n"
        "numCoordinates   = 1\n"
        "xCoordinates     = 0.0\n"
        "yCoordinates     = 0.0\n"
        "discharge        = sourcesink.bc\n"
        "tracerMyDelta    = tracer_delta.bc\n"
        "\n"
        "[Meteo]\n"
        "quantity         = rainfall_rate\n"
        "forcingFile      = meteo.bc\n"
        "forcingFileType  = bcAscii\n"
    )

    return tmp_path


# ---------------------------------------------------------------------------
# Integration tests: full converter round-trip
# ---------------------------------------------------------------------------


class TestBcFilesNotOverwrittenOnRecursiveSave:
    """Regression suite for ExternalForcingConverter.save(recursive=True).

    Each test creates a converter that points at an *already-existing* new-format
    .ext (which references .bc files), calls ``save(recursive=True)``, and asserts
    that the pre-existing .bc files are byte-for-byte identical afterwards.
    """

    def _original_contents(self, d: Path, *names: str) -> Dict[str, str]:
        return {name: (d / name).read_text() for name in names}

    def _make_converter(self, d: Path) -> ExternalForcingConverter:
        return ExternalForcingConverter(
            d / "old_forcing.ext",
            ext_file=d / "existing_new.ext",
        )

    def test_boundary_bc_unchanged_after_save(self, bc_dir: Path):
        """[Boundary].forcingFile .bc must not be rewritten by recursive save."""
        original = (bc_dir / "boundary.bc").read_text()

        converter = self._make_converter(bc_dir)
        converter.save(backup=False, recursive=True)

        assert (bc_dir / "boundary.bc").read_text() == original

    def test_lateral_discharge_bc_unchanged_after_save(self, bc_dir: Path):
        """[Lateral].discharge .bc must not be rewritten by recursive save."""
        original = (bc_dir / "lateral.bc").read_text()

        converter = self._make_converter(bc_dir)
        converter.save(backup=False, recursive=True)

        assert (bc_dir / "lateral.bc").read_text() == original

    def test_sourcesink_discharge_bc_unchanged_after_save(self, bc_dir: Path):
        """[SourceSink].discharge .bc must not be rewritten by recursive save."""
        original = (bc_dir / "sourcesink.bc").read_text()

        converter = self._make_converter(bc_dir)
        converter.save(backup=False, recursive=True)

        assert (bc_dir / "sourcesink.bc").read_text() == original

    def test_sourcesink_tracer_delta_bc_unchanged_after_save(self, bc_dir: Path):
        """[SourceSink] dynamic tracerXxxDelta .bc must not be rewritten by recursive save."""
        original = (bc_dir / "tracer_delta.bc").read_text()

        converter = self._make_converter(bc_dir)
        converter.save(backup=False, recursive=True)

        assert (bc_dir / "tracer_delta.bc").read_text() == original

    def test_meteo_bc_unchanged_after_save(self, bc_dir: Path):
        """[Meteo].forcingFile (bcAscii) .bc must not be rewritten by recursive save."""
        original = (bc_dir / "meteo.bc").read_text()

        converter = self._make_converter(bc_dir)
        converter.save(backup=False, recursive=True)

        assert (bc_dir / "meteo.bc").read_text() == original

    def test_all_bc_files_unchanged_after_save(self, bc_dir: Path):
        """All five pre-existing .bc files survive a single save(recursive=True) call."""
        bc_names = [
            "boundary.bc",
            "lateral.bc",
            "sourcesink.bc",
            "tracer_delta.bc",
            "meteo.bc",
        ]
        originals = self._original_contents(bc_dir, *bc_names)

        converter = self._make_converter(bc_dir)
        converter.save(backup=False, recursive=True)

        for name, original in originals.items():
            assert (bc_dir / name).read_text() == original, (
                f"{name} was modified by save(recursive=True)"
            )


# ---------------------------------------------------------------------------
# Unit tests: mark_existing_forcing_models_as_skip_save_models
# ---------------------------------------------------------------------------


class TestMarkExistingForcingModelsAsSkipSave:
    """Unit tests for the helper that swaps ForcingModel → SkipSaveForcingModel.

    These test the guard in isolation, independent of the full converter pipeline.
    """

    def test_boundary_forcingfile_replaced(self, tmp_path: Path):
        """ForcingModel on Boundary.forcingfile must become SkipSaveForcingModel."""
        bc_path = tmp_path / "boundary.bc"
        bc_path.write_text(_BC_BOUNDARY)

        ext_model = ExtModel(
            boundary=[
                {
                    "quantity": "waterlevelbnd",
                    "nodeid": "bnd_01",
                    "forcingfile": str(bc_path),
                }
            ]
        )

        boundary = ext_model.boundary[0]
        assert isinstance(boundary.forcingfile, ForcingModel)
        assert not isinstance(boundary.forcingfile, SkipSaveForcingModel)

        mark_existing_forcing_models_as_skip_save_models(ext_model)

        assert isinstance(ext_model.boundary[0].forcingfile, SkipSaveForcingModel)
        # filepath is preserved so the .ext still references the correct .bc file
        assert ext_model.boundary[0].forcingfile.filepath == bc_path

    def test_sourcesink_discharge_replaced(self, tmp_path: Path):
        """ForcingModel on SourceSink.discharge must become SkipSaveForcingModel."""
        bc_path = tmp_path / "sourcesink.bc"
        bc_path.write_text(_BC_SOURCESINK)

        sourcesink = SourceSink(
            **{
                "id": "src01",
                "numcoordinates": 1,
                "xcoordinates": [0.0],
                "ycoordinates": [0.0],
                "discharge": str(bc_path),
            }
        )
        ext_model = ExtModel(sourcesink=[sourcesink])

        assert isinstance(sourcesink.discharge, ForcingModel)
        assert not isinstance(sourcesink.discharge, SkipSaveForcingModel)

        mark_existing_forcing_models_as_skip_save_models(ext_model)

        assert isinstance(ext_model.sourcesink[0].discharge, SkipSaveForcingModel)

    def test_sourcesink_tracer_delta_in_model_extra_replaced(self, tmp_path: Path):
        """ForcingModel in a dynamic tracerXxxDelta model_extra field must become SkipSaveForcingModel.

        When the new-format .ext is read from disk the INI parser lowercases all
        property keys (via ``to_key``), so ``tracerMyDelta`` is stored in
        ``model_extra`` as ``tracermydelta``.  This test verifies that
        ``mark_existing_forcing_models_as_skip_save_models`` finds and replaces it.
        """
        bc_path = tmp_path / "tracer_delta.bc"
        bc_path.write_text(_BC_TRACER_DELTA)

        # Simulate the lowercased key that results from INI-file parsing.
        sourcesink = SourceSink(
            **{
                "id": "src01",
                "numcoordinates": 1,
                "xcoordinates": [0.0],
                "ycoordinates": [0.0],
                "discharge": 10.0,
                "tracermydelta": str(bc_path),
            }
        )
        ext_model = ExtModel(sourcesink=[sourcesink])

        # The dynamic delta field is held in model_extra.
        tracer_field = sourcesink.model_extra.get("tracermydelta")
        assert isinstance(tracer_field, ForcingModel), (
            "tracermydelta should be a ForcingModel before the guard runs"
        )
        assert not isinstance(tracer_field, SkipSaveForcingModel)

        mark_existing_forcing_models_as_skip_save_models(ext_model)

        tracer_after = ext_model.sourcesink[0].model_extra.get("tracermydelta")
        assert isinstance(tracer_after, SkipSaveForcingModel), (
            "tracermydelta should be a SkipSaveForcingModel after the guard runs"
        )

    def test_already_skip_save_not_double_wrapped(self, tmp_path: Path):
        """Calling the guard twice must not change already-replaced models."""
        bc_path = tmp_path / "boundary.bc"
        bc_path.write_text(_BC_BOUNDARY)

        ext_model = ExtModel(
            boundary=[
                {
                    "quantity": "waterlevelbnd",
                    "nodeid": "bnd_01",
                    "forcingfile": str(bc_path),
                }
            ]
        )

        mark_existing_forcing_models_as_skip_save_models(ext_model)
        first_instance = ext_model.boundary[0].forcingfile

        # Second call must be a no-op.
        mark_existing_forcing_models_as_skip_save_models(ext_model)
        second_instance = ext_model.boundary[0].forcingfile

        assert first_instance is second_instance

    def test_lateral_discharge_replaced(self, tmp_path: Path):
        """ForcingModel on Lateral.discharge must become SkipSaveForcingModel."""
        bc_path = tmp_path / "lateral.bc"
        bc_path.write_text(_BC_LATERAL)

        lateral = Lateral(
            **{
                "id": "lat01",
                "nodeid": "n01",
                "discharge": str(bc_path),
            }
        )
        ext_model = ExtModel(lateral=[lateral])

        assert isinstance(lateral.discharge, ForcingModel)
        assert not isinstance(lateral.discharge, SkipSaveForcingModel)

        mark_existing_forcing_models_as_skip_save_models(ext_model)

        assert isinstance(ext_model.lateral[0].discharge, SkipSaveForcingModel)
        assert ext_model.lateral[0].discharge.filepath == bc_path

    def test_lateral_already_skip_save_not_double_wrapped(self, tmp_path: Path):
        """Calling the guard twice must not change an already-replaced Lateral model."""
        bc_path = tmp_path / "lateral.bc"
        bc_path.write_text(_BC_LATERAL)

        ext_model = ExtModel(
            lateral=[
                {
                    "id": "lat01",
                    "nodeid": "n01",
                    "discharge": str(bc_path),
                }
            ]
        )

        mark_existing_forcing_models_as_skip_save_models(ext_model)
        first_instance = ext_model.lateral[0].discharge

        mark_existing_forcing_models_as_skip_save_models(ext_model)
        second_instance = ext_model.lateral[0].discharge

        assert first_instance is second_instance

    def test_meteo_forcingfile_replaced(self, tmp_path: Path):
        """ForcingModel on Meteo.forcingfile (bcAscii) must become SkipSaveForcingModel."""
        bc_path = tmp_path / "meteo.bc"
        bc_path.write_text(_BC_METEO)

        meteo = Meteo(
            **{
                "quantity": "rainfall_rate",
                "forcingfile": str(bc_path),
                "forcingfiletype": MeteoForcingFileType.bcascii,
            }
        )
        ext_model = ExtModel(meteo=[meteo])

        assert isinstance(meteo.forcingfile, ForcingModel)
        assert not isinstance(meteo.forcingfile, SkipSaveForcingModel)

        mark_existing_forcing_models_as_skip_save_models(ext_model)

        assert isinstance(ext_model.meteo[0].forcingfile, SkipSaveForcingModel)
        assert ext_model.meteo[0].forcingfile.filepath == bc_path

    def test_meteo_already_skip_save_not_double_wrapped(self, tmp_path: Path):
        """Calling the guard twice must not change an already-replaced Meteo model."""
        bc_path = tmp_path / "meteo.bc"
        bc_path.write_text(_BC_METEO)

        ext_model = ExtModel(
            meteo=[
                {
                    "quantity": "rainfall_rate",
                    "forcingfile": str(bc_path),
                    "forcingfiletype": MeteoForcingFileType.bcascii,
                }
            ]
        )

        mark_existing_forcing_models_as_skip_save_models(ext_model)
        first_instance = ext_model.meteo[0].forcingfile

        mark_existing_forcing_models_as_skip_save_models(ext_model)
        second_instance = ext_model.meteo[0].forcingfile

        assert first_instance is second_instance
