import shutil
from pathlib import Path

from hydrolib.core.dflowfm.mba.models import MassBalanceAreaModel
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser


class TestConvertMassBalanceAreaFromMDU:
    """End-to-end conversion of the mass balance area quantity (c105 reference model)."""

    def _prepare_model(self, input_files_dir: Path, tmp_path: Path) -> Path:
        """Copy the compact c105 fixture to a temp dir and return the MDU path."""
        dst = tmp_path / "c105"
        shutil.copytree(input_files_dir / "mba", dst)
        return dst / "westernscheldt.mdu"

    def test_areas_written_to_mba_file(self, input_files_dir: Path, tmp_path: Path):
        """Test that the waqmassbalancearea quantities become a single `_mba.ini`.

        Test scenario:
            Convert the model; the mass balance areas move to the mba file with a
            [General] block and one [MassBalanceArea] per area (in order), deriving
            the name from the quantity suffix and the polygon from FILENAME.
        """
        mdu = self._prepare_model(input_files_dir, tmp_path)

        converter = ExternalForcingConverter.from_mdu(mdu, debug=True)
        converter.update()
        converter.save(backup=False)

        mba_path = converter.mba_model.filepath
        assert mba_path.exists(), "Expected the _mba.ini to be written"

        reloaded = MassBalanceAreaModel(filepath=mba_path)
        assert reloaded.general.filetype == "massBalanceAreas"
        names = [a.name for a in reloaded.massbalancearea]
        assert names == ["EstruaryWest", "River"], f"Got {names}"
        assert reloaded.massbalancearea[0].locationfile.filepath == Path(
            "EstruaryWest.pol"
        ), f"Got {reloaded.massbalancearea[0].locationfile.filepath}"

    def test_general_block_is_serialized(self, input_files_dir: Path, tmp_path: Path):
        """Test that the mba file always carries its [General] fileType.

        Test scenario:
            The [General] block identifies the file to the kernel and must be
            present even though it uses default values.
        """
        mdu = self._prepare_model(input_files_dir, tmp_path)
        converter = ExternalForcingConverter.from_mdu(mdu, debug=True)
        converter.update()
        converter.save(backup=False)

        text = converter.mba_model.filepath.read_text()
        assert "[General]" in text, "Missing [General] block"
        assert "fileType" in text and "massBalanceAreas" in text, f"Got:\n{text[:200]}"

    def test_mdu_output_keywords_are_set(self, input_files_dir: Path, tmp_path: Path):
        """Test that the MDU [output] section gets mbaFile and mbaInterval.

        Test scenario:
            mbaFile points at the generated file, and mbaInterval is copied from
            the legacy [processes] DtMassBalance (300.0) per the conversion design.
        """
        mdu = self._prepare_model(input_files_dir, tmp_path)
        converter = ExternalForcingConverter.from_mdu(mdu, debug=True)
        converter.update()
        converter.save(backup=False)

        parser = MDUParser(mdu)
        assert (
            parser.get_keyword("mbaFile") == "new_mba.ini"
        ), f"Got {parser.get_keyword('mbaFile')}"
        assert (
            parser.get_keyword("mbaInterval") == "300.0"
        ), f"Got {parser.get_keyword('mbaInterval')}"

    def test_areas_not_in_new_ext_file(self, input_files_dir: Path, tmp_path: Path):
        """Test that mass balance areas do not leak into the new ext file.

        Test scenario:
            Every converted area belongs exclusively to the mba file (Manual F.2.5);
            none may appear as a block in the new external forcings file.
        """
        mdu = self._prepare_model(input_files_dir, tmp_path)
        converter = ExternalForcingConverter.from_mdu(mdu, debug=True)
        ext_model, _ = converter.update()

        assert (
            len(converter.mba_model.massbalancearea) == 2
        ), f"Expected 2 mba areas, got {len(converter.mba_model.massbalancearea)}"
        assert (
            len(ext_model.spatial) == 0
        ), f"Mass balance areas leaked into ext [spatial]: {len(ext_model.spatial)}"
        assert (
            ext_model.n_forcing_blocks == 0
        ), f"Mass balance areas leaked into the new ext file: {ext_model.n_forcing_blocks} block(s)"
