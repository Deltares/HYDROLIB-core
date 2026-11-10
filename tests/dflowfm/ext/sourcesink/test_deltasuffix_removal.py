import warnings
from pathlib import Path
from typing import Tuple

import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm import ExtModel, FMModel, ForcingModel
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from tests.tools.test_main_converter import _make_mdu_parser_mock

_BC_CONTENT = """[General]
fileVersion = 1.01
fileType    = boundConds

[Forcing]
name              = Q_S
function          = timeseries
timeInterpolation = linear
quantity          = time
unit              = minutes since 2020-01-01 00:00:00
quantity          = discharge
unit              = m3/s
0 1.0
60 2.0
"""

_NEW_EXT_CONTENT = """[General]
fileVersion = 3.00
fileType    = extForce

[SourceSink]
id             = Q_S
numCoordinates = 1
xCoordinates   = 104.04
yCoordinates   = 1.41
discharge      = pt_discharge.bc
"""

_OLD_EXT_CONTENT = """QUANTITY     =windspeedfactor
FILENAME     =pt_wind.pol
FILETYPE     =11
METHOD       =4
OPERAND      =O
"""

class TestRecurseBase:
    @staticmethod
    def _create_model(
        model_dir: Path, quantity: str = "discharge"
    ) -> Tuple[Path, Path, Path, Path]:
        model_dir.mkdir(parents=True, exist_ok=True)
        old_file = model_dir / "old_ext.ext"
        old_file.write_text(_OLD_EXT_CONTENT)

        ext_file = model_dir / "new_ext.ext"
        ext_file.write_text(_NEW_EXT_CONTENT)

        bc_file = model_dir / "pt_discharge.bc"
        bc_file.write_text(_BC_CONTENT)

        if quantity != "discharge":
            bc_file = model_dir / f"{quantity}.bc"
            bc_file.write_text(_BC_CONTENT.replace("discharge", f"{quantity}delta"))
            ext_file.write_text(_NEW_EXT_CONTENT + f"{quantity}Delta = {bc_file.name}\n")

        mdu_file = model_dir / "model.mdu"
        mdu_file.write_text(
            "[General]\n"
            "fileVersion = 1.09\n"
            "fileType = modelDef\n"
            "[External Forcing]\n"
            f"extForceFileNew = {ext_file.name}\n"
        )

        return old_file, ext_file, bc_file, mdu_file

class TestRecurseTrue(TestRecurseBase):
    """The .bc files referenced by the new external forcing file (like hyd07_z_for_hydromt)."""

    def test_bc_files_loaded_and_saved_with_recurse(self, tmp_path: Path):
        old_file, ext_file, bc_file, _ = self._create_model(tmp_path / "model")

        converter = ExternalForcingConverter(
            extold_model=old_file,
            ext_file=ext_file,
            mdu_parser=_make_mdu_parser_mock(old_file.parent),
            recurse=True,
        )

        discharge = converter.ext_model.sourcesink[0].discharge
        assert isinstance(discharge, ForcingModel)
        assert discharge.filepath.name == bc_file.name
        assert len(discharge.forcing) == 1

        # remove the .bc file, a recursive save must write it again
        bc_file.unlink()
        converter.save(backup=False, recursive=True)

        assert bc_file.exists()
        assert "[Forcing]" in bc_file.read_text()

    def test_delta_suffix_removed_with_recurse(self, tmp_path: Path):
        """Legacy `<quantity>Delta` keywords referencing .bc files are renamed to the base name when saving."""
        old_file, ext_file, bc_file, _ = self._create_model(tmp_path / "model")
        sal_bc = bc_file.with_name("sal_temp.bc")
        sal_bc.write_text(_BC_CONTENT.replace("discharge", "salinitydelta"))
        ext_file.write_text(
            _NEW_EXT_CONTENT
            + "salinityDelta   = sal_temp.bc\n"
            + "tracerOXYdelta  = sal_temp.bc\n"
        )
        assert "Delta" in ext_file.read_text()
        assert "delta" in sal_bc.read_text()

        mdu_parser = _make_mdu_parser_mock(old_file.parent)

        converter = ExternalForcingConverter(
            extold_model=old_file,
            ext_file=ext_file,
            mdu_parser=mdu_parser,
            recurse=True,
        )

        sourcesink = converter.ext_model.sourcesink[0]
        assert isinstance(sourcesink.salinity, ForcingModel)

        converter.save(backup=False, recursive=True)

        text = ext_file.read_text()
        assert "delta" not in text.lower()
        assert "salinity" in text
        assert "traceroxy" in text.lower()

        assert sal_bc.exists()
        assert "delta" not in sal_bc.read_text().lower()


    @pytest.mark.parametrize("quantity", ["salinity", "tracerOXY"])
    def test_fmm_model_delta_suffix_removed_on_save_and_reload(self, tmp_path: Path, quantity):
        _, ext_file, bc_file, mdu_file = self._create_model(tmp_path / "model", quantity)
        model = FMModel(mdu_file, recurse=True)
        sourcesink = model.external_forcing.extforcefilenew[0].sourcesink[0]
        model.save(recurse=True)

        for path in (ext_file, bc_file, ext_file.with_name("pt_discharge.bc")):
            assert "delta" not in path.read_text().lower()

        reloaded = FMModel(mdu_file, recurse=True)
        reloaded_ext = reloaded.external_forcing.extforcefilenew[0]

        assert isinstance(reloaded_ext, ExtModel)
        assert len(reloaded_ext.sourcesink) == 1
        reloaded_sourcesink = reloaded_ext.sourcesink[0]
        assert reloaded_sourcesink.id == sourcesink.id
        for field in ("discharge", quantity.lower()):
            original_forcing = getattr(sourcesink, field)
            saved_forcing = getattr(reloaded_sourcesink, field)
            assert isinstance(saved_forcing, ForcingModel)
            assert saved_forcing.filepath == original_forcing.filepath
            assert len(saved_forcing.forcing) == 1
            assert (
                saved_forcing.forcing[0].quantityunitpair
                == original_forcing.forcing[0].quantityunitpair
            )
            assert (
                saved_forcing.forcing[0].datablock
                == original_forcing.forcing[0].datablock
            )

