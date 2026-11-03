import shutil
from pathlib import Path

import pytest

from hydrolib.core.dflowfm.ext.models import ExtModel
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter


@pytest.mark.e2e
class TestInifieldThacker1dE2E:
    """Convert the inifield file of the test bench case
    `e02_dflowfm/f003_advection/c040_thacker1d_standard`.

    The MDU (planar1d.mdu) has `IniFieldFile = inifields.ini` with one `[Initial]` block (`initialwaterlevel`,
    a sample file) and `ExtForceFileNew = iniwaterlevel-new.ext`, a new external forcings file without blocks.
    Only the text files of the case are kept (the net file is not read by the converter).
    """

    @pytest.fixture
    def model_copy(self, tmp_path: Path, input_files_dir: Path) -> Path:
        """Copy the model to a temp dir so the conversion does not mutate the originals."""
        dst = tmp_path / "inifield_thacker1d"
        shutil.copytree(input_files_dir / "inifield_thacker1d", dst)
        return dst

    @pytest.fixture
    def converted(self, model_copy: Path) -> ExternalForcingConverter:
        converter = ExternalForcingConverter.from_mdu(model_copy / "planar1d.mdu")
        converter.update()
        converter.save(backup=False)
        return converter

    def test_the_inifield_block_becomes_a_spatial_block(self, converted, model_copy):
        ext = ExtModel(filepath=model_copy / "iniwaterlevel-new.ext", recurse=False)

        assert [b.quantity for b in ext.spatial] == ["initialwaterlevel"]
        block = ext.spatial[0]
        assert block.datafile.filepath == Path("iniwatk.xyz")
        assert block.datafiletype == "sample"
        assert block.interpolationmethod == "triangulation"
        assert block.operand == "override"
        assert block.averagingtype == "mean"
        assert block.extrapolationallowed is False

    def test_the_mdu_drops_the_inifield_and_keeps_the_new_ext_file(
        self, converted, model_copy
    ):
        text = (model_copy / "planar1d.mdu").read_text().lower()

        assert "inifieldfile" not in text
        assert "extforcefilenew" in text
        assert "iniwaterlevel-new.ext" in text

    def test_clean_removes_only_the_inifield_file(self, converted, model_copy):
        converted.clean()

        assert not (model_copy / "inifields.ini").exists()
        assert (model_copy / "iniwatk.xyz").is_file()
        assert (model_copy / "iniwaterlevel-new.ext").is_file()
