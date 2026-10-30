from pathlib import Path
from typing import Tuple

import pytest

from hydrolib.core.dflowfm import ForcingModel
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
    def _create_model(model_dir: Path) -> Tuple[Path, Path, Path]:
        model_dir.mkdir(parents=True, exist_ok=True)
        old_file = model_dir / "old_ext.ext"
        old_file.write_text(_OLD_EXT_CONTENT)

        ext_file = model_dir / "new_ext.ext"
        ext_file.write_text(_NEW_EXT_CONTENT)

        bc_file = model_dir / "pt_discharge.bc"
        bc_file.write_text(_BC_CONTENT)

        return old_file, ext_file, bc_file

class TestRecurseTrue(TestRecurseBase):
    """The .bc files referenced by the new external forcing file (like hyd07_z_for_hydromt)."""

    def test_bc_files_loaded_and_saved_with_recurse(self, tmp_path: Path):
        old_file, ext_file, bc_file = self._create_model(tmp_path / "model")

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
        old_file, ext_file, bc_file = self._create_model(tmp_path / "model")
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

        with pytest.warns(UserWarning, match="suffix `delta`"):
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


class TestRecurseFalse(TestRecurseBase):
    def test_delta_suffix_kept_in_bc_without_recurse(self, tmp_path: Path):
        """Without recurse the .bc files are never loaded, so they are not rewritten."""
        old_file, ext_file, bc_file = self._create_model(tmp_path / "model")
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
        old_file, ext_file, bc_file = self._create_model(tmp_path / "model")

        converter = ExternalForcingConverter(
            extold_model=old_file,
            ext_file=ext_file,
            mdu_parser=_make_mdu_parser_mock(old_file.parent),
            recurse=False,
        )

        assert not isinstance(converter.ext_model.sourcesink[0].discharge, ForcingModel)
