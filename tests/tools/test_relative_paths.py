import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.extold.models import ExtOldForcing, ExtOldModel
from hydrolib.core.dflowfm.inifield.models import IniFieldModel
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser


class TestInitialConditionConverter:

    @pytest.mark.parametrize("quantity", ["initialsalinity", "AdvectionType"])
    def test_convert_different_locations(self, tmp_path: Path, quantity: str):
        ext_old_path = tmp_path / "tests/computation/test/tba/old-ext-file.ext"
        initialfield_path = (
            tmp_path / "tests/initial-conditions/test/initial-condition.ini"
        )
        forcing_data = {
            "QUANTITY": quantity,
            "filename": "../../../initial-conditions/test/iniSal_autoTransportTimeStep1_filtered_inclVZM.xyz",
            "filetype": 7,
            "method": 5,
            "operand": "O",
        }
        forcing = ExtOldForcing(**forcing_data)
        with patch(
            "hydrolib.tools.extforce_convert.main_converter.ExternalForcingConverter.__init__",
            return_value=None,
        ):
            extold_model = MagicMock(spec=ExtOldModel)
            extold_model.filepath = ext_old_path
            inifield_model = MagicMock(spec=IniFieldModel)
            inifield_model.filepath = initialfield_path
            mdu_parser = MagicMock(spec=MDUParser)
            mdu_parser.loaded_fm_data = {"general": {"pathsrelativetoparent": "1"}}
            external_forcing_converter = ExternalForcingConverter("old-ext-file.ext")
            external_forcing_converter._inifield_model = inifield_model
            external_forcing_converter._extold_model = extold_model
            external_forcing_converter._root_dir = tmp_path
            external_forcing_converter._legacy_files = []
            external_forcing_converter._mdu_parser = mdu_parser
        initial_field = external_forcing_converter._convert_forcing(forcing)
        assert initial_field.datafile == DiskOnlyFileModel(
            "iniSal_autoTransportTimeStep1_filtered_inclVZM.xyz"
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
        assert boundary.forcingfile[0].filepath == boundary_paths["bc_relative_path"]

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