class TestRecurseFalse(TestRecurseBase):
    @pytest.mark.parametrize("quantity", ["salinity", "tracerOXY"])
    def test_fmm_model_delta_suffix_kept_on_save_and_reload(
        self, tmp_path: Path, quantity
    ):
        _, ext_file, bc_file, mdu_file = self._create_model(tmp_path / "model", quantity)
        paths = (ext_file, bc_file, ext_file.with_name("pt_discharge.bc"))
        original_contents = {path: path.read_bytes() for path in paths}
        assert "delta" in ext_file.read_text().lower()
        assert "delta" in bc_file.read_text().lower()

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "error", message=".*suffix `delta`", category=UserWarning
            )
            model = FMModel(mdu_file, recurse=False)
            ext_reference = model.external_forcing.extforcefilenew[0]
            assert isinstance(ext_reference, DiskOnlyFileModel)
            assert ext_reference.filepath == Path(ext_file.name)

            model.save(recurse=False)
            reloaded = FMModel(mdu_file, recurse=False)

        reloaded_reference = reloaded.external_forcing.extforcefilenew[0]
        assert isinstance(reloaded_reference, DiskOnlyFileModel)
        assert reloaded_reference.filepath == ext_reference.filepath
        for path, content in original_contents.items():
            assert path.read_bytes() == content

    def test_delta_suffix_kept_in_bc_without_recurse(self, tmp_path: Path):
        """Without recurse the .bc files are never loaded, so they are not rewritten."""
        old_file, ext_file, bc_file, _ = self._create_model(tmp_path / "model")
        sal_bc = bc_file.with_name("sal_temp.bc")
        sal_bc.write_text(_BC_CONTENT.replace("discharge", "salinitydelta"))
        ext_file.write_text(_NEW_EXT_CONTENT + "salinityDelta   = sal_temp.bc\n")
        original = sal_bc.read_text()

        mdu_parser = _make_mdu_parser_mock(old_file.parent)

        with pytest.warns(UserWarning, match="suffix `delta`"):
            converter = ExternalForcingConverter(
                extold_model=old_file,
                ext_file=ext_file,
                mdu_parser=mdu_parser,
                recurse=False,
            )
        assert not isinstance(converter.ext_model.sourcesink[0].salinity, ForcingModel)

        converter.save(backup=False, recursive=False)

        assert sal_bc.read_text() == original
        assert "delta" in sal_bc.read_text().lower()

    def test_bc_files_not_loaded_without_recurse(self, tmp_path: Path):
        old_file, ext_file, bc_file, _ = self._create_model(tmp_path / "model")

        converter = ExternalForcingConverter(
            extold_model=old_file,
            ext_file=ext_file,
            mdu_parser=_make_mdu_parser_mock(old_file.parent),
            recurse=False,
        )

        assert not isinstance(converter.ext_model.sourcesink[0].discharge, ForcingModel)
