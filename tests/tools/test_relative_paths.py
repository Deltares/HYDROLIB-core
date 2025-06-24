import os
from pathlib import Path

from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter


class TestSourceSinks:
    def test_read_correctly_result_bc_correct(self, models_dir: Path):
        """
        Test that the pli file is read correctly and the result bc file has the right relative path.
        """
        mdu_file = models_dir / "relative-path-model/model-config/relative-path.mdu"
        bc_relative_path = Path("../model-inputs/relative-path.bc")
        bc_abs_path = models_dir / "relative-path-model/model-inputs/relative-path.bc"

        converter = ExternalForcingConverter.from_mdu(mdu_file)
        ext_model, _, _ = converter.update()
        assert len(ext_model.sourcesink) == 1
        source_sink = ext_model.sourcesink[0]
        assert source_sink.discharge.filepath == bc_relative_path
        assert source_sink.salinitydelta.filepath == bc_relative_path
        assert source_sink.temperaturedelta.filepath == bc_relative_path
        converter.save()

        assert ext_model.filepath.exists()
        ext_model.filepath.unlink()

        # remove the newly created mdu file and restore the backup
        converter.mdu_parser.mdu_path.unlink()
        backup_file = converter.mdu_parser.mdu_path.with_suffix(".mdu.bak")
        backup_file.rename(backup_file.with_suffix(""))

        # check the bc file
        bc_abs_path.exists()
        bc_abs_path.unlink()
