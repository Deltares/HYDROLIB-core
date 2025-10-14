import os
from pathlib import Path

from hydrolib.core.dflowfm.extold.models import ExtOldForcing
from hydrolib.tools.extforce_convert.converters import InitialConditionConverter
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter


class TestInitialConditionConverter:
    def test_convert_different_locations(self, tmp_path: Path):
        ext_old_path = (
            tmp_path
            / "tests/testdata/tools/relative-path-model/model-inputs/computation/test/tba/old-ext-file.ext"
        )
        initialfield_path = (
            tmp_path
            / "tests/testdata/tools/relative-path-model/model-inputs/initial-conditions/test/initial-condition.ini"
        )
        forcing_data = {
            "QUANTITY": "initialsalinity",
            "filename": "../../../initial-conditions/test/iniSal_autoTransportTimeStep1_filtered_inclVZM.xyz",
            "filetype": 7,
            "method": 5,
            "operand": "O",
        }
        forcing = ExtOldForcing(**forcing_data)
        initial_field = InitialConditionConverter().convert(
            forcing, initialfield_path, ext_old_path
        )
        assert (
            initial_field.datafile._source_file_path
            == Path("iniSal_autoTransportTimeStep1_filtered_inclVZM.xyz").resolve()
        )


class TestSourceSinks:
    def test_read_correctly_result_bc_correct(self, models_dir: Path):
        """
        Test that the pli file is read correctly and the result bc file has the right relative path.
        """
        mdu_file = models_dir / "relative-path-model/model-config/relative-path.mdu"
        source_sink_paths = {
            "bc_relative_path": Path(
                "../model-inputs/source-sink/source-sink-relative-path.bc"
            ),
            "bc_abs_path": models_dir
            / "relative-path-model/model-inputs/source-sink/source-sink-relative-path.bc",
        }
        boundary_paths = {
            "bc_relative_path": Path(
                "../model-inputs/boundary-condition/boundary-condition-relative-path.bc"
            ),
            "bc_abs_path": models_dir
            / "relative-path-model/model-inputs/boundary-condition/boundary-condition-relative-path.bc",
        }

        converter = ExternalForcingConverter.from_mdu(mdu_file)
        ext_model, _, _ = converter.update()
        assert len(ext_model.sourcesink) == 1
        assert len(ext_model.boundary) == 1

        source_sink = ext_model.sourcesink[0]
        assert source_sink.discharge.filepath == source_sink_paths["bc_relative_path"]
        assert (
            source_sink.salinitydelta.filepath == source_sink_paths["bc_relative_path"]
        )
        assert (
            source_sink.temperaturedelta.filepath
            == source_sink_paths["bc_relative_path"]
        )

        assert len(ext_model.boundary) == 1
        boundary = ext_model.boundary[0]
        assert boundary.forcingfile.filepath == boundary_paths["bc_relative_path"]

        converter.save()

        assert ext_model.filepath.exists()
        ext_model.filepath.unlink()

        # remove the newly created mdu file and restore the backup
        converter.mdu_parser.mdu_path.unlink()
        backup_file = converter.mdu_parser.mdu_path.with_suffix(".mdu.bak")
        backup_file.rename(backup_file.with_suffix(""))

        # check the bc file
        assert source_sink_paths["bc_abs_path"].exists()
        source_sink_paths["bc_abs_path"].unlink()

        assert boundary_paths["bc_abs_path"].exists()
        boundary_paths["bc_abs_path"].unlink()
