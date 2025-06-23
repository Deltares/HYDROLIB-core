from pathlib import Path
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter


class TestSourceSinks:
    def test_read_correctly_result_bc_correct(self):
        """
        Test that the pli file is read correctly and the result bc file has the right relative path.
        """
        mdu_file = Path("tests/data/models/relative-path-model/model-config/relative-path.mdu")
        bc_relative_path = Path("../model-inputs/relative-path.bc")
        converter = ExternalForcingConverter.from_mdu(mdu_file)
        ext_model, _, _ = converter.update()
        assert len(ext_model.sourcesink) == 1
        source_sink = ext_model.sourcesink[0]
        assert source_sink.discharge.filepath == bc_relative_path
        assert source_sink.salinitydelta.filepath == bc_relative_path
        assert source_sink.temperaturedelta.filepath == bc_relative_path

