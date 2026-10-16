from pathlib import Path

import pytest

from hydrolib.core.dflowfm.structure.models import (
    StructureGeneral,
    StructureModel,
    Weir,
)


class TestFileVersionForLocationFile:
    """`locationFile` belongs to structure file version 3.01, so the version must follow."""

    _legacy_weir = (
        "[Structure]\n"
        "id = weir_id\n"
        "type = weir\n"
        "polylinefile = weir.pli\n"
        "crestLevel = 1.0\n"
        "lat_contr_coeff = 0.8\n"
    )

    _branch_weir = (
        "[Structure]\n"
        "id = weir_id\n"
        "type = weir\n"
        "branchId = branch\n"
        "chainage = 1.0\n"
        "crestLevel = 1.0\n"
    )

    @staticmethod
    def _header(fileversion: str) -> str:
        return f"[General]\nfileVersion = {fileversion}\nfileType = structure\n\n"

    @staticmethod
    def _save_and_read(model: StructureModel, tmp_path: Path) -> str:
        model.filepath = tmp_path / "saved.ini"
        model.save()
        return model.filepath.read_text()

    @pytest.mark.parametrize("fileversion", ["1.00", "2.00", "3.00", "3.01"])
    def test_loaded_legacy_file_is_saved_as_version_3_01(self, tmp_path, fileversion):
        path = tmp_path / "structures.ini"
        path.write_text(self._header(fileversion) + self._legacy_weir)

        text = self._save_and_read(StructureModel(path), tmp_path)

        assert "fileVersion = 3.01" in text
        assert "locationFile" in text
        assert "polylinefile" not in text

    def test_legacy_lat_contr_coeff_is_saved_as_corrcoeff_in_version_3_01(
        self, tmp_path
    ):
        path = tmp_path / "structures.ini"
        path.write_text(self._header("1.00") + self._legacy_weir)

        model = StructureModel(path)
        text = self._save_and_read(model, tmp_path)

        assert model.structure[0].corrcoeff == pytest.approx(0.8)
        assert "fileVersion = 3.01" in text
        assert "corrCoeff" in text
        assert "lat_contr_coeff" not in text

    def test_file_without_general_section_is_saved_as_version_3_01(self, tmp_path):
        path = tmp_path / "structures.ini"
        path.write_text(self._legacy_weir)

        text = self._save_and_read(StructureModel(path), tmp_path)

        assert "fileVersion = 3.01" in text

    def test_version_is_kept_when_no_structure_uses_a_location_file(self, tmp_path):
        path = tmp_path / "structures.ini"
        path.write_text(self._header("1.00") + self._branch_weir)

        text = self._save_and_read(StructureModel(path), tmp_path)

        assert "fileVersion = 1.00" in text
        assert "locationFile" not in text

    def test_structure_with_location_file_added_after_loading_raises_the_version(
        self, tmp_path
    ):
        path = tmp_path / "structures.ini"
        path.write_text(self._header("1.00") + self._branch_weir)
        model = StructureModel(path)
        model.structure.append(
            Weir(id="added", type="weir", crestlevel=1.0, locationfile="added.pli")
        )

        text = self._save_and_read(model, tmp_path)

        assert "fileVersion = 3.01" in text

    def test_replacing_the_general_section_raises_the_version(self, tmp_path):
        """The extforce converter rebuilds `[General]` from the version it read."""
        path = tmp_path / "structures.ini"
        path.write_text(self._header("3.01") + self._legacy_weir)
        model = StructureModel(path)

        model.general = StructureGeneral(fileVersion="1.00", fileType="structure")

        assert model.general.fileversion == "3.01"

    def test_raising_the_version_is_logged(self, tmp_path, caplog):
        path = tmp_path / "structures.ini"
        path.write_text(self._header("1.00") + self._legacy_weir)

        with caplog.at_level("WARNING"):
            StructureModel(path)

        assert "1.00 is raised to 3.01" in caplog.text
